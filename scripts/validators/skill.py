"""
スキルのバリデーター
"""

import re
from pathlib import Path

from .base import ValidationResult, parse_frontmatter


def validate_skill(file_path: Path, content: str) -> ValidationResult:
    """スキルを検証する"""
    result = ValidationResult()
    frontmatter, body, yaml_warnings = parse_frontmatter(content)

    # YAML警告を追加
    for w in yaml_warnings:
        result.add_warning(f"{file_path.name}: {w}")

    # nameの確認
    name = frontmatter.get("name", "")
    name_str = str(name) if name else ""
    if not name_str:
        result.add_error(f"{file_path.name}: nameが必須です")
    else:
        # 形式チェック
        if len(name_str) > 64:
            result.add_error(f"{file_path.name}: nameは64文字以内にしてください: {len(name_str)}文字")
        if not re.match(r"^[a-z0-9-]+$", name_str):
            result.add_error(f"{file_path.name}: nameは小文字、数字、ハイフンのみ使用可能です")
        # 予約語チェック
        if "anthropic" in name_str.lower() or "claude" in name_str.lower():
            result.add_error(f"{file_path.name}: nameに予約語（anthropic, claude）は使用できません")

    # descriptionの確認
    description = frontmatter.get("description", "")
    description_str = str(description) if description else ""
    if not description_str:
        result.add_error(f"{file_path.name}: descriptionが必須です")
    elif len(description_str) > 1024:
        result.add_error(f"{file_path.name}: descriptionは1024文字以内にしてください: {len(description_str)}文字")

    # 本文の行数チェック
    body_lines = body.strip().split("\n")
    if len(body_lines) > 500:
        result.add_warning(f"{file_path.name}: 本文が500行を超えています（{len(body_lines)}行）。別ファイルへの分割を検討してください")

    return result
