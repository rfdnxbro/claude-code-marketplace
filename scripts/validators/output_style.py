"""
出力スタイルのバリデーター
"""

from pathlib import Path

from .base import MarkdownValidationContext, ValidationResult, validate_bool_field


def validate_output_style(file_path: Path, content: str) -> ValidationResult:
    """出力スタイルを検証する"""
    ctx = MarkdownValidationContext(file_path, content)
    result = ctx.result
    frontmatter = ctx.frontmatter

    # nameフィールドの検証（オプション、指定時はファイル名と一致推奨）
    name = frontmatter.get("name", "")
    if name:
        if not isinstance(name, str):
            result.add_error(f"{file_path.name}: nameは文字列で指定してください")
        else:
            # ファイル名（拡張子除く）と異なる場合は警告
            stem = file_path.stem
            if name != stem:
                msg = (
                    f"{file_path.name}: nameとファイル名が異なります"
                    f"（name: {name}, ファイル: {stem}）"
                )
                result.add_warning(msg)

    # descriptionフィールドの検証（オプション、推奨）
    description = frontmatter.get("description", "")
    if description:
        if not isinstance(description, str):
            result.add_error(f"{file_path.name}: descriptionは文字列で指定してください")
    else:
        # description がない場合は推奨
        result.add_warning(f"{file_path.name}: descriptionの指定を推奨します（UIに表示されます）")

    # keep-coding-instructionsフィールドの検証（オプション、boolean）
    validate_bool_field(
        frontmatter,
        "keep-coding-instructions",
        file_path,
        result,
        message_suffix="true/falseで指定してください",
    )

    # 本文（スタイル指示）の確認
    if not ctx.body.strip():
        result.add_error(f"{file_path.name}: スタイル指示（本文）が必須です")

    return result
