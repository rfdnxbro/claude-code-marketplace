"""
plugin.json のバリデーター
"""

import re
from pathlib import Path
from typing import Any

from .base import ValidationResult, parse_json_safe, validate_kebab_case
from .monitors_json import validate_monitors_entries


def _validate_user_config_mapping(
    result: ValidationResult,
    file_path: Path,
    user_config: Any,
    label: str,
) -> None:
    """userConfig のスキーマを検証する（トップレベルと per-channel で共通使用）"""
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
            # mcp_keys が空 set のままなら mcpServers が未宣言。
            # mcpServers: {} と未宣言は動作上どちらも整合性チェックの根拠が無いため同一扱い。
            mcp_keys: set[str] = set(mcp_servers.keys()) if isinstance(mcp_servers, dict) else set()
            for i, entry in enumerate(channels):
                prefix = f"{file_path.name}: channels[{i}]"
                if not isinstance(entry, dict):
                    result.add_error(f"{prefix}: エントリはオブジェクトが必要です")
                    continue

                # serverの検証: 存在→型→値の順
                server = entry.get("server")
                if server is None:
                    result.add_error(f"{prefix}: serverは必須です")
                elif not isinstance(server, str):
                    result.add_error(f"{prefix}: serverは文字列が必要です")
                elif not server:
                    result.add_error(f"{prefix}: serverは空文字列にできません")
                elif mcp_keys and server not in mcp_keys:
                    # mcpServers が同じ plugin.json 内に宣言されている場合のみ整合性チェック
                    result.add_warning(
                        f"{prefix}: server '{server}' が mcpServers のキーと一致しません"
                        f"（mcpServers: {sorted(mcp_keys)}）"
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

    # 公式スキーマに存在しないフィールドを警告
    # settings は plugin.json のフィールドではなく、settings.json はプラグインルート
    # 直下に配置すれば自動検出される。誤って指定された場合にサイレント無視を防ぐ。
    if "settings" in data:
        result.add_warning(
            f"{file_path.name}: settingsはplugin.jsonの公式フィールドではありません。"
            f"settings.jsonはプラグインルート直下に配置すれば自動検出されます"
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

    # monitors がインライン配列の場合はエントリを検証（v2.1.105以降）
    monitors = data.get("monitors")
    if isinstance(monitors, list):
        validate_monitors_entries(monitors, file_path, result)

    # パスの確認
    path_fields = [
        "commands",
        "agents",
        "skills",
        "hooks",
        "mcpServers",
        "lspServers",
        "outputStyles",
        "monitors",
        "themes",
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
        "monitors": ["./monitors/monitors.json"],
        "themes": ["./themes/", "./themes"],
    }
    for field, defaults in default_paths.items():
        value = data.get(field)
        if isinstance(value, str) and value in defaults:
            result.add_warning(
                f"{file_path.name}: {field}はデフォルトパス（{value}）と同一のため"
                f"指定不要です。削除してください"
            )

    return result
