"""
スキルのバリデーター
"""

import re
from pathlib import Path

from .base import (
    WARNING_BROAD_BASH_WILDCARD,
    ValidationResult,
    get_disabled_warnings,
    parse_frontmatter,
)


def validate_skill(file_path: Path, content: str) -> ValidationResult:
    """スキルを検証する"""
    result = ValidationResult()
    frontmatter, body, yaml_warnings = parse_frontmatter(content)
    disabled_warnings = get_disabled_warnings(content)

    # YAML警告を追加
    for w in yaml_warnings:
        result.add_warning(f"{file_path.name}: {w}")

    # nameの確認
    name = frontmatter.get("name", "")
    name_str = str(name) if name else ""
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
    description_str = str(description) if description else ""
    if not description_str:
        result.add_error(f"{file_path.name}: descriptionが必須です")
    elif len(description_str) > 1024:
        result.add_error(
            f"{file_path.name}: descriptionは1024文字以内にしてください: {len(description_str)}文字"
        )

    # contextの確認（forkのみサポート、省略時はメインコンテキスト）
    context = frontmatter.get("context")
    if context is not None:
        context_str = str(context) if context else ""
        if context_str and context_str != "fork":
            result.add_error(
                f"{file_path.name}: contextの値が不正です: {context_str}（forkのみ有効）"
            )

    # user-invocableの確認（boolean型）
    user_invocable = frontmatter.get("user-invocable")
    if user_invocable is not None and not isinstance(user_invocable, bool):
        result.add_error(f"{file_path.name}: user-invocableはブール値が必要です")

    # agentの確認（空でない文字列）
    agent = frontmatter.get("agent")
    if agent is not None:
        agent_str = str(agent) if agent else ""
        if not agent_str:
            result.add_error(f"{file_path.name}: agentは空でない文字列が必要です")

    # allowed-toolsの確認（リスト形式対応）
    allowed_tools = frontmatter.get("allowed-tools")
    if allowed_tools is not None:
        # リスト形式または文字列形式をチェック
        tools_str = ""
        if isinstance(allowed_tools, list):
            tools_str = ", ".join(str(t) for t in allowed_tools)
        else:
            tools_str = str(allowed_tools)

        # Bash(*)のような広範なワイルドカードを警告
        if "Bash(*)" in tools_str:
            if WARNING_BROAD_BASH_WILDCARD not in disabled_warnings:
                result.add_warning(
                    f"{file_path.name}: allowed-toolsにBash(*)が指定。"
                    "v2.1.20以降Bash(*)はBashと同等に扱われますが、具体的なパターンを推奨"
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
