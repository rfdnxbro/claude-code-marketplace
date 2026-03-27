"""
サブエージェントのバリデーター
"""

import re
from pathlib import Path

from .base import (
    MarkdownValidationContext,
    ValidationResult,
    coerce_str,
    validate_bool_field,
    validate_enum_field,
    validate_kebab_case,
    validate_string_list_field,
)

_TASK_SYNTAX_PATTERN = re.compile(r"Task\([^)]+\)")
_FULL_MODEL_ID_PATTERN = re.compile(r"^claude-[a-z]+-[0-9][a-z0-9-]*$")


def _validate_task_syntax(tools_str: str) -> bool:
    """Task(agent_type)構文の妥当性を検証する"""
    matches = _TASK_SYNTAX_PATTERN.findall(tools_str)
    if not matches:
        return False
    for match in matches:
        inner = match[5:-1]
        if not inner.strip():
            return False
    return True


def validate_agent(file_path: Path, content: str) -> ValidationResult:
    """サブエージェントを検証する"""
    ctx = MarkdownValidationContext(file_path, content)
    result = ctx.result
    frontmatter = ctx.frontmatter

    name_str = coerce_str(frontmatter.get("name", ""))
    if not name_str:
        result.add_error(f"{file_path.name}: nameが必須です")
    else:
        kebab_error = validate_kebab_case(name_str)
        if kebab_error:
            result.add_error(f"{file_path.name}: {kebab_error}")

    description_str = coerce_str(frontmatter.get("description", ""))
    if not description_str:
        result.add_error(f"{file_path.name}: descriptionが必須です")
    elif len(description_str) < 20:
        result.add_warning(
            f"{file_path.name}: descriptionが短すぎます。いつ使うべきかを明確に記述してください"
        )

    # modelの値チェック（v2.1.74以降: フルモデルIDも使用可能）
    model_str = coerce_str(frontmatter.get("model", ""))
    valid_shorthand_models = ["sonnet", "opus", "haiku", "inherit"]
    if (
        model_str
        and model_str not in valid_shorthand_models
        and not _FULL_MODEL_ID_PATTERN.match(model_str)
    ):
        result.add_warning(
            f"{file_path.name}: modelが不正: {model_str}"
            f"（sonnet/opus/haiku/inherit またはフルモデルID例: claude-sonnet-4-6）"
        )

    validate_enum_field(
        frontmatter,
        "permissionMode",
        ["default", "acceptEdits", "bypassPermissions", "plan", "dontAsk"],
        file_path,
        result,
    )

    validate_enum_field(
        frontmatter,
        "memory",
        ["user", "project", "local"],
        file_path,
        result,
        label="user/project/local",
    )

    validate_enum_field(
        frontmatter,
        "isolation",
        ["worktree"],
        file_path,
        result,
        label="worktree",
    )

    validate_enum_field(
        frontmatter,
        "effort",
        ["low", "medium", "high", "max"],
        file_path,
        result,
        label="low/medium/high/max",
    )

    validate_bool_field(
        frontmatter,
        "background",
        file_path,
        result,
        message_suffix=f"ブール値（true/false）が必要です: {frontmatter.get('background')}",
    )

    initial_prompt = frontmatter.get("initialPrompt")
    if initial_prompt is not None and not isinstance(initial_prompt, str):
        result.add_error(f"{file_path.name}: initialPromptは文字列が必要です: {initial_prompt}")

    tools = validate_string_list_field(frontmatter, "tools", file_path, result)
    if tools is not None:
        tools_str = (
            tools if isinstance(tools, str) else " ".join(tools) if isinstance(tools, list) else ""
        )
        if "Task(" in tools_str and not _validate_task_syntax(tools_str):
            result.add_warning(
                f"{file_path.name}: Task()構文の形式を確認してください（例: Task(agent-name)）"
            )

    validate_string_list_field(frontmatter, "disallowedTools", file_path, result)
    validate_string_list_field(frontmatter, "skills", file_path, result)

    if not ctx.body.strip():
        result.add_warning(f"{file_path.name}: システムプロンプト（本文）が空です")

    return result
