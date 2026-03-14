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
        return bool(self.errors)

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


def _strip_quotes(value: str) -> str:
    """文字列からクォート（'または"）を除去する"""
    if len(value) >= 2:
        if (value[0] == '"' and value[-1] == '"') or (value[0] == "'" and value[-1] == "'"):
            return value[1:-1]
    return value


def _convert_yaml_value(value: str) -> Any:
    """YAML値を適切なPython型に変換する"""
    unquoted = _strip_quotes(value)
    if unquoted != value:
        return unquoted
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if value.isdigit():
        return int(value)
    return value


def _find_frontmatter_boundary(lines: list[str]) -> int:
    """フロントマターの終了行インデックスを返す。見つからなければ-1"""
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            return i
    return -1


class _FrontmatterParser:
    """簡易YAMLフロントマターパーサー（PyYAMLを使わない）"""

    def __init__(self):
        self.frontmatter: dict[str, Any] = {}
        self.warnings: list[str] = []
        self._list_key: str | None = None
        self._list_items: list[str] = []

    def _save_pending_list(self):
        """収集中のリストを保存する"""
        if self._list_key:
            self.frontmatter[self._list_key] = self._list_items if self._list_items else ""
            self._list_key = None
            self._list_items = []

    def _handle_list_item(self, stripped: str):
        """リストアイテムを処理する"""
        if not self._list_key:
            self.warnings.append("リスト/配列はキーの後に続く必要があります")
            return
        item = "" if stripped == "-" else _strip_quotes(stripped[2:].strip())
        self._list_items.append(item)

    def _handle_key_value(self, line: str):
        """キー: 値の行を処理する"""
        self._save_pending_list()
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()

        if not value:
            self._list_key = key
            self._list_items = []
        else:
            self.frontmatter[key] = _convert_yaml_value(value)

    def parse_line(self, line: str):
        """1行を解析する"""
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            return

        if stripped in ("|", ">") or stripped.endswith("|") or stripped.endswith(">"):
            self.warnings.append("複数行の値（|, >）はサポートされていません")
            self._save_pending_list()
            return

        if stripped.startswith("- ") or stripped == "-":
            self._handle_list_item(stripped)
            return

        if line.startswith("  ") and ":" in line:
            self.warnings.append("ネストされたオブジェクトはサポートされていません")
            self._save_pending_list()
            return

        if ":" in line:
            self._handle_key_value(line)

    def finalize(self):
        """解析を完了し、残りのリストを保存する"""
        self._save_pending_list()


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str, list[str]]:
    """
    YAMLフロントマターを解析する

    サポートする機能:
    - 単純なキー: 値
    - リスト/配列（YAML形式とカンマ区切り）

    制限事項（サポートしていない機能）:
    - 複数行の値（|, >）
    - ネストされたオブジェクト

    Returns:
        tuple: (frontmatter辞書, 本文, 警告リスト)
    """
    if not content.startswith("---"):
        return {}, content, []

    lines = content.split("\n")
    end_idx = _find_frontmatter_boundary(lines)
    if end_idx == -1:
        return {}, content, []

    body = "\n".join(lines[end_idx + 1 :])
    parser = _FrontmatterParser()
    for line in lines[1:end_idx]:
        parser.parse_line(line)
    parser.finalize()

    return parser.frontmatter, body, parser.warnings


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


def normalize_path(path: str) -> str:
    """
    プラグインパスを正規化する

    先頭・末尾のスラッシュを除去し、連続スラッシュを単一にする。

    Args:
        path: 正規化するパス文字列

    Returns:
        正規化されたパス
    """
    # 連続スラッシュを単一に
    normalized = re.sub(r"/+", "/", path)
    # 先頭・末尾のスラッシュを除去
    return normalized.strip("/")


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
