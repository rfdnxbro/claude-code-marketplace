"""
サブエージェントのバリデーター
"""

import re
from pathlib import Path

from .base import ValidationResult, parse_frontmatter


def validate_agent(file_path: Path, content: str) -> ValidationResult:
    """サブエージェントを検証する"""
    result = ValidationResult()
    frontmatter, body = parse_frontmatter(content)

    # 必須フィールドの確認
    name = frontmatter.get("name", "")
    if not name:
        result.add_error(f"{file_path.name}: nameが必須です")
    else:
        # kebab-case（小文字とハイフンのみ）チェック
        if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", name):
            result.add_error(f"{file_path.name}: nameは小文字とハイフンのみ使用可能です（kebab-case）: {name}")

    # descriptionの確認
    description = frontmatter.get("description", "")
    if not description:
        result.add_error(f"{file_path.name}: descriptionが必須です")
    elif len(description) < 20:
        result.add_warning(f"{file_path.name}: descriptionが短すぎます。いつ使うべきかを明確に記述してください")

    # modelの値チェック
    model = frontmatter.get("model", "")
    valid_models = ["sonnet", "opus", "haiku", "inherit", ""]
    if model and model not in valid_models:
        result.add_warning(f"{file_path.name}: modelの値が不正です: {model}（sonnet, opus, haiku, inheritのいずれか）")

    # permissionModeの値チェック
    permission_mode = frontmatter.get("permissionMode", "")
    valid_modes = ["default", "acceptEdits", "bypassPermissions", "plan", "ignore", ""]
    if permission_mode and permission_mode not in valid_modes:
        result.add_error(f"{file_path.name}: permissionModeの値が不正です: {permission_mode}")

    # 本文（システムプロンプト）の確認
    if not body.strip():
        result.add_warning(f"{file_path.name}: システムプロンプト（本文）が空です")

    return result
