"""
monitors/monitors.json のバリデーター
"""

import re
from pathlib import Path

from .base import ValidationResult, parse_json_safe

# when フィールドの有効値
VALID_WHEN_ALWAYS = "always"
# when の on-skill-invoke:<skill-name> パターン
# 公式はスキル名の書式制約を明示していないが、既存ルール（kebab-case）に合わせて
# 一致しないものを警告扱いとする
ON_SKILL_INVOKE_PATTERN = re.compile(r"^on-skill-invoke:[a-z0-9]+(-[a-z0-9]+)*$")

# 既知のフィールド
KNOWN_FIELDS = {"name", "command", "description", "when"}

# 必須の文字列フィールド
REQUIRED_STRING_FIELDS = ("name", "command", "description")


def _validate_when_value(when: str) -> bool:
    """when の値が有効な形式かどうかを判定する"""
    if when == VALID_WHEN_ALWAYS:
        return True
    return bool(ON_SKILL_INVOKE_PATTERN.match(when))


def validate_monitors_entries(
    entries: list,
    file_path: Path,
    result: ValidationResult,
    label: str = "monitors",
) -> None:
    """
    モニターエントリ配列を検証する（plugin.json の monitors インライン指定と
    monitors/monitors.json で共通に使用）

    Args:
        entries: 検証する配列
        file_path: エラーメッセージ用のファイルパス
        result: 検証結果（呼び出し側が初期化する）
        label: エントリ位置のプレフィックス（デフォルト "monitors"）
    """
    seen_names: set[str] = set()

    for i, entry in enumerate(entries):
        prefix = f"{file_path.name}: {label}[{i}]"

        if not isinstance(entry, dict):
            result.add_error(f"{prefix}: エントリはオブジェクトが必要です")
            continue

        # 必須フィールド（string）
        for field in REQUIRED_STRING_FIELDS:
            value = entry.get(field)
            if value is None:
                result.add_error(f"{prefix}: {field}は必須です")
            elif not isinstance(value, str):
                result.add_error(f"{prefix}: {field}は文字列が必要です")
            elif not value:
                result.add_error(f"{prefix}: {field}は空文字列にできません")

        # name の重複チェック
        name = entry.get("name")
        if isinstance(name, str) and name:
            if name in seen_names:
                result.add_error(f"{prefix}: nameが重複しています: {name}")
            else:
                seen_names.add(name)

        # when のバリデーション
        when = entry.get("when")
        if when is not None:
            if not isinstance(when, str):
                result.add_error(f"{prefix}: whenは文字列が必要です")
            elif not _validate_when_value(when):
                result.add_warning(
                    f"{prefix}: whenの値が公式仕様に一致しません: {when}"
                    '（"always" または "on-skill-invoke:<skill-name>"）'
                )

        # 未知のフィールド警告
        for key in entry:
            if key not in KNOWN_FIELDS:
                result.add_warning(f"{prefix}: 未知のフィールド: {key}")


def validate_monitors_json(file_path: Path, content: str) -> ValidationResult:
    """バックグラウンドモニター設定（monitors.json）を検証する"""
    result = ValidationResult()

    data = parse_json_safe(content, file_path, result)
    if data is None:
        return result

    # トップレベルは配列
    if not isinstance(data, list):
        result.add_error(f"{file_path.name}: ルートは配列が必要です")
        return result

    if not data:
        result.add_warning(f"{file_path.name}: monitors設定が空です")
        return result

    validate_monitors_entries(data, file_path, result)
    return result
