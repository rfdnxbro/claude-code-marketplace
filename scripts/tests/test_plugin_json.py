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
            "themes",
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

    def test_unofficial_settings_field_warning(self):
        """settingsフィールド指定に対する非公式警告（plugin.jsonの公式スキーマに存在しない）"""
        content = json.dumps({"name": "my-plugin", "settings": "./config/settings.json"})
        result = validate_plugin_json(Path("plugin.json"), content)
        assert not result.has_errors()
        assert any("settings" in w and "公式フィールドではありません" in w for w in result.warnings)

    def test_unofficial_settings_field_with_empty_value(self):
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

    # channels フィールドのテスト（v2.1.80以降）

    def test_channels_valid_server_matches_mcp_servers(self):
        """channelsの server が mcpServers キーと一致する場合、整合性警告が出ない"""
        content = json.dumps(
            {
                "name": "my-plugin",
                "mcpServers": {"telegram": {"command": "node", "args": ["server.js"]}},
                "channels": [
                    {
                        "server": "telegram",
                        "userConfig": {
                            "bot_token": {"description": "Bot token", "sensitive": True}
                        },
                    }
                ],
            }
        )
        result = validate_plugin_json(Path("plugin.json"), content)
        assert not result.has_errors()
        assert not any("mcpServers のキーと一致しません" in w for w in result.warnings)

    def test_channels_not_array(self):
        """channelsが配列以外の場合エラー"""
        content = json.dumps({"name": "my-plugin", "channels": {"server": "telegram"}})
        result = validate_plugin_json(Path("plugin.json"), content)
        assert result.has_errors()
        assert any("channels" in e for e in result.errors)

    def test_channels_entry_not_object(self):
        """channelsのエントリがオブジェクト以外の場合エラー"""
        content = json.dumps({"name": "my-plugin", "channels": ["telegram"]})
        result = validate_plugin_json(Path("plugin.json"), content)
        assert result.has_errors()
        assert any("channels[0]" in e for e in result.errors)

    def test_channels_missing_server(self):
        """channelsのserverが欠落した場合エラー"""
        content = json.dumps({"name": "my-plugin", "channels": [{"userConfig": {}}]})
        result = validate_plugin_json(Path("plugin.json"), content)
        assert result.has_errors()
        assert any("server" in e for e in result.errors)

    def test_channels_server_not_string(self):
        """channelsのserverが文字列以外の場合エラー"""
        content = json.dumps({"name": "my-plugin", "channels": [{"server": 123}]})
        result = validate_plugin_json(Path("plugin.json"), content)
        assert result.has_errors()
        assert any("server" in e for e in result.errors)

    def test_channels_server_not_in_mcp_servers(self):
        """channelsのserverがmcpServersに存在しない場合に警告"""
        content = json.dumps(
            {
                "name": "my-plugin",
                "mcpServers": {"slack": {"command": "node"}},
                "channels": [{"server": "telegram"}],
            }
        )
        result = validate_plugin_json(Path("plugin.json"), content)
        assert any("server" in w and "telegram" in w for w in result.warnings)

    def test_channels_server_no_mcp_servers_declared(self):
        """mcpServersが未宣言の場合、serverの整合性チェックは行わない"""
        content = json.dumps({"name": "my-plugin", "channels": [{"server": "telegram"}]})
        result = validate_plugin_json(Path("plugin.json"), content)
        assert not result.has_errors()
        assert not any("server" in w and "telegram" in w for w in result.warnings)

    def test_channels_user_config_not_object(self):
        """per-channel userConfigがオブジェクト以外の場合エラー"""
        content = json.dumps(
            {
                "name": "my-plugin",
                "mcpServers": {"telegram": {"command": "node"}},
                "channels": [{"server": "telegram", "userConfig": "invalid"}],
            }
        )
        result = validate_plugin_json(Path("plugin.json"), content)
        assert result.has_errors()
        assert any("userConfig" in e for e in result.errors)

    def test_channels_user_config_item_not_object(self):
        """per-channel userConfig の設定項目がオブジェクトでない場合エラー"""
        content = json.dumps(
            {
                "name": "my-plugin",
                "mcpServers": {"telegram": {"command": "node"}},
                "channels": [
                    {
                        "server": "telegram",
                        "userConfig": {"bot_token": "invalid"},
                    }
                ],
            }
        )
        result = validate_plugin_json(Path("plugin.json"), content)
        assert result.has_errors()
        assert any("channels[0].userConfig.bot_token" in e for e in result.errors)

    def test_channels_user_config_sensitive_non_boolean(self):
        """per-channel userConfig の sensitive がブール値でない場合エラー"""
        content = json.dumps(
            {
                "name": "my-plugin",
                "mcpServers": {"telegram": {"command": "node"}},
                "channels": [
                    {
                        "server": "telegram",
                        "userConfig": {"bot_token": {"description": "Token", "sensitive": "true"}},
                    }
                ],
            }
        )
        result = validate_plugin_json(Path("plugin.json"), content)
        assert result.has_errors()
        assert any("channels[0].userConfig.bot_token.sensitive" in e for e in result.errors)

    def test_channels_server_empty_string(self):
        """channelsのserverが空文字列の場合エラー（必須ではなく空禁止エラー）"""
        content = json.dumps({"name": "my-plugin", "channels": [{"server": ""}]})
        result = validate_plugin_json(Path("plugin.json"), content)
        assert result.has_errors()
        assert any("空文字列" in e for e in result.errors)

    def test_channels_server_integer_zero(self):
        """server=0 の場合は必須ではなく型エラーを返す"""
        content = json.dumps({"name": "my-plugin", "channels": [{"server": 0}]})
        result = validate_plugin_json(Path("plugin.json"), content)
        assert result.has_errors()
        assert any("文字列" in e for e in result.errors)

    def test_channels_multiple_entries_error_index(self):
        """複数チャンネルのうち特定のエントリが不正ならインデックス付きエラー"""
        content = json.dumps(
            {
                "name": "my-plugin",
                "mcpServers": {"telegram": {"command": "node"}, "slack": {"command": "node"}},
                "channels": [
                    {"server": "telegram"},
                    {"userConfig": {}},
                    {"server": "slack"},
                ],
            }
        )
        result = validate_plugin_json(Path("plugin.json"), content)
        assert result.has_errors()
        assert any("channels[1]" in e and "server" in e for e in result.errors)

    def test_channels_user_config_without_description(self):
        """description がない userConfig エントリは正常（description は必須と明示されていない）"""
        content = json.dumps(
            {
                "name": "my-plugin",
                "mcpServers": {"telegram": {"command": "node"}},
                "channels": [
                    {
                        "server": "telegram",
                        "userConfig": {"bot_token": {"sensitive": True}},
                    }
                ],
            }
        )
        result = validate_plugin_json(Path("plugin.json"), content)
        assert not result.has_errors()

    def test_channels_mcp_servers_empty_dict(self):
        """mcpServers: {} の場合は整合性チェックをスキップ（未宣言と同扱い）"""
        content = json.dumps(
            {"name": "my-plugin", "mcpServers": {}, "channels": [{"server": "telegram"}]}
        )
        result = validate_plugin_json(Path("plugin.json"), content)
        assert not result.has_errors()
        assert not any("server" in w and "telegram" in w for w in result.warnings)

    def test_channels_empty_array(self):
        """channelsが空配列の場合はエラーなし"""
        content = json.dumps({"name": "my-plugin", "channels": []})
        result = validate_plugin_json(Path("plugin.json"), content)
        assert not result.has_errors()

    # monitors インライン配列のテスト（v2.1.105以降）

    def test_monitors_inline_valid(self):
        """monitorsがインライン配列で有効な場合エラーなし"""
        content = json.dumps(
            {
                "name": "my-plugin",
                "monitors": [
                    {
                        "name": "deploy",
                        "command": "./scripts/poll.sh",
                        "description": "Deploy monitor",
                    }
                ],
            }
        )
        result = validate_plugin_json(Path("plugin.json"), content)
        assert not result.has_errors()

    def test_monitors_inline_missing_required(self):
        """monitorsインラインで必須フィールド欠落はエラー"""
        content = json.dumps({"name": "my-plugin", "monitors": [{"name": "only-name"}]})
        result = validate_plugin_json(Path("plugin.json"), content)
        assert result.has_errors()
        assert any("command" in e for e in result.errors)

    def test_monitors_inline_duplicate_names(self):
        """monitorsインラインでname重複はエラー"""
        content = json.dumps(
            {
                "name": "my-plugin",
                "monitors": [
                    {"name": "dup", "command": "a", "description": "a"},
                    {"name": "dup", "command": "b", "description": "b"},
                ],
            }
        )
        result = validate_plugin_json(Path("plugin.json"), content)
        assert result.has_errors()
        assert any("重複" in e for e in result.errors)

    def test_monitors_string_path_skips_entry_validation(self):
        """monitorsが文字列パスの場合はエントリ検証をスキップ（ファイル解決は別途）"""
        content = json.dumps({"name": "my-plugin", "monitors": "./config/monitors.json"})
        result = validate_plugin_json(Path("plugin.json"), content)
        assert not result.has_errors()

    def test_themes_valid_custom_path(self):
        """themesにカスタムパスを指定した場合はエラーなし（v2.1.118以降）"""
        content = json.dumps({"name": "my-plugin", "themes": "./custom-themes/"})
        result = validate_plugin_json(Path("plugin.json"), content)
        assert not result.has_errors()
        assert not any("デフォルトパス" in w for w in result.warnings)

    def test_themes_redundant_default_path(self):
        """themesにデフォルトパスを指定した場合に警告が出ることを確認（v2.1.118以降）"""
        content = json.dumps({"name": "my-plugin", "themes": "./themes/"})
        result = validate_plugin_json(Path("plugin.json"), content)
        assert any("デフォルトパス" in w for w in result.warnings)

    def test_themes_path_without_prefix_warning(self):
        """themesにパスを指定する場合は./プレフィックスを推奨"""
        content = json.dumps({"name": "my-plugin", "themes": "themes/"})
        result = validate_plugin_json(Path("plugin.json"), content)
        assert any("./" in w for w in result.warnings)

    def test_schema_field_valid(self):
        """$schema フィールドが有効であることを確認（v2.1.120以降）"""
        content = json.dumps(
            {
                "$schema": "https://example.com/plugin-schema.json",
                "name": "my-plugin",
            }
        )
        result = validate_plugin_json(Path("plugin.json"), content)
        assert not result.has_errors()
