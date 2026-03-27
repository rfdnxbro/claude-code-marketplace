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
    normalized = re.sub(r"/+", "/", path)
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


# --- 共通ヘルパー関数 ---


def coerce_str(value: Any) -> str:
    """frontmatter値を安全に文字列に変換する"""
    return str(value) if value else ""


class MarkdownValidationContext:
    """frontmatterベースのMarkdownファイル検証の共通セットアップ

    frontmatter解析、YAML警告の自動追加、disabled_warningsの取得を一括で行う。
    """

    def __init__(self, file_path: Path, content: str):
        self.file_path = file_path
        self.content = content
        self.result = ValidationResult()
        self.frontmatter, self.body, yaml_warnings = parse_frontmatter(content)
        self.disabled_warnings = get_disabled_warnings(content)
        for w in yaml_warnings:
            self.result.add_warning(f"{file_path.name}: {w}")


def validate_enum_field(
    frontmatter: dict[str, Any],
    field: str,
    valid_values: list[str],
    file_path: Path,
    result: ValidationResult,
    *,
    level: str = "error",
    label: str | None = None,
) -> str:
    """列挙値フィールドを検証する

    Args:
        frontmatter: フロントマター辞書
        field: フィールド名
        valid_values: 許可される値のリスト
        file_path: エラーメッセージ用のファイルパス
        result: 検証結果オブジェクト
        level: "error" または "warning"
        label: エラーメッセージに表示する値リスト（省略時はvalid_valuesから生成）

    Returns:
        変換後の文字列値
    """
    value = frontmatter.get(field, "")
    value_str = coerce_str(value)
    if value_str and value_str not in valid_values:
        display_label = label or "/".join(v for v in valid_values if v)
        message = f"{file_path.name}: {field}の値が不正です: {value_str}（{display_label}）"
        if level == "warning":
            result.add_warning(message)
        else:
            result.add_error(message)
    return value_str


def validate_bool_field(
    frontmatter: dict[str, Any],
    field: str,
    file_path: Path,
    result: ValidationResult,
    *,
    message_suffix: str = "ブール値が必要です",
) -> bool | None:
    """booleanフィールドを検証する

    Returns:
        フィールドの値。未設定ならNone
    """
    value = frontmatter.get(field)
    if value is not None and not isinstance(value, bool):
        result.add_error(f"{file_path.name}: {field}は{message_suffix}")
    return value


def validate_string_list_field(
    frontmatter: dict[str, Any],
    field: str,
    file_path: Path,
    result: ValidationResult,
) -> str | list | None:
    """文字列またはリスト型フィールドを検証する

    Returns:
        フィールドの値。未設定ならNone
    """
    value = frontmatter.get(field)
    if value is None:
        return None
    if not isinstance(value, (str, list)):
        result.add_error(f"{file_path.name}: {field}は文字列またはリストが必要です")
    elif isinstance(value, list):
        for item in value:
            if not isinstance(item, str) or not item:
                result.add_error(f"{file_path.name}: {field}の各要素は空でない文字列が必要です")
                break
    return value


def validate_context_field(
    frontmatter: dict[str, Any],
    file_path: Path,
    result: ValidationResult,
) -> None:
    """contextフィールドを検証する（forkのみ有効）"""
    context = frontmatter.get("context")
    if context is not None:
        context_str = coerce_str(context)
        if context_str and context_str != "fork":
            result.add_error(
                f"{file_path.name}: contextの値が不正です: {context_str}（forkのみ有効）"
            )


def validate_allowed_tools_field(
    frontmatter: dict[str, Any],
    file_path: Path,
    result: ValidationResult,
    disabled_warnings: set[str],
) -> None:
    """allowed-toolsフィールドを検証する（Bash(*)警告を含む）"""
    allowed_tools = frontmatter.get("allowed-tools")
    if allowed_tools is None:
        return
    if isinstance(allowed_tools, list):
        tools_str = ", ".join(str(t) for t in allowed_tools)
    else:
        tools_str = str(allowed_tools)

    if "Bash(*)" in tools_str:
        if WARNING_BROAD_BASH_WILDCARD not in disabled_warnings:
            result.add_warning(
                f"{file_path.name}: allowed-toolsにBash(*)が指定。"
                "v2.1.20以降Bash(*)はBashと同等に扱われますが、具体的なパターンを推奨"
            )


def validate_agent_ref_field(
    frontmatter: dict[str, Any],
    file_path: Path,
    result: ValidationResult,
) -> None:
    """agentフィールドを検証する（空でない文字列が必要）"""
    agent = frontmatter.get("agent")
    if agent is not None:
        agent_str = coerce_str(agent)
        if not agent_str:
            result.add_error(f"{file_path.name}: agentは空でない文字列が必要です")


def validate_effort_field(
    frontmatter: dict[str, Any],
    file_path: Path,
    result: ValidationResult,
    *,
    valid_values: list[str] | None = None,
    level: str = "warning",
) -> None:
    """effortフィールドを検証する

    Args:
        valid_values: 許可される値のリスト。省略時は["low", "normal", "high"]
        level: "error" または "warning"
    """
    effort = frontmatter.get("effort")
    if effort is None:
        return
    effort_str = coerce_str(effort)
    values = valid_values or ["low", "normal", "high"]
    if effort_str and effort_str not in values:
        display = "/".join(values)
        message = f"{file_path.name}: effortが不正: {effort_str}（{display}）"
        if level == "warning":
            result.add_warning(message)
        else:
            result.add_error(message)
