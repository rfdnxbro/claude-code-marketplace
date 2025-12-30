"""
サブエージェントのバリデーター
"""

from pathlib import Path

from .base import ValidationResult, parse_frontmatter, validate_kebab_case


def validate_agent(file_path: Path, content: str) -> ValidationResult:
    """サブエージェントを検証する"""
    result = ValidationResult()
    frontmatter, body, yaml_warnings = parse_frontmatter(content)

    # YAML警告を追加
    for w in yaml_warnings:
        result.add_warning(f"{file_path.name}: {w}")

    # 必須フィールドの確認
    name = frontmatter.get("name", "")
    name_str = str(name) if name else ""
    if not name_str:
        result.add_error(f"{file_path.name}: nameが必須です")
    else:
        # kebab-case（小文字とハイフンのみ）チェック
        kebab_error = validate_kebab_case(name_str)
        if kebab_error:
            result.add_error(f"{file_path.name}: {kebab_error}")

    # descriptionの確認
    description = frontmatter.get("description", "")
    description_str = str(description) if description else ""
    if not description_str:
        result.add_error(f"{file_path.name}: descriptionが必須です")
    elif len(description_str) < 20:
        result.add_warning(
            f"{file_path.name}: descriptionが短すぎます。いつ使うべきかを明確に記述してください"
        )

    # modelの値チェック
    model = frontmatter.get("model", "")
    model_str = str(model) if model else ""
    valid_models = ["sonnet", "opus", "haiku", "inherit", ""]
    if model_str and model_str not in valid_models:
        result.add_warning(
            f"{file_path.name}: modelが不正: {model_str}（sonnet/opus/haiku/inherit）"
        )

    # permissionModeの値チェック
    permission_mode = frontmatter.get("permissionMode", "")
    permission_mode_str = str(permission_mode) if permission_mode else ""
    valid_modes = ["default", "acceptEdits", "bypassPermissions", "plan", "ignore", ""]
    if permission_mode_str and permission_mode_str not in valid_modes:
        result.add_error(f"{file_path.name}: permissionModeの値が不正です: {permission_mode_str}")

    # 本文（システムプロンプト）の確認
    if not body.strip():
        result.add_warning(f"{file_path.name}: システムプロンプト（本文）が空です")

    return result
