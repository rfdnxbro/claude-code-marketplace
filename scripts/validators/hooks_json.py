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
        "ConfigChange",
        "WorktreeCreate",
        "WorktreeRemove",
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
                "Notification",
                "SubagentStart",
                "SubagentStop",
                "PreCompact",
                "SessionStart",
                "ConfigChange",
            ]
            if event_name in events_with_matcher:
                matcher = hook_config.get("matcher")
                if not matcher:
                    result.add_warning(
                        f"{file_path.name}: {event_name}のmatcherが未設定（全ツールにマッチ）"
                    )

            # hooksの確認
            inner_hooks = hook_config.get("hooks", [])
            for h in inner_hooks:
                hook_type = h.get("type")
                valid_types = ["command", "prompt", "agent", "http"]
                if hook_type not in valid_types:
                    types_str = "/".join(valid_types)
                    result.add_error(
                        f"{file_path.name}: 無効なhook type: {hook_type}（{types_str}）"
                    )

                if hook_type == "command" and not h.get("command"):
                    result.add_error(
                        f"{file_path.name}: commandタイプにcommandフィールドがありません"
                    )

                if hook_type == "prompt" and not h.get("prompt"):
                    result.add_error(
                        f"{file_path.name}: promptタイプにpromptフィールドがありません"
                    )

                if hook_type == "agent" and not h.get("agent"):
                    result.add_error(f"{file_path.name}: agentタイプにagentフィールドがありません")

                if hook_type == "http" and not h.get("url"):
                    result.add_error(f"{file_path.name}: httpタイプにurlフィールドがありません")

                # onceの確認（boolean型）
                once = h.get("once")
                if once is not None and not isinstance(once, bool):
                    result.add_error(f"{file_path.name}: onceはブール値が必要です")

    return result
