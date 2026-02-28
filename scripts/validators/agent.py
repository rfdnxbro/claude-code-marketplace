"""
サブエージェントのバリデーター
"""

import re
from pathlib import Path

from .base import ValidationResult, parse_frontmatter, validate_kebab_case


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

    # YAML警告を追加
    for w in yaml_warnings:
        result.add_warning(f"{file_path.name}: {w}")

    # 必須フィールドの確認
    name = frontmatter.get("name", "")
    name_str = str(name) if name else ""
    if not name_str:
        result.add_error(f"{file_path.name}: nameが必須です")
    else:
        # kebab-case（小文字とハイフンのみ）チェック
        kebab_error = validate_kebab_case(name_str)
        if kebab_error:
            result.add_error(f"{file_path.name}: {kebab_error}")

    # descriptionの確認
    description = frontmatter.get("description", "")
    description_str = str(description) if description else ""
    if not description_str:
        result.add_error(f"{file_path.name}: descriptionが必須です")
    elif len(description_str) < 20:
        result.add_warning(
            f"{file_path.name}: descriptionが短すぎます。いつ使うべきかを明確に記述してください"
        )

    # modelの値チェック
    model = frontmatter.get("model", "")
    model_str = str(model) if model else ""
    valid_models = ["sonnet", "opus", "haiku", "inherit", ""]
    if model_str and model_str not in valid_models:
        result.add_warning(
            f"{file_path.name}: modelが不正: {model_str}（sonnet/opus/haiku/inherit）"
        )

    # permissionModeの値チェック
    permission_mode = frontmatter.get("permissionMode", "")
    permission_mode_str = str(permission_mode) if permission_mode else ""
    valid_modes = ["default", "acceptEdits", "bypassPermissions", "plan", "dontAsk", ""]
    if permission_mode_str and permission_mode_str not in valid_modes:
        result.add_error(f"{file_path.name}: permissionModeの値が不正です: {permission_mode_str}")

    # memoryの値チェック（v2.1.33以降）
    memory = frontmatter.get("memory", "")
    memory_str = str(memory) if memory else ""
    valid_memory_scopes = ["user", "project", "local", ""]
    if memory_str and memory_str not in valid_memory_scopes:
        result.add_error(
            f"{file_path.name}: memoryの値が不正です: {memory_str}（user/project/local）"
        )

    # isolationの値チェック（v2.1.50以降）
    isolation = frontmatter.get("isolation", "")
    isolation_str = str(isolation) if isolation else ""
    valid_isolation_modes = ["worktree", ""]
    if isolation_str and isolation_str not in valid_isolation_modes:
        result.add_error(f"{file_path.name}: isolationの値が不正です: {isolation_str}（worktree）")

    # backgroundの値チェック（v2.1.49以降）
    background = frontmatter.get("background")
    if background is not None and not isinstance(background, bool):
        result.add_error(
            f"{file_path.name}: backgroundはブール値（true/false）が必要です: {background}"
        )

    # toolsの確認（リスト形式検証）
    tools = frontmatter.get("tools")
    if tools is not None:
        if not isinstance(tools, (str, list)):
            result.add_error(f"{file_path.name}: toolsは文字列またはリストが必要です")
        elif isinstance(tools, list):
            for t in tools:
                if not isinstance(t, str) or not t:
                    result.add_error(f"{file_path.name}: toolsの各要素は空でない文字列が必要です")
                    break
        # Task(agent_type) 構文の検証
        tools_str = (
            tools if isinstance(tools, str) else " ".join(tools) if isinstance(tools, list) else ""
        )
        if "Task(" in tools_str and not _validate_task_syntax(tools_str):
            result.add_warning(
                f"{file_path.name}: Task()構文の形式を確認してください（例: Task(agent-name)）"
            )

    # disallowedToolsの確認（リスト形式検証）
    disallowed_tools = frontmatter.get("disallowedTools")
    if disallowed_tools is not None:
        if not isinstance(disallowed_tools, (str, list)):
            result.add_error(f"{file_path.name}: disallowedToolsは文字列またはリストが必要です")
        elif isinstance(disallowed_tools, list):
            for t in disallowed_tools:
                if not isinstance(t, str) or not t:
                    result.add_error(
                        f"{file_path.name}: disallowedToolsの各要素は空でない文字列が必要です"
                    )
                    break

    # skillsの確認（リスト形式検証）
    skills = frontmatter.get("skills")
    if skills is not None:
        if not isinstance(skills, (str, list)):
            result.add_error(f"{file_path.name}: skillsは文字列またはリストが必要です")
        elif isinstance(skills, list):
            for s in skills:
                if not isinstance(s, str) or not s:
                    result.add_error(f"{file_path.name}: skillsの各要素は空でない文字列が必要です")
                    break

    # 本文（システムプロンプト）の確認
    if not body.strip():
        result.add_warning(f"{file_path.name}: システムプロンプト（本文）が空です")

    return result
