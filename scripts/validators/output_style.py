"""
出力スタイルのバリデーター
"""

from pathlib import Path

from .base import ValidationResult, parse_frontmatter


def validate_output_style(file_path: Path, content: str) -> ValidationResult:
    """出力スタイルを検証する"""
    result = ValidationResult()
    frontmatter, body, yaml_warnings = parse_frontmatter(content)

    # YAML警告を追加
    for w in yaml_warnings:
        result.add_warning(f"{file_path.name}: {w}")

    # nameフィールドの検証（オプション、指定時はファイル名と一致推奨）
    name = frontmatter.get("name", "")
    if name and not isinstance(name, str):
        result.add_error(f"{file_path.name}: nameは文字列で指定してください")
        name_str = ""
    else:
        name_str = str(name) if name else ""
    if name_str:
        # ファイル名（拡張子除く）と異なる場合は警告
        stem = file_path.stem
        if name_str != stem:
            msg = (
                f"{file_path.name}: nameとファイル名が異なります"
                f"（name: {name_str}, ファイル: {stem}）"
            )
            result.add_warning(msg)

    # descriptionフィールドの検証（オプション、推奨）
    description = frontmatter.get("description", "")
    if description and not isinstance(description, str):
        result.add_error(f"{file_path.name}: descriptionは文字列で指定してください")
        description_str = ""
    else:
        description_str = str(description) if description else ""
    if not description_str:
        result.add_warning(f"{file_path.name}: descriptionの指定を推奨します（UIに表示されます）")

    # keep-coding-instructionsフィールドの検証（オプション、boolean）
    keep_coding = frontmatter.get("keep-coding-instructions")
    if keep_coding is not None and not isinstance(keep_coding, bool):
        result.add_error(
            f"{file_path.name}: keep-coding-instructionsはtrue/falseで指定してください"
        )

    # 本文（スタイル指示）の確認
    if not body.strip():
        result.add_error(f"{file_path.name}: スタイル指示（本文）が必須です")

    return result
