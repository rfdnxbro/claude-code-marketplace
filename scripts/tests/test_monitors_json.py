"""
monitors_json.py のテスト
"""

import json
from pathlib import Path

from scripts.validators.monitors_json import validate_monitors_json


class TestValidateMonitorsJson:
    """monitors.json 検証のテスト"""

    def test_valid_minimal(self):
        """最小限の有効な設定（必須フィールドのみ）"""
        content = json.dumps(
            [
                {
                    "name": "deploy-status",
                    "command": "./scripts/poll.sh",
                    "description": "Deployment status",
                }
            ]
        )
        result = validate_monitors_json(Path("monitors.json"), content)
        assert not result.has_errors()
        assert not result.warnings

    def test_valid_full(self):
        """すべてのフィールドを含む有効な設定"""
        content = json.dumps(
            [
                {
                    "name": "error-log",
                    "command": "tail -F ./logs/error.log",
                    "description": "Application error log",
                    "when": "always",
                },
                {
                    "name": "debug-monitor",
                    "command": "${CLAUDE_PLUGIN_ROOT}/scripts/debug.sh",
                    "description": "Debug monitor",
                    "when": "on-skill-invoke:debug",
                },
            ]
        )
        result = validate_monitors_json(Path("monitors.json"), content)
        assert not result.has_errors()
        assert not result.warnings

    def test_valid_on_skill_invoke_kebab_case(self):
        """on-skill-invoke のスキル名が kebab-case で有効"""
        content = json.dumps(
            [
                {
                    "name": "mon",
                    "command": "echo hi",
                    "description": "desc",
                    "when": "on-skill-invoke:my-custom-skill",
                }
            ]
        )
        result = validate_monitors_json(Path("monitors.json"), content)
        assert not result.has_errors()

    def test_invalid_json(self):
        """不正なJSON"""
        content = "{ invalid json }"
        result = validate_monitors_json(Path("monitors.json"), content)
        assert result.has_errors()
        assert any("JSON" in e for e in result.errors)

    def test_root_not_array(self):
        """ルートが配列でない場合はエラー"""
        content = json.dumps({"name": "foo"})
        result = validate_monitors_json(Path("monitors.json"), content)
        assert result.has_errors()
        assert any("配列" in e for e in result.errors)

    def test_empty_array(self):
        """空配列は警告のみ"""
        content = json.dumps([])
        result = validate_monitors_json(Path("monitors.json"), content)
        assert not result.has_errors()
        assert any("空" in w for w in result.warnings)

    def test_entry_not_object(self):
        """エントリがオブジェクトでない場合はエラー"""
        content = json.dumps(["not-an-object"])
        result = validate_monitors_json(Path("monitors.json"), content)
        assert result.has_errors()
        assert any("オブジェクト" in e for e in result.errors)

    def test_missing_name(self):
        """name欠落はエラー"""
        content = json.dumps([{"command": "echo hi", "description": "desc"}])
        result = validate_monitors_json(Path("monitors.json"), content)
        assert result.has_errors()
        assert any("name" in e for e in result.errors)

    def test_missing_command(self):
        """command欠落はエラー"""
        content = json.dumps([{"name": "mon", "description": "desc"}])
        result = validate_monitors_json(Path("monitors.json"), content)
        assert result.has_errors()
        assert any("command" in e for e in result.errors)

    def test_missing_description(self):
        """description欠落はエラー"""
        content = json.dumps([{"name": "mon", "command": "echo hi"}])
        result = validate_monitors_json(Path("monitors.json"), content)
        assert result.has_errors()
        assert any("description" in e for e in result.errors)

    def test_empty_name(self):
        """name が空文字列はエラー"""
        content = json.dumps([{"name": "", "command": "echo hi", "description": "desc"}])
        result = validate_monitors_json(Path("monitors.json"), content)
        assert result.has_errors()
        assert any("name" in e for e in result.errors)

    def test_non_string_command(self):
        """command が文字列でない場合はエラー"""
        content = json.dumps([{"name": "mon", "command": ["echo", "hi"], "description": "desc"}])
        result = validate_monitors_json(Path("monitors.json"), content)
        assert result.has_errors()
        assert any("command" in e for e in result.errors)

    def test_duplicate_names(self):
        """name重複はエラー"""
        content = json.dumps(
            [
                {"name": "dup", "command": "echo a", "description": "a"},
                {"name": "dup", "command": "echo b", "description": "b"},
            ]
        )
        result = validate_monitors_json(Path("monitors.json"), content)
        assert result.has_errors()
        assert any("重複" in e for e in result.errors)

    def test_invalid_when(self):
        """when の値が不正な場合は警告"""
        content = json.dumps(
            [
                {
                    "name": "mon",
                    "command": "echo hi",
                    "description": "desc",
                    "when": "never",
                }
            ]
        )
        result = validate_monitors_json(Path("monitors.json"), content)
        assert not result.has_errors()
        assert any("when" in w for w in result.warnings)

    def test_when_not_string(self):
        """when が文字列でない場合はエラー"""
        content = json.dumps(
            [
                {
                    "name": "mon",
                    "command": "echo hi",
                    "description": "desc",
                    "when": True,
                }
            ]
        )
        result = validate_monitors_json(Path("monitors.json"), content)
        assert result.has_errors()
        assert any("when" in e for e in result.errors)

    def test_unknown_field_warning(self):
        """未知のフィールドは警告"""
        content = json.dumps(
            [
                {
                    "name": "mon",
                    "command": "echo hi",
                    "description": "desc",
                    "unknownField": "value",
                }
            ]
        )
        result = validate_monitors_json(Path("monitors.json"), content)
        assert not result.has_errors()
        assert any("unknownField" in w for w in result.warnings)

    def test_on_skill_invoke_without_skill_name(self):
        """on-skill-invoke: の後にスキル名がない場合は警告（エラーではない）"""
        content = json.dumps(
            [
                {
                    "name": "mon",
                    "command": "echo hi",
                    "description": "desc",
                    "when": "on-skill-invoke:",
                }
            ]
        )
        result = validate_monitors_json(Path("monitors.json"), content)
        assert not result.has_errors()
        assert any("when" in w for w in result.warnings)

    def test_when_empty_string(self):
        """when が空文字列の場合はエラー（必須フィールドと同じ一貫性）"""
        content = json.dumps(
            [
                {
                    "name": "mon",
                    "command": "echo hi",
                    "description": "desc",
                    "when": "",
                }
            ]
        )
        result = validate_monitors_json(Path("monitors.json"), content)
        assert result.has_errors()
        assert any("when" in e and "空文字列" in e for e in result.errors)
