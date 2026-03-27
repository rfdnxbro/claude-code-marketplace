"""
README.mdのバリデーター
"""

import re
from pathlib import Path

from .base import ValidationResult

# 必須セクション（日本語/英語の両方に対応）
REQUIRED_SECTIONS = [
    (re.compile(r"##\s+(概要|Overview)", re.IGNORECASE), "概要/Overview"),
    (re.compile(r"##\s+(インストール|Installation)", re.IGNORECASE), "インストール/Installation"),
    (re.compile(r"##\s+(使い方|Usage)", re.IGNORECASE), "使い方/Usage"),
]

_LINK_PATTERN = re.compile(r"\[([^\]]*)\]\(([^)]*)\)")
_IMAGE_PATTERN = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")


def validate_readme(file_path: Path, content: str) -> ValidationResult:
    """README.mdを検証する"""
    result = ValidationResult()

    # 必須セクションの存在確認
    for pattern, section_name in REQUIRED_SECTIONS:
        if not pattern.search(content):
            result.add_error(f"{file_path.name}: 必須セクション「{section_name}」がありません")

    # 相対パスリンクのチェック
    _check_relative_links(file_path, content, result)

    # コードブロックの言語指定チェック
    _check_code_blocks(file_path, content, result)

    return result


def _check_relative_links(file_path: Path, content: str, result: ValidationResult) -> None:
    """相対パスのリンク切れをチェックする"""
    base_dir = file_path.parent

    for match in _LINK_PATTERN.finditer(content):
        link_text = match.group(1)
        link_path = match.group(2)

        if link_path.startswith(("#", "http://", "https://", "mailto:")):
            continue

        link_path_without_anchor = link_path.split("#")[0]
        if not link_path_without_anchor:
            continue

        target_path = (base_dir / link_path_without_anchor).resolve()

        if not target_path.exists():
            result.add_error(
                f"{file_path.name}: リンク切れ [{link_text}]({link_path}) - ファイルが存在しません"
            )

    for match in _IMAGE_PATTERN.finditer(content):
        alt_text = match.group(1)
        image_path = match.group(2)

        if image_path.startswith(("http://", "https://")):
            continue

        target_path = (base_dir / image_path).resolve()

        if not target_path.exists():
            result.add_error(
                f"{file_path.name}: 画像リンク切れ ![{alt_text}]({image_path}) "
                f"- ファイルが存在しません"
            )


def _check_code_blocks(file_path: Path, content: str, result: ValidationResult) -> None:
    """コードブロックの言語指定をチェックする"""
    lines = content.split("\n")
    in_code_block = False

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        if stripped.startswith("```"):
            if not in_code_block:
                in_code_block = True
                lang_spec = stripped[3:].strip()
                if not lang_spec:
                    result.add_warning(
                        f"{file_path.name}: {i}行目のコードブロックに言語指定がありません"
                    )
            else:
                in_code_block = False
