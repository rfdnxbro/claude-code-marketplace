"""
スキルのバリデーター
"""

import re
from pathlib import Path

from .base import (
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


def validate_skill(file_path: Path, content: str) -> ValidationResult:
    """スキルを検証する"""
    result = ValidationResult()
    frontmatter, body, yaml_warnings = parse_frontmatter(content)
    disabled_warnings = get_disabled_warnings(content)

    add_yaml_warnings(result, file_path, yaml_warnings)

    # nameの確認
    name = frontmatter.get("name", "")
    name_str = to_str(name)
    if not name_str:
        result.add_error(f"{file_path.name}: nameが必須です")
    else:
        # 形式チェック
        if len(name_str) > 64:
            result.add_error(
                f"{file_path.name}: nameは64文字以内にしてください: {len(name_str)}文字"
            )
        if not re.match(r"^[a-z0-9-]+$", name_str):
            result.add_error(f"{file_path.name}: nameは小文字、数字、ハイフンのみ使用可能です")
        # 予約語チェック
        if "anthropic" in name_str.lower() or "claude" in name_str.lower():
            result.add_error(f"{file_path.name}: nameに予約語（anthropic, claude）は使用できません")

    # descriptionの確認
    description = frontmatter.get("description", "")
    description_str = to_str(description)
    if not description_str:
        result.add_error(f"{file_path.name}: descriptionが必須です")
    elif len(description_str) > 1536:
        result.add_error(
            f"{file_path.name}: descriptionは1536文字以内にしてください: {len(description_str)}文字"
        )

    # contextの確認（forkのみサポート、省略時はメインコンテキスト）
    validate_context_field(result, file_path, frontmatter)

    # modelの値チェック
    model = frontmatter.get("model", "")
    model_str = to_str(model)
    valid_models = ["sonnet", "opus", "haiku", ""]
    if model_str and model_str not in valid_models:
        result.add_warning(f"{file_path.name}: modelが不正: {model_str}（sonnet/opus/haiku）")

    # user-invocableの確認（boolean型）
    user_invocable = frontmatter.get("user-invocable")
    if user_invocable is not None and not isinstance(user_invocable, bool):
        result.add_error(f"{file_path.name}: user-invocableはブール値が必要です")

    # agentの確認（空でない文字列）
    validate_agent_field(result, file_path, frontmatter)

    # allowed-toolsの確認（リスト形式対応）
    validate_allowed_tools(result, file_path, frontmatter, disabled_warnings)

    # effortの確認（v2.1.80以降。v2.1.111でxhigh追加、maxも従来から有効）
    validate_effort_field(
        result,
        file_path,
        frontmatter,
        ["low", "medium", "high", "xhigh", "max"],
        hint="low/medium/high/xhigh/max",
    )

    # hooksの確認（形式警告のみ）
    hooks = frontmatter.get("hooks")
    if hooks is not None:
        # hooksはYAML形式で定義されるため、フロントマターで直接設定されている場合は警告
        result.add_warning(f"{file_path.name}: hooksはhooks.jsonでの定義を推奨します")

    # 本文の行数チェック
    body_lines = body.strip().split("\n")
    if len(body_lines) > 500:
        result.add_warning(f"{file_path.name}: 本文が500行超（{len(body_lines)}行）。分割を検討")

    return result
