"""
共通ユーティリティ: ValidationResult と parse_frontmatter
"""

import json
import re
from pathlib import Path
from typing import Any

# kebab-case検証用の正規表現（プリコンパイル）
KEBAB_CASE_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

# 警告スキップコメントの正規表現
# 形式: <!-- validator-disable warning-id -->
DISABLE_PATTERN = re.compile(r"<!--\s*validator-disable\s+([\w-]+)\s*-->")

# 警告ID定数
WARNING_DANGEROUS_OPERATION = "dangerous-operation"
WARNING_BROAD_BASH_WILDCARD = "broad-bash-wildcard"


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
    body = "\n".join(lines[end_idx + 1 :])

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


def validate_kebab_case(name: str) -> str | None:
    """
    kebab-case形式（小文字とハイフン）を検証する

    Args:
        name: 検証する文字列

    Returns:
        エラーメッセージ。問題なければNone
    """
    if not KEBAB_CASE_PATTERN.match(name):
        return f"nameはkebab-case（小文字とハイフン）のみ: {name}"
    return None


def parse_json_safe(content: str, file_path: Path, result: ValidationResult) -> dict | None:
    """
    JSON文字列を安全にパースする

    Args:
        content: JSON文字列
        file_path: エラーメッセージ用のファイルパス
        result: 検証結果オブジェクト

    Returns:
        パース成功時はdict、失敗時はNone（resultにエラーを追加）
    """
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        result.add_error(f"{file_path.name}: JSONパースエラー: {e}")
        return None


def get_disabled_warnings(content: str) -> set[str]:
    """
    ファイル内容から無効化された警告IDを取得する

    形式: <!-- validator-disable warning-id -->

    Args:
        content: ファイル全体の内容

    Returns:
        無効化されている警告IDのset
    """
    return set(DISABLE_PATTERN.findall(content))
