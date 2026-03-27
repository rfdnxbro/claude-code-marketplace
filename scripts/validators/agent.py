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


def _validate_task_syntax(tools_str: str) -> bool:
    """Task(agent_type)構文の妥当性を検証する"""
    # Task(xxx) の形式をチェック（xxxは空でない）
    pattern = r"Task\([^)]+\)"
    matches = re.findall(pattern, tools_str)
    if not matches:
        return False
    # すべてのマッチが有効な形式かチェック
    for match in matches:
        # Task() の中身が空でないことを確認
        inner = match[5:-1]  # "Task(" と ")" を除去
        if not inner.strip():
            return False
    return True


def validate_agent(file_path: Path, content: str) -> ValidationResult:
    """サブエージェントを検証する"""
    ctx = MarkdownValidationContext(file_path, content)
    result = ctx.result
    frontmatter = ctx.frontmatter

    # 必須フィールドの確認
    name_str = coerce_str(frontmatter.get("name", ""))
    if not name_str:
        result.add_error(f"{file_path.name}: nameが必須です")
    else:
        # kebab-case（小文字とハイフンのみ）チェック
        kebab_error = validate_kebab_case(name_str)
        if kebab_error:
            result.add_error(f"{file_path.name}: {kebab_error}")

    # descriptionの確認
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
    # フルモデルID（例: claude-opus-4-5, claude-sonnet-4-6, claude-haiku-4-5-20251001）のパターン
    full_model_id_pattern = re.compile(r"^claude-[a-z]+-[0-9][a-z0-9-]*$")
    if (
        model_str
        and model_str not in valid_shorthand_models
        and not full_model_id_pattern.match(model_str)
    ):
        result.add_warning(
            f"{file_path.name}: modelが不正: {model_str}"
            f"（sonnet/opus/haiku/inherit またはフルモデルID例: claude-sonnet-4-6）"
        )

    # permissionModeの値チェック
    validate_enum_field(
        frontmatter,
        "permissionMode",
        ["default", "acceptEdits", "bypassPermissions", "plan", "dontAsk"],
        file_path,
        result,
    )

    # memoryの値チェック（v2.1.33以降）
    validate_enum_field(
        frontmatter,
        "memory",
        ["user", "project", "local"],
        file_path,
        result,
        label="user/project/local",
    )

    # isolationの値チェック（v2.1.50以降）
    validate_enum_field(
        frontmatter,
        "isolation",
        ["worktree"],
        file_path,
        result,
        label="worktree",
    )

    # effortの値チェック（v2.1.78以降）
    validate_enum_field(
        frontmatter,
        "effort",
        ["low", "medium", "high", "max"],
        file_path,
        result,
        label="low/medium/high/max",
    )

    # backgroundの値チェック（v2.1.49以降）
    validate_bool_field(
        frontmatter,
        "background",
        file_path,
        result,
        message_suffix=f"ブール値（true/false）が必要です: {frontmatter.get('background')}",
    )

    # initialPromptの値チェック（v2.1.83以降）
    initial_prompt = frontmatter.get("initialPrompt")
    if initial_prompt is not None and not isinstance(initial_prompt, str):
        result.add_error(f"{file_path.name}: initialPromptは文字列が必要です: {initial_prompt}")

    # toolsの確認（リスト形式検証）
    tools = validate_string_list_field(frontmatter, "tools", file_path, result)
    if tools is not None:
        # Task(agent_type) 構文の検証
        tools_str = (
            tools if isinstance(tools, str) else " ".join(tools) if isinstance(tools, list) else ""
        )
        if "Task(" in tools_str and not _validate_task_syntax(tools_str):
            result.add_warning(
                f"{file_path.name}: Task()構文の形式を確認してください（例: Task(agent-name)）"
            )

    # disallowedToolsの確認（リスト形式検証）
    validate_string_list_field(frontmatter, "disallowedTools", file_path, result)

    # skillsの確認（リスト形式検証）
    validate_string_list_field(frontmatter, "skills", file_path, result)

    # 本文（システムプロンプト）の確認
    if not ctx.body.strip():
        result.add_warning(f"{file_path.name}: システムプロンプト（本文）が空です")

    return result
