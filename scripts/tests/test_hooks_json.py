"""
hooks_json.py のテスト
"""

import json
from pathlib import Path

from scripts.validators.hooks_json import validate_hooks_json


class TestValidateHooksJson:
    """hooks.json検証のテスト"""

    def test_valid_hooks(self):
        content = json.dumps(
            {
                "hooks": {
                    "PostToolUse": [
                        {
                            "matcher": "Edit|Write",
                            "hooks": [{"type": "command", "command": "echo test"}],
                        }
                    ]
                }
            }
        )
        result = validate_hooks_json(Path("hooks.json"), content)
        assert not result.has_errors()

    def test_invalid_json(self):
        content = "{ invalid json }"
        result = validate_hooks_json(Path("hooks.json"), content)
        assert result.has_errors()
        assert any("JSON" in e for e in result.errors)

    def test_empty_hooks(self):
        content = json.dumps({"hooks": {}})
        result = validate_hooks_json(Path("hooks.json"), content)
        assert not result.has_errors()
        assert any("空" in w for w in result.warnings)

    def test_invalid_event_name(self):
        content = json.dumps({"hooks": {"InvalidEvent": [{"matcher": "*", "hooks": []}]}})
        result = validate_hooks_json(Path("hooks.json"), content)
        assert result.has_errors()
        assert any("無効なイベント名" in e for e in result.errors)

    def test_all_valid_events(self):
        """すべての有効なイベント名をテスト"""
        valid_events = [
            "PreToolUse",
            "PostToolUse",
            "PermissionRequest",
            "UserPromptSubmit",
            "Notification",
            "Stop",
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
        for event in valid_events:
            content = json.dumps(
                {"hooks": {event: [{"hooks": [{"type": "command", "command": "test"}]}]}}
            )
            result = validate_hooks_json(Path("hooks.json"), content)
            assert not result.has_errors(), f"Event {event} should be valid"

    def test_invalid_hook_type(self):
        content = json.dumps(
            {"hooks": {"PostToolUse": [{"matcher": "*", "hooks": [{"type": "invalid"}]}]}}
        )
        result = validate_hooks_json(Path("hooks.json"), content)
        assert result.has_errors()
        assert any("type" in e for e in result.errors)

    def test_missing_command_field(self):
        content = json.dumps(
            {"hooks": {"PostToolUse": [{"matcher": "*", "hooks": [{"type": "command"}]}]}}
        )
        result = validate_hooks_json(Path("hooks.json"), content)
        assert result.has_errors()
        assert any("command" in e for e in result.errors)

    def test_missing_prompt_field(self):
        content = json.dumps(
            {"hooks": {"PostToolUse": [{"matcher": "*", "hooks": [{"type": "prompt"}]}]}}
        )
        result = validate_hooks_json(Path("hooks.json"), content)
        assert result.has_errors()
        assert any("prompt" in e for e in result.errors)

    def test_valid_agent_type(self):
        """agentタイプのフックが有効であることをテスト"""
        content = json.dumps(
            {
                "hooks": {
                    "PostToolUse": [
                        {"matcher": "*", "hooks": [{"type": "agent", "agent": "code-reviewer"}]}
                    ]
                }
            }
        )
        result = validate_hooks_json(Path("hooks.json"), content)
        assert not result.has_errors()

    def test_missing_agent_field(self):
        """agentタイプでagentフィールドが無い場合のテスト"""
        content = json.dumps(
            {"hooks": {"PostToolUse": [{"matcher": "*", "hooks": [{"type": "agent"}]}]}}
        )
        result = validate_hooks_json(Path("hooks.json"), content)
        assert result.has_errors()
        assert any("agent" in e for e in result.errors)

    def test_missing_matcher_warning(self):
        content = json.dumps(
            {"hooks": {"PostToolUse": [{"hooks": [{"type": "command", "command": "test"}]}]}}
        )
        result = validate_hooks_json(Path("hooks.json"), content)
        assert not result.has_errors()
        assert any("matcher" in w for w in result.warnings)

    def test_valid_setup_hook(self):
        """Setupフックが有効であることをテスト"""
        content = json.dumps(
            {
                "hooks": {
                    "Setup": [
                        {
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "${CLAUDE_PLUGIN_ROOT}/scripts/setup.sh",
                                    "timeout": 60,
                                }
                            ]
                        }
                    ]
                }
            }
        )
        result = validate_hooks_json(Path("hooks.json"), content)
        assert not result.has_errors()

    def test_once_boolean_true(self):
        """once: trueが有効であることをテスト"""
        content = json.dumps(
            {
                "hooks": {
                    "PostToolUse": [
                        {
                            "matcher": "Edit",
                            "hooks": [{"type": "command", "command": "echo test", "once": True}],
                        }
                    ]
                }
            }
        )
        result = validate_hooks_json(Path("hooks.json"), content)
        assert not result.has_errors()

    def test_once_boolean_false(self):
        """once: falseが有効であることをテスト"""
        content = json.dumps(
            {
                "hooks": {
                    "PostToolUse": [
                        {
                            "matcher": "Edit",
                            "hooks": [{"type": "command", "command": "echo test", "once": False}],
                        }
                    ]
                }
            }
        )
        result = validate_hooks_json(Path("hooks.json"), content)
        assert not result.has_errors()

    def test_valid_config_change_hook(self):
        """ConfigChangeフックが有効であることをテスト"""
        content = json.dumps(
            {
                "hooks": {
                    "ConfigChange": [
                        {
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "${CLAUDE_PLUGIN_ROOT}/scripts/audit-config.sh",
                                    "timeout": 30,
                                }
                            ]
                        }
                    ]
                }
            }
        )
        result = validate_hooks_json(Path("hooks.json"), content)
        assert not result.has_errors()

    def test_once_invalid_type(self):
        """onceがブール値でない場合エラー"""
        content = json.dumps(
            {
                "hooks": {
                    "PostToolUse": [
                        {
                            "matcher": "Edit",
                            "hooks": [{"type": "command", "command": "echo test", "once": "true"}],
                        }
                    ]
                }
            }
        )
        result = validate_hooks_json(Path("hooks.json"), content)
        assert result.has_errors()
        assert any("once" in e for e in result.errors)

    def test_valid_worktree_create_hook(self):
        """WorktreeCreateフックが有効であることをテスト（v2.1.50以降）"""
        content = json.dumps(
            {
                "hooks": {
                    "WorktreeCreate": [
                        {
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "${CLAUDE_PLUGIN_ROOT}/scripts/worktree-setup.sh",
                                    "timeout": 60,
                                }
                            ]
                        }
                    ]
                }
            }
        )
        result = validate_hooks_json(Path("hooks.json"), content)
        assert not result.has_errors()

    def test_valid_worktree_remove_hook(self):
        """WorktreeRemoveフックが有効であることをテスト（v2.1.50以降）"""
        content = json.dumps(
            {
                "hooks": {
                    "WorktreeRemove": [
                        {
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "${CLAUDE_PLUGIN_ROOT}/scripts/worktree-cleanup.sh",
                                    "timeout": 30,
                                }
                            ]
                        }
                    ]
                }
            }
        )
        result = validate_hooks_json(Path("hooks.json"), content)
        assert not result.has_errors()
