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

    def test_path_with_prefix_custom(self):
        """カスタムパスに./プレフィックスがある場合は警告なし"""
        content = json.dumps(
            {
                "name": "my-plugin",
                "commands": "./src/commands/",
                "agents": "./src/agents/",
                "skills": "./src/skills/",
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
            "monitors",
        ]
        for field in path_fields:
            content = json.dumps({"name": "my-plugin", field: "some/path"})
            result = validate_plugin_json(Path("plugin.json"), content)
            assert any("./" in w for w in result.warnings), (
                f"Field {field} should trigger path warning"
            )

    def test_redundant_default_path_hooks(self):
        """hooksにデフォルトパスを指定した場合に警告が出ることを確認"""
        content = json.dumps({"name": "my-plugin", "hooks": "./hooks/hooks.json"})
        result = validate_plugin_json(Path("plugin.json"), content)
        assert any("デフォルトパス" in w for w in result.warnings)

    def test_redundant_default_path_commands(self):
        """commandsにデフォルトパスを指定した場合に警告が出ることを確認"""
        content = json.dumps({"name": "my-plugin", "commands": "./commands/"})
        result = validate_plugin_json(Path("plugin.json"), content)
        assert any("デフォルトパス" in w for w in result.warnings)

    def test_custom_path_no_redundant_warning(self):
        """カスタムパスの場合はデフォルトパス警告が出ないことを確認"""
        content = json.dumps(
            {
                "name": "my-plugin",
                "hooks": "./custom/hooks.json",
                "mcpServers": "./config/mcp.json",
            }
        )
        result = validate_plugin_json(Path("plugin.json"), content)
        assert not any("デフォルトパス" in w for w in result.warnings)

    def test_redundant_default_path_lsp_servers(self):
        """lspServersにデフォルトパスを指定した場合に警告が出ることを確認"""
        content = json.dumps({"name": "my-plugin", "lspServers": "./.lsp.json"})
        result = validate_plugin_json(Path("plugin.json"), content)
        assert any("デフォルトパス" in w for w in result.warnings)

    def test_redundant_default_path_mcp_servers(self):
        """mcpServersにデフォルトパスを指定した場合に警告が出ることを確認"""
        content = json.dumps({"name": "my-plugin", "mcpServers": "./.mcp.json"})
        result = validate_plugin_json(Path("plugin.json"), content)
        assert any("デフォルトパス" in w for w in result.warnings)

    def test_redundant_default_path_monitors(self):
        """monitorsにデフォルトパスを指定した場合に警告が出ることを確認（v2.1.105以降）"""
        content = json.dumps({"name": "my-plugin", "monitors": "./monitors/monitors.json"})
        result = validate_plugin_json(Path("plugin.json"), content)
        assert any("デフォルトパス" in w for w in result.warnings)

    def test_deprecated_settings_field_warning(self):
        """settingsフィールド指定に対する非公式警告（plugin.jsonの公式スキーマに存在しない）"""
        content = json.dumps({"name": "my-plugin", "settings": "./config/settings.json"})
        result = validate_plugin_json(Path("plugin.json"), content)
        assert not result.has_errors()
        assert any("settings" in w and "公式フィールドではありません" in w for w in result.warnings)

    def test_deprecated_settings_field_with_empty_value(self):
        """settingsを空文字で指定した場合も警告（値に関わらずフィールド名で検出）"""
        content = json.dumps({"name": "my-plugin", "settings": ""})
        result = validate_plugin_json(Path("plugin.json"), content)
        assert any("settings" in w and "公式フィールドではありません" in w for w in result.warnings)

    def test_user_config_valid(self):
        """userConfigが有効なオブジェクトの場合はエラーなし（v2.1.83以降）"""
        content = json.dumps(
            {
                "name": "my-plugin",
                "userConfig": {
                    "apiKey": {"description": "API認証キー", "sensitive": True},
                    "serverUrl": {
                        "description": "サーバーURL",
                        "default": "https://api.example.com",
                    },
                },
            }
        )
        result = validate_plugin_json(Path("plugin.json"), content)
        assert not result.has_errors()

    def test_user_config_not_object(self):
        """userConfigがオブジェクト以外の場合エラー（v2.1.83以降）"""
        content = json.dumps({"name": "my-plugin", "userConfig": "invalid"})
        result = validate_plugin_json(Path("plugin.json"), content)
        assert result.has_errors()
        assert any("userConfig" in e for e in result.errors)

    def test_user_config_item_not_object(self):
        """userConfigの設定項目がオブジェクト以外の場合エラー（v2.1.83以降）"""
        content = json.dumps({"name": "my-plugin", "userConfig": {"apiKey": "invalid"}})
        result = validate_plugin_json(Path("plugin.json"), content)
        assert result.has_errors()
        assert any("userConfig.apiKey" in e for e in result.errors)

    def test_user_config_sensitive_non_boolean(self):
        """userConfigのsensitiveがブール値以外の場合エラー（v2.1.83以降）"""
        content = json.dumps(
            {
                "name": "my-plugin",
                "userConfig": {"apiKey": {"description": "API Key", "sensitive": "true"}},
            }
        )
        result = validate_plugin_json(Path("plugin.json"), content)
        assert result.has_errors()
        assert any("sensitive" in e for e in result.errors)

    def test_user_config_sensitive_valid_true(self):
        """userConfigのsensitive: trueが有効であることを確認（v2.1.83以降）"""
        content = json.dumps(
            {
                "name": "my-plugin",
                "userConfig": {"apiKey": {"description": "API Key", "sensitive": True}},
            }
        )
        result = validate_plugin_json(Path("plugin.json"), content)
        assert not result.has_errors()

    def test_user_config_sensitive_valid_false(self):
        """userConfigのsensitive: falseが有効であることを確認（v2.1.83以降）"""
        content = json.dumps(
            {
                "name": "my-plugin",
                "userConfig": {"serverUrl": {"description": "Server URL", "sensitive": False}},
            }
        )
        result = validate_plugin_json(Path("plugin.json"), content)
        assert not result.has_errors()

    def test_dependencies_valid(self):
        """dependenciesが有効な配列の場合はエラーなし（v2.1.110以降）"""
        content = json.dumps(
            {
                "name": "my-plugin",
                "dependencies": ["base-plugin", "shared-tools"],
            }
        )
        result = validate_plugin_json(Path("plugin.json"), content)
        assert not result.has_errors()

    def test_dependencies_empty_array(self):
        """dependenciesが空配列の場合はエラーなし（v2.1.110以降）"""
        content = json.dumps({"name": "my-plugin", "dependencies": []})
        result = validate_plugin_json(Path("plugin.json"), content)
        assert not result.has_errors()

    def test_dependencies_not_array(self):
        """dependenciesが配列以外の場合エラー（v2.1.110以降）"""
        content = json.dumps({"name": "my-plugin", "dependencies": "base-plugin"})
        result = validate_plugin_json(Path("plugin.json"), content)
        assert result.has_errors()
        assert any("dependencies" in e for e in result.errors)

    def test_dependencies_item_not_string(self):
        """dependenciesの要素が文字列以外の場合エラー（v2.1.110以降）"""
        content = json.dumps({"name": "my-plugin", "dependencies": [123]})
        result = validate_plugin_json(Path("plugin.json"), content)
        assert result.has_errors()
        assert any("dependencies" in e for e in result.errors)

    def test_dependencies_item_not_kebab_case(self):
        """dependenciesの要素がkebab-caseでない場合に警告（v2.1.110以降）"""
        content = json.dumps({"name": "my-plugin", "dependencies": ["MyPlugin"]})
        result = validate_plugin_json(Path("plugin.json"), content)
        dep_warnings = [w for w in result.warnings if "dependencies" in w]
        assert dep_warnings
        assert not any("name" in w for w in dep_warnings)

    def test_dependencies_item_empty_string(self):
        """dependenciesの要素が空文字列の場合エラー（v2.1.110以降）"""
        content = json.dumps({"name": "my-plugin", "dependencies": [""]})
        result = validate_plugin_json(Path("plugin.json"), content)
        assert result.has_errors()
        assert any("dependencies" in e for e in result.errors)
