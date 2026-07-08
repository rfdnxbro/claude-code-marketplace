"""
README.mdのバリデーター
"""

import re
from pathlib import Path

from .base import ValidationResult

# 必須セクション（日本語/英語の両方に対応）
REQUIRED_SECTIONS = [
    (r"##\s+(概要|Overview)", "概要/Overview"),
    (r"##\s+(インストール|Installation)", "インストール/Installation"),
    (r"##\s+(使い方|Usage)", "使い方/Usage"),
]


def validate_readme(file_path: Path, content: str) -> ValidationResult:
    """README.mdを検証する"""
    result = ValidationResult()

    # 必須セクションの存在確認
    for pattern, section_name in REQUIRED_SECTIONS:
        if not re.search(pattern, content, re.IGNORECASE):
            result.add_error(f"{file_path.name}: 必須セクション「{section_name}」がありません")

    # 相対パスリンクのチェック（コードブロック内のサンプルリンクは対象外にする）
    _check_relative_links(file_path, _strip_code_blocks(content), result)

    # コードブロックの言語指定チェック
    _check_code_blocks(file_path, content, result)

    return result


def _strip_code_blocks(content: str) -> str:
    """フェンス付きコードブロックの中身を空行に置き換えた文字列を返す

    行数・全体の構造は変えず、コードブロック内（フェンス行自体も含む）の
    内容だけを消す。判定ロジックは_check_code_blocksと同様。
    """
    lines = content.split("\n")
    in_code_block = False
    stripped_lines = []

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("```"):
            # コードブロックの開始/終了フラグを反転
            in_code_block = not in_code_block
            stripped_lines.append("")
        elif in_code_block:
            stripped_lines.append("")
        else:
            stripped_lines.append(line)

    return "\n".join(stripped_lines)


def _check_relative_links(file_path: Path, content: str, result: ValidationResult) -> None:
    """相対パスのリンク切れをチェックする"""
    # Markdownリンク: [text](path) 形式
    # 外部URL（http://, https://）は除外
    # 画像記法 ![alt](path) の [alt](path) 部分は除外（直前の!を否定先読み）
    link_pattern = r"(?<!!)\[([^\]]*)\]\(([^)]*)\)"
    base_dir = file_path.parent

    for match in re.finditer(link_pattern, content):
        link_text = match.group(1)
        link_path = match.group(2)

        # アンカーリンク（#で始まる）はスキップ
        if link_path.startswith("#"):
            continue

        # 外部URLはスキップ
        if link_path.startswith(("http://", "https://", "mailto:")):
            continue

        # アンカー部分を除去（例: ./file.md#section -> ./file.md）
        link_path_without_anchor = link_path.split("#")[0]
        if not link_path_without_anchor:
            continue

        # 相対パスを解決
        target_path = (base_dir / link_path_without_anchor).resolve()

        if not target_path.exists():
            result.add_error(
                f"{file_path.name}: リンク切れ [{link_text}]({link_path}) - ファイルが存在しません"
            )

    # 画像参照: ![alt](path) 形式
    image_pattern = r"!\[([^\]]*)\]\(([^)]+)\)"

    for match in re.finditer(image_pattern, content):
        alt_text = match.group(1)
        image_path = match.group(2)

        # 外部URLはスキップ
        if image_path.startswith(("http://", "https://")):
            continue

        # 相対パスを解決
        target_path = (base_dir / image_path).resolve()

        if not target_path.exists():
            result.add_error(
                f"{file_path.name}: 画像リンク切れ ![{alt_text}]({image_path}) "
                f"- ファイルが存在しません"
            )


def _check_code_blocks(file_path: Path, content: str, result: ValidationResult) -> None:
    """コードブロックの言語指定をチェックする"""
    # ```のみで言語指定がないコードブロックを検出
    # ```python や ```js などは対象外
    lines = content.split("\n")
    in_code_block = False

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        if stripped.startswith("```"):
            if not in_code_block:
                # コードブロック開始
                in_code_block = True
                # ``` の後に言語指定があるかチェック
                lang_spec = stripped[3:].strip()
                if not lang_spec:
                    result.add_warning(
                        f"{file_path.name}: {i}行目のコードブロックに言語指定がありません"
                    )
            else:
                # コードブロック終了
                in_code_block = False
