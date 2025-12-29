"""
共通ユーティリティ: ValidationResult と parse_frontmatter
"""

from typing import Any


class ValidationResult:
    """検証結果を管理するクラス"""

    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def add_error(self, message: str):
        self.errors.append(message)

    def add_warning(self, message: str):
        self.warnings.append(message)

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def to_message(self) -> str:
        lines = []
        if self.errors:
            lines.append("❌ エラー:")
            for e in self.errors:
                lines.append(f"  - {e}")
        if self.warnings:
            lines.append("⚠️ 警告:")
            for w in self.warnings:
                lines.append(f"  - {w}")
        return "\n".join(lines)


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str, list[str]]:
    """
    YAMLフロントマターを解析する

    制限事項（サポートしていない機能）:
    - 複数行の値（|, >）
    - リスト/配列
    - ネストされたオブジェクト

    Returns:
        tuple: (frontmatter辞書, 本文, 警告リスト)
    """
    warnings: list[str] = []

    if not content.startswith("---"):
        return {}, content, warnings

    lines = content.split("\n")
    end_idx = -1
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            end_idx = i
            break

    if end_idx == -1:
        return {}, content, warnings

    frontmatter_lines = lines[1:end_idx]
    body = "\n".join(lines[end_idx + 1:])

    # 簡易YAMLパーサー（PyYAMLを使わない）
    frontmatter = {}
    for line in frontmatter_lines:
        # 空行とコメントをスキップ
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # サポートしていない機能を検出
        if stripped in ["|", ">"] or stripped.endswith("|") or stripped.endswith(">"):
            warnings.append("複数行の値（|, >）はサポートされていません")
            continue
        if stripped.startswith("- "):
            warnings.append("リスト/配列はサポートされていません")
            continue
        if line.startswith("  ") and ":" in line:
            warnings.append("ネストされたオブジェクトはサポートされていません")
            continue

        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()

            # 文字列のクォートを除去
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]

            # 型変換
            if value.lower() == "true":
                frontmatter[key] = True
            elif value.lower() == "false":
                frontmatter[key] = False
            elif value.isdigit():
                frontmatter[key] = int(value)
            else:
                frontmatter[key] = value

    return frontmatter, body, warnings
