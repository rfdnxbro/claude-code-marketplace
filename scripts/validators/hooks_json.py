"""
hooks.json のバリデーター
"""

import json
from pathlib import Path

from .base import ValidationResult


def validate_hooks_json(file_path: Path, content: str) -> ValidationResult:
    """hooks.jsonを検証する"""
    result = ValidationResult()

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        result.add_error(f"{file_path.name}: JSONパースエラー: {e}")
        return result

    hooks = data.get("hooks", {})
    if not hooks:
        result.add_warning(f"{file_path.name}: hooksが空です")
        return result

    # 有効なイベント名
    valid_events = [
        "PreToolUse", "PostToolUse", "PermissionRequest", "UserPromptSubmit",
        "Notification", "Stop", "SubagentStop", "PreCompact", "SessionStart", "SessionEnd"
    ]

    for event_name, event_hooks in hooks.items():
        if event_name not in valid_events:
            result.add_error(f"{file_path.name}: 無効なイベント名: {event_name}")
            continue

        for hook_config in event_hooks:
            # matcherの確認（マッチャー対応イベントのみ）
            events_with_matcher = ["PreToolUse", "PostToolUse", "PermissionRequest", "Notification", "PreCompact", "SessionStart"]
            if event_name in events_with_matcher:
                matcher = hook_config.get("matcher")
                if not matcher:
                    result.add_warning(f"{file_path.name}: {event_name}のmatcherが未設定（全ツールにマッチ）")

            # hooksの確認
            inner_hooks = hook_config.get("hooks", [])
            for h in inner_hooks:
                hook_type = h.get("type")
                if hook_type not in ["command", "prompt"]:
                    result.add_error(f"{file_path.name}: 無効なhook type: {hook_type}（command, promptのいずれか）")

                if hook_type == "command" and not h.get("command"):
                    result.add_error(f"{file_path.name}: commandタイプにcommandフィールドがありません")

                if hook_type == "prompt" and not h.get("prompt"):
                    result.add_error(f"{file_path.name}: promptタイプにpromptフィールドがありません")

    return result
