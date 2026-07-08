"""
hooks.json のバリデーター
"""

import re
from pathlib import Path

from .base import ValidationResult, parse_json_safe

# httpタイプのheaders値内の環境変数プレースホルダー（${VAR_NAME}形式）を抽出する正規表現
ENV_VAR_PLACEHOLDER_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")

# イベントごとに使用できないhookタイプと、使用可能なタイプの案内文言
DISALLOWED_HOOK_TYPES_BY_EVENT = {
    "SessionStart": ({"prompt", "agent", "http"}, "command/mcp_toolタイプ"),
    "Setup": ({"prompt", "agent", "http"}, "command/mcp_toolタイプ"),
    "SubagentStart": ({"prompt", "agent"}, "command/http/mcp_toolタイプ"),
}


def _validate_http_allowed_env_vars(h: dict, file_path: Path, result: ValidationResult) -> None:
    """httpタイプのheadersで使用される環境変数プレースホルダーが
    allowedEnvVarsにホワイトリスト登録されているかを検証する"""
    headers = h.get("headers")
    if not isinstance(headers, dict):
        return

    used_env_vars: set[str] = set()
    for header_value in headers.values():
        if isinstance(header_value, str):
            used_env_vars.update(ENV_VAR_PLACEHOLDER_PATTERN.findall(header_value))

    if not used_env_vars:
        return

    allowed_env_vars = h.get("allowedEnvVars")
    if allowed_env_vars is not None and not isinstance(allowed_env_vars, list):
        result.add_error(f"{file_path.name}: httpタイプのallowedEnvVarsは配列が必要です")
        return

    missing_env_vars = sorted(used_env_vars - set(allowed_env_vars or []))
    if missing_env_vars:
        missing_str = ", ".join(missing_env_vars)
        result.add_error(
            f"{file_path.name}: httpタイプのheadersで環境変数 "
            f"{missing_str} を使用していますが"
            f"allowedEnvVarsに含まれていません"
        )


def validate_hooks_json(file_path: Path, content: str) -> ValidationResult:
    """hooks.jsonを検証する"""
    result = ValidationResult()

    data = parse_json_safe(content, file_path, result)
    if data is None:
        return result

    hooks = data.get("hooks", {})
    if not isinstance(hooks, dict):
        result.add_error(f"{file_path.name}: hooksはオブジェクトが必要です")
        return result
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
        "MessageDisplay",
    ]

    for event_name, event_hooks in hooks.items():
        if event_name not in valid_events:
            result.add_error(f"{file_path.name}: 無効なイベント名: {event_name}")
            continue

        if not isinstance(event_hooks, list):
            result.add_error(f"{file_path.name}: {event_name}のフック設定は配列が必要です")
            continue

        for hook_config in event_hooks:
            if not isinstance(hook_config, dict):
                result.add_error(
                    f"{file_path.name}: {event_name}のフック設定はオブジェクトが必要です"
                )
                continue

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
            if not isinstance(inner_hooks, list):
                result.add_error(f"{file_path.name}: {event_name}のhooksは配列が必要です")
                continue

            for h in inner_hooks:
                if not isinstance(h, dict):
                    result.add_error(
                        f"{file_path.name}: {event_name}のhooks要素はオブジェクトが必要です"
                    )
                    continue

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

                # イベントごとに使用できないhookタイプの確認
                disallowed = DISALLOWED_HOOK_TYPES_BY_EVENT.get(event_name)
                if disallowed and hook_type in disallowed[0]:
                    allowed_types_str = disallowed[1]
                    result.add_error(
                        f"{file_path.name}: {event_name}イベントには"
                        f"{hook_type}タイプは使用できません。"
                        f"{allowed_types_str}を使用してください"
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

                if hook_type == "http":
                    if not h.get("url"):
                        result.add_error(f"{file_path.name}: httpタイプにurlフィールドがありません")
                    _validate_http_allowed_env_vars(h, file_path, result)

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
