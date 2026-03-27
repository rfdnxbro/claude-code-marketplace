"""
サブエージェントのバリデーター
"""

import re
from pathlib import Path

from .base import (
    ValidationResult,
    add_yaml_warnings,
    parse_frontmatter,
    to_str,
    validate_effort_field,
    validate_kebab_case,
    validate_string_or_list_field,
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
    result = ValidationResult()
    frontmatter, body, yaml_warnings = parse_frontmatter(content)

    add_yaml_warnings(result, file_path, yaml_warnings)

    # 必須フィールドの確認
    name = frontmatter.get("name", "")
    name_str = to_str(name)
    if not name_str:
        result.add_error(f"{file_path.name}: nameが必須です")
    else:
        # kebab-case（小文字とハイフンのみ）チェック
        kebab_error = validate_kebab_case(name_str)
        if kebab_error:
            result.add_error(f"{file_path.name}: {kebab_error}")

    # descriptionの確認
    description = frontmatter.get("description", "")
    description_str = to_str(description)
    if not description_str:
        result.add_error(f"{file_path.name}: descriptionが必須です")
    elif len(description_str) < 20:
        result.add_warning(
            f"{file_path.name}: descriptionが短すぎます。いつ使うべきかを明確に記述してください"
        )

    # modelの値チェック（v2.1.74以降: フルモデルIDも使用可能）
    model = frontmatter.get("model", "")
    model_str = to_str(model)
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
    permission_mode = frontmatter.get("permissionMode", "")
    permission_mode_str = to_str(permission_mode)
    valid_modes = ["default", "acceptEdits", "bypassPermissions", "plan", "dontAsk", ""]
    if permission_mode_str and permission_mode_str not in valid_modes:
        result.add_error(f"{file_path.name}: permissionModeの値が不正です: {permission_mode_str}")

    # memoryの値チェック（v2.1.33以降）
    memory = frontmatter.get("memory", "")
    memory_str = to_str(memory)
    valid_memory_scopes = ["user", "project", "local", ""]
    if memory_str and memory_str not in valid_memory_scopes:
        result.add_error(
            f"{file_path.name}: memoryの値が不正です: {memory_str}（user/project/local）"
        )

    # isolationの値チェック（v2.1.50以降）
    isolation = frontmatter.get("isolation", "")
    isolation_str = to_str(isolation)
    valid_isolation_modes = ["worktree", ""]
    if isolation_str and isolation_str not in valid_isolation_modes:
        result.add_error(f"{file_path.name}: isolationの値が不正です: {isolation_str}（worktree）")

    # effortの値チェック（v2.1.78以降）
    validate_effort_field(
        result,
        file_path,
        frontmatter,
        ["low", "medium", "high", "max"],
        level="error",
        hint="low/medium/high/max",
    )

    # backgroundの値チェック（v2.1.49以降）
    background = frontmatter.get("background")
    if background is not None and not isinstance(background, bool):
        result.add_error(
            f"{file_path.name}: backgroundはブール値（true/false）が必要です: {background}"
        )

    # initialPromptの値チェック（v2.1.83以降）
    initial_prompt = frontmatter.get("initialPrompt")
    if initial_prompt is not None and not isinstance(initial_prompt, str):
        result.add_error(f"{file_path.name}: initialPromptは文字列が必要です: {initial_prompt}")

    # toolsの確認（リスト形式検証）
    tools = frontmatter.get("tools")
    validate_string_or_list_field(result, file_path, "tools", tools)
    # Task(agent_type) 構文の検証
    if tools is not None:
        tools_str = (
            tools if isinstance(tools, str) else " ".join(tools) if isinstance(tools, list) else ""
        )
        if "Task(" in tools_str and not _validate_task_syntax(tools_str):
            result.add_warning(
                f"{file_path.name}: Task()構文の形式を確認してください（例: Task(agent-name)）"
            )

    # disallowedToolsの確認（リスト形式検証）
    validate_string_or_list_field(
        result, file_path, "disallowedTools", frontmatter.get("disallowedTools")
    )

    # skillsの確認（リスト形式検証）
    validate_string_or_list_field(result, file_path, "skills", frontmatter.get("skills"))

    # 本文（システムプロンプト）の確認
    if not body.strip():
        result.add_warning(f"{file_path.name}: システムプロンプト（本文）が空です")

    return result
