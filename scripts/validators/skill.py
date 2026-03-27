"""
スキルのバリデーター
"""

import re
from pathlib import Path

from .base import (
    MarkdownValidationContext,
    ValidationResult,
    coerce_str,
    validate_agent_ref_field,
    validate_allowed_tools_field,
    validate_bool_field,
    validate_context_field,
    validate_effort_field,
    validate_enum_field,
)


def validate_skill(file_path: Path, content: str) -> ValidationResult:
    """スキルを検証する"""
    ctx = MarkdownValidationContext(file_path, content)
    result = ctx.result
    frontmatter = ctx.frontmatter

    # nameの確認
    name_str = coerce_str(frontmatter.get("name", ""))
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
    description_str = coerce_str(frontmatter.get("description", ""))
    if not description_str:
        result.add_error(f"{file_path.name}: descriptionが必須です")
    elif len(description_str) > 1024:
        result.add_error(
            f"{file_path.name}: descriptionは1024文字以内にしてください: {len(description_str)}文字"
        )

    # contextの確認
    validate_context_field(frontmatter, file_path, result)

    # modelの値チェック
    validate_enum_field(
        frontmatter,
        "model",
        ["sonnet", "opus", "haiku"],
        file_path,
        result,
        level="warning",
        label="sonnet/opus/haiku",
    )

    # user-invocableの確認（boolean型）
    validate_bool_field(
        frontmatter,
        "user-invocable",
        file_path,
        result,
        message_suffix="ブール値が必要です",
    )

    # agentの確認
    validate_agent_ref_field(frontmatter, file_path, result)

    # allowed-toolsの確認
    validate_allowed_tools_field(frontmatter, file_path, result, ctx.disabled_warnings)

    # effortの確認
    validate_effort_field(frontmatter, file_path, result)

    # hooksの確認（形式警告のみ）
    hooks = frontmatter.get("hooks")
    if hooks is not None:
        # hooksはYAML形式で定義されるため、フロントマターで直接設定されている場合は警告
        result.add_warning(f"{file_path.name}: hooksはhooks.jsonでの定義を推奨します")

    # 本文の行数チェック
    body_lines = ctx.body.strip().split("\n")
    if len(body_lines) > 500:
        result.add_warning(f"{file_path.name}: 本文が500行超（{len(body_lines)}行）。分割を検討")

    return result
