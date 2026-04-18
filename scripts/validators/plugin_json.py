"""
plugin.json のバリデーター
"""

import re
from pathlib import Path

from .base import ValidationResult, parse_json_safe, validate_kebab_case


def _validate_user_config_mapping(
    result: ValidationResult,
    file_path: Path,
    user_config: object,
    label: str,
) -> None:
    """
    userConfig のスキーマを検証する（トップレベルと per-channel で共通化）

    Args:
        result: 検証結果オブジェクト
        file_path: エラーメッセージ用のファイルパス
        user_config: 検証対象の値
        label: エラーメッセージのプレフィックス（例: "userConfig", "channels[0].userConfig"）
    """
    if not isinstance(user_config, dict):
        result.add_error(
            f"{file_path.name}: {label}はオブジェクト（キーと設定項目のマッピング）が必要です"
        )
        return
    for config_key, config_value in user_config.items():
        if not isinstance(config_value, dict):
            result.add_error(f"{file_path.name}: {label}.{config_key}はオブジェクトが必要です")
            continue
        # sensitiveはブール値のみ
        sensitive = config_value.get("sensitive")
        if sensitive is not None and not isinstance(sensitive, bool):
            result.add_error(
                f"{file_path.name}: {label}.{config_key}.sensitiveはブール値が必要です"
            )


def validate_plugin_json(file_path: Path, content: str) -> ValidationResult:
    """plugin.jsonを検証する"""
    result = ValidationResult()

    data = parse_json_safe(content, file_path, result)
    if data is None:
        return result

    # 必須フィールド
    if not data.get("name"):
        result.add_error(f"{file_path.name}: nameが必須です")
    else:
        name = data["name"]
        # kebab-caseチェック
        kebab_error = validate_kebab_case(name)
        if kebab_error:
            result.add_error(f"{file_path.name}: {kebab_error}")
        if " " in name:
            result.add_error(f"{file_path.name}: nameにスペースは使用できません")

    # バージョン形式
    version = data.get("version", "")
    if version and not re.match(r"^\d+\.\d+\.\d+", version):
        result.add_warning(
            f"{file_path.name}: versionはセマンティックバージョニング（x.y.z）を推奨: {version}"
        )

    # userConfigの確認（v2.1.83以降）
    user_config = data.get("userConfig")
    if user_config is not None:
        _validate_user_config_mapping(result, file_path, user_config, "userConfig")

    # channelsの確認（v2.1.80以降）
    channels = data.get("channels")
    if channels is not None:
        if not isinstance(channels, list):
            result.add_error(f"{file_path.name}: channelsは配列が必要です")
        else:
            mcp_servers = data.get("mcpServers")
            mcp_keys: set[str] = set()
            if isinstance(mcp_servers, dict):
                mcp_keys = set(mcp_servers.keys())
            for i, entry in enumerate(channels):
                prefix = f"{file_path.name}: channels[{i}]"
                if not isinstance(entry, dict):
                    result.add_error(f"{prefix}: エントリはオブジェクトが必要です")
                    continue

                server = entry.get("server")
                if not server:
                    result.add_error(f"{prefix}: serverは必須です")
                elif not isinstance(server, str):
                    result.add_error(f"{prefix}: serverは文字列が必要です")
                else:
                    # mcpServers が同じ plugin.json 内に宣言されている場合のみ整合性チェック
                    if isinstance(mcp_servers, dict) and server not in mcp_keys:
                        result.add_warning(
                            f"{prefix}: server '{server}' が mcpServers のキーと一致しません"
                            f"（mcpServers: {sorted(mcp_keys) if mcp_keys else '未宣言'}）"
                        )

                # per-channel userConfig はトップレベル userConfig と同じスキーマ
                channel_user_config = entry.get("userConfig")
                if channel_user_config is not None:
                    _validate_user_config_mapping(
                        result,
                        file_path,
                        channel_user_config,
                        f"channels[{i}].userConfig",
                    )

    # dependenciesの確認（v2.1.110以降）
    dependencies = data.get("dependencies")
    if dependencies is not None:
        if not isinstance(dependencies, list):
            result.add_error(f"{file_path.name}: dependenciesは配列が必要です")
        else:
            for i, dep in enumerate(dependencies):
                if not isinstance(dep, str):
                    result.add_error(f"{file_path.name}: dependencies[{i}]は文字列が必要です")
                elif not dep:
                    result.add_error(f"{file_path.name}: dependencies[{i}]は空文字列です")
                else:
                    dep_error = validate_kebab_case(dep)
                    if dep_error:
                        msg = f"dependencies[{i}]はkebab-case（小文字とハイフン）のみ: {dep}"
                        result.add_warning(f"{file_path.name}: {msg}")

    # パスの確認
    path_fields = [
        "commands",
        "agents",
        "skills",
        "hooks",
        "mcpServers",
        "lspServers",
        "outputStyles",
        "settings",
        "monitors",
    ]
    for field in path_fields:
        value = data.get(field)
        if value and isinstance(value, str) and not value.startswith("./"):
            result.add_warning(f"{file_path.name}: {field}のパスは./で始めることを推奨: {value}")

    # デフォルトパスと同一のコンポーネント参照は冗長
    default_paths = {
        "commands": ["./commands/", "./commands"],
        "agents": ["./agents/", "./agents"],
        "skills": ["./skills/", "./skills"],
        "hooks": ["./hooks/hooks.json"],
        "mcpServers": ["./.mcp.json"],
        "lspServers": ["./.lsp.json"],
        "settings": ["./settings.json"],
        "monitors": ["./monitors/monitors.json"],
    }
    for field, defaults in default_paths.items():
        value = data.get(field)
        if isinstance(value, str) and value in defaults:
            result.add_warning(
                f"{file_path.name}: {field}はデフォルトパス（{value}）と同一のため"
                f"指定不要です。削除してください"
            )

    return result
