"""
plugin.json のバリデーター
"""

import json
import re
from pathlib import Path

from .base import ValidationResult


def validate_plugin_json(file_path: Path, content: str) -> ValidationResult:
    """plugin.jsonを検証する"""
    result = ValidationResult()

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        result.add_error(f"{file_path.name}: JSONパースエラー: {e}")
        return result

    # 必須フィールド
    if not data.get("name"):
        result.add_error(f"{file_path.name}: nameが必須です")
    else:
        name = data["name"]
        # kebab-caseチェック
        if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", name):
            result.add_error(
                f"{file_path.name}: nameはkebab-case（小文字とハイフン）で記述してください: {name}"
            )
        if " " in name:
            result.add_error(f"{file_path.name}: nameにスペースは使用できません")

    # バージョン形式
    version = data.get("version", "")
    if version and not re.match(r"^\d+\.\d+\.\d+", version):
        result.add_warning(
            f"{file_path.name}: versionはセマンティックバージョニング（x.y.z）を推奨: {version}"
        )

    # パスの確認
    path_fields = [
        "commands",
        "agents",
        "skills",
        "hooks",
        "mcpServers",
        "lspServers",
        "outputStyles",
    ]
    for field in path_fields:
        value = data.get(field)
        if value and isinstance(value, str) and not value.startswith("./"):
            result.add_warning(f"{file_path.name}: {field}のパスは./で始めることを推奨: {value}")

    return result
