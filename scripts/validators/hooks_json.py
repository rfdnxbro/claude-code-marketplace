"""
hooks.json のバリデーター
"""

from pathlib import Path

from .base import ValidationResult, parse_json_safe

# イベントメタデータ: supports_matcher=True のイベントはmatcherフィールドを使用可能
_EVENTS: dict[str, dict[str, bool]] = {
    "PreToolUse": {"supports_matcher": True},
    "PostToolUse": {"supports_matcher": True},
    "PostToolUseFailure": {"supports_matcher": True},
    "PermissionRequest": {"supports_matcher": True},
    "UserPromptSubmit": {"supports_matcher": False},
    "Notification": {"supports_matcher": True},
    "Stop": {"supports_matcher": False},
    "SubagentStart": {"supports_matcher": True},
    "SubagentStop": {"supports_matcher": True},
    "PreCompact": {"supports_matcher": True},
    "SessionStart": {"supports_matcher": True},
    "SessionEnd": {"supports_matcher": False},
    "Setup": {"supports_matcher": False},
    "TeammateIdle": {"supports_matcher": False},
    "TaskCompleted": {"supports_matcher": False},
    "TaskCreated": {"supports_matcher": False},
    "ConfigChange": {"supports_matcher": True},
    "CwdChanged": {"supports_matcher": True},
    "FileChanged": {"supports_matcher": True},
    "WorktreeCreate": {"supports_matcher": False},
    "WorktreeRemove": {"supports_matcher": False},
    "InstructionsLoaded": {"supports_matcher": False},
    "PostCompact": {"supports_matcher": True},
    "Elicitation": {"supports_matcher": True},
    "ElicitationResult": {"supports_matcher": True},
    "StopFailure": {"supports_matcher": False},
}

VALID_EVENTS = set(_EVENTS)
EVENTS_WITH_MATCHER = {name for name, meta in _EVENTS.items() if meta["supports_matcher"]}
VALID_HOOK_TYPES = {"command", "prompt", "agent", "http"}
_VALID_HOOK_TYPES_STR = "/".join(sorted(VALID_HOOK_TYPES))


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

    for event_name, event_hooks in hooks.items():
        if event_name not in VALID_EVENTS:
            result.add_error(f"{file_path.name}: 無効なイベント名: {event_name}")
            continue

        for hook_config in event_hooks:
            if event_name in EVENTS_WITH_MATCHER:
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

            inner_hooks = hook_config.get("hooks", [])
            for h in inner_hooks:
                hook_type = h.get("type")
                if hook_type not in VALID_HOOK_TYPES:
                    result.add_error(
                        f"{file_path.name}: 無効なhook type: {hook_type}（{_VALID_HOOK_TYPES_STR}）"
                    )

                if (
                    event_name == "PostCompact"
                    and hook_type != "command"
                    and hook_type in VALID_HOOK_TYPES
                ):
                    result.add_error(
                        f"{file_path.name}: PostCompactイベントはcommandタイプのみ対応しています"
                    )

                if hook_type == "command" and not h.get("command"):
                    result.add_error(
                        f"{file_path.name}: commandタイプにcommandフィールドがありません"
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

                # onceの確認（boolean型）
                once = h.get("once")
                if once is not None and not isinstance(once, bool):
                    result.add_error(f"{file_path.name}: onceはブール値が必要です")

    return result
