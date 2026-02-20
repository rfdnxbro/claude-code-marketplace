"""
plugin_json.py のテスト
"""

import json
from pathlib import Path

from scripts.validators.plugin_json import validate_plugin_json


class TestValidatePluginJson:
    """plugin.json検証のテスト"""

    def test_valid_plugin(self):
        content = json.dumps(
            {
                "name": "my-plugin",
                "version": "1.0.0",
                "description": "テストプラグイン",
                "commands": "./commands/",
            }
        )
        result = validate_plugin_json(Path("plugin.json"), content)
        assert not result.has_errors()

    def test_minimal_valid(self):
        """最小限の有効な設定"""
        content = json.dumps({"name": "my-plugin"})
        result = validate_plugin_json(Path("plugin.json"), content)
        assert not result.has_errors()

    def test_invalid_json(self):
        content = "{ invalid json }"
        result = validate_plugin_json(Path("plugin.json"), content)
        assert result.has_errors()
        assert any("JSON" in e for e in result.errors)

    def test_missing_name(self):
        content = json.dumps({"version": "1.0.0"})
        result = validate_plugin_json(Path("plugin.json"), content)
        assert result.has_errors()
        assert any("name" in e for e in result.errors)

    def test_invalid_name_uppercase(self):
        content = json.dumps({"name": "MyPlugin"})
        result = validate_plugin_json(Path("plugin.json"), content)
        assert result.has_errors()
        assert any("kebab-case" in e for e in result.errors)

    def test_invalid_name_underscore(self):
        content = json.dumps({"name": "my_plugin"})
        result = validate_plugin_json(Path("plugin.json"), content)
        assert result.has_errors()
        assert any("kebab-case" in e for e in result.errors)

    def test_invalid_name_space(self):
        content = json.dumps({"name": "My Plugin"})
        result = validate_plugin_json(Path("plugin.json"), content)
        assert result.has_errors()
        assert any("スペース" in e for e in result.errors)

    def test_invalid_version_format(self):
        content = json.dumps({"name": "my-plugin", "version": "v1"})
        result = validate_plugin_json(Path("plugin.json"), content)
        assert any("セマンティックバージョニング" in w for w in result.warnings)

    def test_valid_version_formats(self):
        """有効なバージョン形式"""
        for version in ["1.0.0", "0.1.0", "2.3.4", "1.0.0-alpha", "1.0.0-beta.1"]:
            content = json.dumps({"name": "my-plugin", "version": version})
            result = validate_plugin_json(Path("plugin.json"), content)
            assert not any("セマンティックバージョニング" in w for w in result.warnings), (
                f"Version {version} should be valid"
            )

    def test_path_without_prefix(self):
        content = json.dumps({"name": "my-plugin", "commands": "commands/"})
        result = validate_plugin_json(Path("plugin.json"), content)
        assert any("./" in w for w in result.warnings)

    def test_path_with_prefix(self):
        content = json.dumps(
            {
                "name": "my-plugin",
                "commands": "./commands/",
                "agents": "./agents/",
                "skills": "./skills/",
            }
        )
        result = validate_plugin_json(Path("plugin.json"), content)
        assert not any("./" in w for w in result.warnings)

    def test_all_path_fields(self):
        """すべてのパスフィールドをテスト"""
        path_fields = [
            "commands",
            "agents",
            "skills",
            "hooks",
            "mcpServers",
            "lspServers",
            "outputStyles",
            "settings",
        ]
        for field in path_fields:
            content = json.dumps({"name": "my-plugin", field: "some/path"})
            result = validate_plugin_json(Path("plugin.json"), content)
            assert any("./" in w for w in result.warnings), (
                f"Field {field} should trigger path warning"
            )

    def test_settings_valid_path(self):
        """settingsのパスが./で始まる場合に警告が出ないことを確認"""
        content = json.dumps({"name": "my-plugin", "settings": "./settings.json"})
        result = validate_plugin_json(Path("plugin.json"), content)
        assert not any("./" in w and "settings" in w for w in result.warnings)

    def test_settings_path_without_prefix(self):
        """settingsのパスが./で始まらない場合に警告が出ることを確認"""
        content = json.dumps({"name": "my-plugin", "settings": "settings.json"})
        result = validate_plugin_json(Path("plugin.json"), content)
        assert any("settings" in w for w in result.warnings)
