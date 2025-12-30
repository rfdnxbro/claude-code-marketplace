"""
共通ユーティリティ: ValidationResult と parse_frontmatter
"""

import re
from pathlib import Path
from typing import Any

# kebab-case検証用の正規表現（プリコンパイル）
KEBAB_CASE_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

# シークレット検出用パターン（プリコンパイル）
SECRET_PATTERNS = [
    (re.compile(r"sk-[a-zA-Z0-9]{32,}"), "OpenAI APIキー"),
    (re.compile(r"sk-proj-[a-zA-Z0-9]{32,}"), "OpenAI Project APIキー"),
    (re.compile(r"ghp_[a-zA-Z0-9]{36}"), "GitHub Personal Access Token"),
    (re.compile(r"gho_[a-zA-Z0-9]{36}"), "GitHub OAuth Token"),
    (re.compile(r"ghu_[a-zA-Z0-9]{36}"), "GitHub User Token"),
    (re.compile(r"ghs_[a-zA-Z0-9]{36}"), "GitHub Server Token"),
    (re.compile(r"xoxb-[a-zA-Z0-9-]+"), "Slack Bot Token"),
    (re.compile(r"xoxa-[a-zA-Z0-9-]+"), "Slack App Token"),
    (re.compile(r"xoxp-[a-zA-Z0-9-]+"), "Slack User Token"),
    (re.compile(r"AKIA[A-Z0-9]{16}"), "AWS Access Key ID"),
    (re.compile(r"AIza[a-zA-Z0-9_-]{35}"), "Google API Key"),
]

# 汎用的な機密情報パターン（長い英数字文字列）
GENERIC_SECRET_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")


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


def check_env_secrets(
    result: ValidationResult,
    file_path: Path,
    context_name: str,
    env: dict,
) -> None:
    """
    環境変数に機密情報が直接記述されていないかチェック

    Args:
        result: 検証結果オブジェクト
        file_path: 検証対象ファイルのパス
        context_name: エラーメッセージに含めるコンテキスト名（サーバー名など）
        env: 環境変数の辞書
    """
    for key, value in env.items():
        if not isinstance(value, str) or value.startswith("${"):
            continue

        # 既知の機密情報パターンをチェック
        for pattern, description in SECRET_PATTERNS:
            if pattern.search(value):
                result.add_error(
                    f"{file_path.name}: {context_name}: "
                    f"envの{key}に{description}が直接記述。${{{{VAR}}}}形式を使用"
                )
                break
        else:
            # 既知パターンに一致しない場合、汎用チェック（警告）
            if len(value) > 20 and GENERIC_SECRET_PATTERN.match(value):
                result.add_warning(
                    f"{file_path.name}: {context_name}: "
                    f"envの{key}に機密情報の可能性。${{{{VAR}}}}形式を使用"
                )
