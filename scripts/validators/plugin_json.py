"""
plugin.json のバリデーター
"""

import re
from pathlib import Path

from .base import ValidationResult, parse_json_safe, validate_kebab_case


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
        if not isinstance(user_config, dict):
            result.add_error(
                f"{file_path.name}: userConfigはオブジェクト（キーと設定項目のマッピング）"
                "が必要です"
            )
        else:
            for config_key, config_value in user_config.items():
                if not isinstance(config_value, dict):
                    result.add_error(
                        f"{file_path.name}: userConfig.{config_key}はオブジェクトが必要です"
                    )
                    continue
                # sensitiveはブール値のみ
                sensitive = config_value.get("sensitive")
                if sensitive is not None and not isinstance(sensitive, bool):
                    result.add_error(
                        f"{file_path.name}: userConfig.{config_key}.sensitiveはブール値が必要です"
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
                        result.add_warning(f"{file_path.name}: dependencies[{i}]: {dep_error}")

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
    }
    for field, defaults in default_paths.items():
        value = data.get(field)
        if isinstance(value, str) and value in defaults:
            result.add_warning(
                f"{file_path.name}: {field}はデフォルトパス（{value}）と同一のため"
                f"指定不要です。削除してください"
            )

    return result
