"""
hooks.json のバリデーター
"""

from pathlib import Path

from .base import ValidationResult, parse_json_safe


def validate_hooks_json(file_path: Path, content: str) -> ValidationResult:
    """hooks.jsonを検証する"""
    result = ValidationResult()

    data = parse_json_safe(content, file_path, result)
    if data is None:
        return result

    hooks = data.get("hooks", {})
    if not hooks:
        result.add_warning(f"{file_path.name}: hooksが空です")
        return result

    # 有効なイベント名
    valid_events = [
        "PreToolUse",
        "PostToolUse",
        "PostToolUseFailure",
        "PermissionRequest",
        "UserPromptSubmit",
        "Notification",
        "Stop",
        "SubagentStart",
        "SubagentStop",
        "PreCompact",
        "SessionStart",
        "SessionEnd",
        "Setup",
        "TeammateIdle",
        "TaskCompleted",
        "TaskCreated",
        "ConfigChange",
        "CwdChanged",
        "FileChanged",
        "WorktreeCreate",
        "WorktreeRemove",
        "InstructionsLoaded",
        "PostCompact",
        "Elicitation",
        "ElicitationResult",
        "StopFailure",
        "PermissionDenied",
    ]

    for event_name, event_hooks in hooks.items():
        if event_name not in valid_events:
            result.add_error(f"{file_path.name}: 無効なイベント名: {event_name}")
            continue

        for hook_config in event_hooks:
            # matcherの確認（マッチャー対応イベントのみ）
            events_with_matcher = [
                "PreToolUse",
                "PostToolUse",
                "PostToolUseFailure",
                "PermissionRequest",
                "PermissionDenied",
                "Notification",
                "SubagentStart",
                "SubagentStop",
                "PreCompact",
                "PostCompact",
                "SessionStart",
                "ConfigChange",
                "CwdChanged",
                "FileChanged",
                "Elicitation",
                "ElicitationResult",
            ]
            if event_name in events_with_matcher:
                matcher = hook_config.get("matcher")
                if not matcher:
                    result.add_warning(
                        f"{file_path.name}: {event_name}のmatcherが未設定（全ツールにマッチ）"
                    )

            # ifフィールドの確認（v2.1.85以降）
            if_field = hook_config.get("if")
            if if_field is not None and not isinstance(if_field, str):
                result.add_error(
                    f"{file_path.name}: ifフィールドは文字列が必要です（パーミッションルール構文）"
                )

            # continueOnBlockフィールドの確認（v2.1.139以降、PostToolUse向け）
            continue_on_block = hook_config.get("continueOnBlock")
            if continue_on_block is not None and not isinstance(continue_on_block, bool):
                result.add_error(f"{file_path.name}: continueOnBlockはブール値が必要です")

            # hooksの確認
            inner_hooks = hook_config.get("hooks", [])
            for h in inner_hooks:
                hook_type = h.get("type")
                valid_types = ["command", "prompt", "agent", "http", "mcp_tool"]
                if hook_type not in valid_types:
                    types_str = "/".join(valid_types)
                    result.add_error(
                        f"{file_path.name}: 無効なhook type: {hook_type}（{types_str}）"
                    )

                # PostCompactはcommandタイプのみ対応
                if (
                    event_name == "PostCompact"
                    and hook_type != "command"
                    and hook_type in valid_types
                ):
                    result.add_error(
                        f"{file_path.name}: PostCompactイベントはcommandタイプのみ対応しています"
                    )

                # SessionStart/Setup/SubagentStartはprompt/agentタイプ不可（v2.1.142）
                command_only_prompt_agent_events = ["SessionStart", "Setup", "SubagentStart"]
                if event_name in command_only_prompt_agent_events and hook_type in [
                    "prompt",
                    "agent",
                ]:
                    result.add_error(
                        f"{file_path.name}: {event_name}イベントには"
                        f"prompt/agentタイプは使用できません。commandタイプを使用してください"
                    )

                if hook_type == "command" and not h.get("command"):
                    result.add_error(
                        f"{file_path.name}: commandタイプにcommandフィールドがありません"
                    )

                # argsフィールドの確認（commandタイプ、v2.1.139以降）
                if hook_type == "command":
                    args_field = h.get("args")
                    if args_field is not None:
                        if not isinstance(args_field, list) or not all(
                            isinstance(a, str) for a in args_field
                        ):
                            result.add_error(
                                f"{file_path.name}: commandタイプのargsは文字列の配列が必要です"
                            )

                if hook_type == "prompt" and not h.get("prompt"):
                    result.add_error(
                        f"{file_path.name}: promptタイプにpromptフィールドがありません"
                    )

                if hook_type == "agent":
                    if not h.get("agent"):
                        result.add_error(
                            f"{file_path.name}: agentタイプにagentフィールドがありません"
                        )
                    if not h.get("prompt"):
                        result.add_error(
                            f"{file_path.name}: agentタイプにpromptフィールドがありません"
                        )

                if hook_type == "http" and not h.get("url"):
                    result.add_error(f"{file_path.name}: httpタイプにurlフィールドがありません")

                if hook_type == "mcp_tool":
                    if not h.get("server"):
                        result.add_error(
                            f"{file_path.name}: mcp_toolタイプにserverフィールドがありません"
                        )
                    if not h.get("tool"):
                        result.add_error(
                            f"{file_path.name}: mcp_toolタイプにtoolフィールドがありません"
                        )

                # onceの確認（boolean型）
                once = h.get("once")
                if once is not None and not isinstance(once, bool):
                    result.add_error(f"{file_path.name}: onceはブール値が必要です")

    return result
