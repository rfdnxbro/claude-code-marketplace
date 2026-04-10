"""
スラッシュコマンドのバリデーター
"""

import re
from pathlib import Path

from .base import (
    WARNING_DANGEROUS_OPERATION,
    ValidationResult,
    add_yaml_warnings,
    get_disabled_warnings,
    parse_frontmatter,
    to_str,
    validate_agent_field,
    validate_allowed_tools,
    validate_context_field,
    validate_effort_field,
)

# 引用符なしのYAMLブール値キーワードを検出するパターン
# 文字列フィールド（description, name）で引用符なしのブール値キーワードを検出する
_UNQUOTED_BOOL_PATTERN = re.compile(
    r"^(description|name)\s*:\s*(?![\"'])(true|false|on|off|yes|no|y|n)\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def _find_unquoted_bool_fields(content: str) -> list[tuple[str, str]]:
    """frontmatterで引用符なしのYAMLブール値キーワードを持つフィールドを検出する"""
    if not content.startswith("---"):
        return []
    lines = content.split("\n")
    end_idx = -1
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            end_idx = i
            break
    if end_idx == -1:
        return []
    frontmatter_text = "\n".join(lines[1:end_idx])
    return _UNQUOTED_BOOL_PATTERN.findall(frontmatter_text)


def validate_slash_command(file_path: Path, content: str) -> ValidationResult:
    """スラッシュコマンドを検証する"""
    result = ValidationResult()
    frontmatter, body, yaml_warnings = parse_frontmatter(content)
    disabled_warnings = get_disabled_warnings(content)

    add_yaml_warnings(result, file_path, yaml_warnings)

    # description / name フィールドに引用符なしのYAMLブール値キーワードが使われていないか確認
    bool_fields = _find_unquoted_bool_fields(content)
    bool_field_names = {field for field, _ in bool_fields}
    for field, keyword in bool_fields:
        result.add_warning(
            f"{file_path.name}: {field}にYAMLブール値キーワードが使用されています。"
            f'引用符で囲んでください（例: {field}: "{keyword}"）'
        )

    # descriptionの確認
    description_raw = frontmatter.get("description")
    if "description" not in bool_field_names and not description_raw:
        # 本文の最初の行がデフォルトになるが、明示的に設定することを推奨
        if body.strip():
            result.add_warning(
                f"{file_path.name}: descriptionが未設定（本文の最初の行がデフォルトで使用される）"
            )
        else:
            result.add_error(f"{file_path.name}: descriptionが未設定で本文も空")

    # argument-hintの確認（文字列型）
    argument_hint = frontmatter.get("argument-hint")
    if argument_hint is not None:
        if not isinstance(argument_hint, str) or not argument_hint.strip():
            result.add_warning(f"{file_path.name}: argument-hintは空でない文字列が必要です")

    # allowed-toolsの確認（リスト形式対応）
    validate_allowed_tools(result, file_path, frontmatter, disabled_warnings)

    # contextの確認（forkのみサポート、省略時はメインコンテキスト）
    validate_context_field(result, file_path, frontmatter)

    # agentの確認（空でない文字列）
    validate_agent_field(result, file_path, frontmatter)

    # disable-model-invocationの確認
    disable_model = frontmatter.get("disable-model-invocation", False)
    # 危険そうなキーワードが含まれる場合は警告
    dangerous_keywords = ["deploy", "delete", "drop", "production", "本番"]
    description = frontmatter.get("description", "")
    description_str = to_str(description)
    if any(kw in body.lower() or kw in description_str.lower() for kw in dangerous_keywords):
        if disable_model is not True:
            if WARNING_DANGEROUS_OPERATION not in disabled_warnings:
                result.add_warning(
                    f"{file_path.name}: 危険な操作の可能性。disable-model-invocation: trueを検討"
                )

    # modelの値チェック（短縮形のみ許可、inheritは不可）
    model = frontmatter.get("model")
    model_str = str(model).strip() if model is not None else ""
    valid_models = {"sonnet", "opus", "haiku"}
    if model_str and model_str not in valid_models:
        result.add_warning(f"{file_path.name}: modelが不正: {model_str}（sonnet/opus/haiku）")

    # effortの確認（v2.1.80以降）
    validate_effort_field(
        result, file_path, frontmatter, ["low", "normal", "high"], hint="low/normal/high"
    )

    return result
