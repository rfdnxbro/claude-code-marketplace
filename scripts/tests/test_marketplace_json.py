"""
marketplace_json.py のテスト
"""

import json
from pathlib import Path

from scripts.validators.marketplace_json import validate_marketplace_json


class TestValidateMarketplaceJson:
    """marketplace.json検証のテスト"""

    def test_valid_minimal(self):
        """最小限の有効な設定"""
        content = json.dumps(
            {
                "name": "my-marketplace",
                "owner": {"name": "Team Name"},
                "plugins": [{"name": "plugin-one", "source": "./plugins/plugin-one"}],
            }
        )
        result = validate_marketplace_json(Path("marketplace.json"), content)
        assert not result.has_errors()

    def test_valid_full(self):
        """すべてのオプションを含む有効な設定"""
        content = json.dumps(
            {
                "name": "my-marketplace",
                "owner": {"name": "Team Name", "email": "team@example.com"},
                "metadata": {
                    "description": "マーケットプレイスの説明",
                    "version": "1.0.0",
                    "pluginRoot": "./plugins",
                },
                "plugins": [
                    {
                        "name": "plugin-one",
                        "source": "./plugins/plugin-one",
                        "description": "プラグインの説明",
                        "version": "1.0.0",
                    },
                    {
                        "name": "plugin-two",
                        "source": {"source": "github", "repo": "owner/repo"},
                    },
                ],
            }
        )
        result = validate_marketplace_json(Path("marketplace.json"), content)
        assert not result.has_errors()

    def test_invalid_json(self):
        """不正なJSON"""
        content = "{ invalid json }"
        result = validate_marketplace_json(Path("marketplace.json"), content)
        assert result.has_errors()
        assert any("JSON" in e for e in result.errors)

    def test_missing_name(self):
        """nameがない（エラー）"""
        content = json.dumps(
            {
                "owner": {"name": "Team Name"},
                "plugins": [{"name": "plugin-one", "source": "./plugins/plugin-one"}],
            }
        )
        result = validate_marketplace_json(Path("marketplace.json"), content)
        assert result.has_errors()
        assert any("name" in e and "必須" in e for e in result.errors)

    def test_invalid_name_format(self):
        """nameがkebab-caseでない（エラー）"""
        content = json.dumps(
            {
                "name": "My_Marketplace",
                "owner": {"name": "Team Name"},
                "plugins": [{"name": "plugin-one", "source": "./plugins/plugin-one"}],
            }
        )
        result = validate_marketplace_json(Path("marketplace.json"), content)
        assert result.has_errors()
        assert any("kebab-case" in e for e in result.errors)

    def test_reserved_name(self):
        """予約済み名前（エラー）"""
        content = json.dumps(
            {
                "name": "anthropic-marketplace",
                "owner": {"name": "Team Name"},
                "plugins": [{"name": "plugin-one", "source": "./plugins/plugin-one"}],
            }
        )
        result = validate_marketplace_json(Path("marketplace.json"), content)
        assert result.has_errors()
        assert any("予約済み" in e for e in result.errors)

    def test_missing_owner(self):
        """ownerがない（エラー）"""
        content = json.dumps(
            {
                "name": "my-marketplace",
                "plugins": [{"name": "plugin-one", "source": "./plugins/plugin-one"}],
            }
        )
        result = validate_marketplace_json(Path("marketplace.json"), content)
        assert result.has_errors()
        assert any("owner" in e and "必須" in e for e in result.errors)

    def test_missing_owner_name(self):
        """owner.nameがない（エラー）"""
        content = json.dumps(
            {
                "name": "my-marketplace",
                "owner": {"email": "team@example.com"},
                "plugins": [{"name": "plugin-one", "source": "./plugins/plugin-one"}],
            }
        )
        result = validate_marketplace_json(Path("marketplace.json"), content)
        assert result.has_errors()
        assert any("owner.name" in e for e in result.errors)

    def test_missing_plugins(self):
        """pluginsがない（エラー）"""
        content = json.dumps({"name": "my-marketplace", "owner": {"name": "Team Name"}})
        result = validate_marketplace_json(Path("marketplace.json"), content)
        assert result.has_errors()
        assert any("plugins" in e and "必須" in e for e in result.errors)

    def test_plugins_not_array(self):
        """pluginsが配列でない（エラー）"""
        content = json.dumps(
            {
                "name": "my-marketplace",
                "owner": {"name": "Team Name"},
                "plugins": "invalid",
            }
        )
        result = validate_marketplace_json(Path("marketplace.json"), content)
        assert result.has_errors()
        assert any("plugins" in e and "配列" in e for e in result.errors)

    def test_plugin_missing_name(self):
        """プラグインにnameがない（エラー）"""
        content = json.dumps(
            {
                "name": "my-marketplace",
                "owner": {"name": "Team Name"},
                "plugins": [{"source": "./plugins/plugin-one"}],
            }
        )
        result = validate_marketplace_json(Path("marketplace.json"), content)
        assert result.has_errors()
        assert any("plugins[0].name" in e for e in result.errors)

    def test_plugin_invalid_name_format(self):
        """プラグインのnameがkebab-caseでない（エラー）"""
        content = json.dumps(
            {
                "name": "my-marketplace",
                "owner": {"name": "Team Name"},
                "plugins": [{"name": "Plugin_One", "source": "./plugins/plugin-one"}],
            }
        )
        result = validate_marketplace_json(Path("marketplace.json"), content)
        assert result.has_errors()
        assert any("kebab-case" in e for e in result.errors)

    def test_plugin_missing_source(self):
        """プラグインにsourceがない（エラー）"""
        content = json.dumps(
            {
                "name": "my-marketplace",
                "owner": {"name": "Team Name"},
                "plugins": [{"name": "plugin-one"}],
            }
        )
        result = validate_marketplace_json(Path("marketplace.json"), content)
        assert result.has_errors()
        assert any("plugins[0].source" in e for e in result.errors)

    def test_plugin_source_object(self):
        """プラグインのsourceがオブジェクト形式でも有効"""
        content = json.dumps(
            {
                "name": "my-marketplace",
                "owner": {"name": "Team Name"},
                "plugins": [
                    {"name": "plugin-one", "source": {"source": "github", "repo": "owner/repo"}}
                ],
            }
        )
        result = validate_marketplace_json(Path("marketplace.json"), content)
        assert not result.has_errors()

    def test_root_not_object(self):
        """ルートがオブジェクトでない"""
        content = json.dumps(["invalid"])
        result = validate_marketplace_json(Path("marketplace.json"), content)
        assert result.has_errors()
        assert any("ルートはオブジェクト" in e for e in result.errors)

    def test_name_not_string(self):
        """nameが文字列でない（エラー）"""
        content = json.dumps(
            {
                "name": 123,
                "owner": {"name": "Team Name"},
                "plugins": [{"name": "plugin-one", "source": "./plugins/plugin-one"}],
            }
        )
        result = validate_marketplace_json(Path("marketplace.json"), content)
        assert result.has_errors()
        assert any("name" in e and "文字列が必要" in e for e in result.errors)

    def test_owner_not_object(self):
        """ownerがオブジェクトでない（エラー）"""
        content = json.dumps(
            {
                "name": "my-marketplace",
                "owner": "string-owner",
                "plugins": [{"name": "plugin-one", "source": "./plugins/plugin-one"}],
            }
        )
        result = validate_marketplace_json(Path("marketplace.json"), content)
        assert result.has_errors()
        assert any("owner" in e and "オブジェクトが必要" in e for e in result.errors)

    def test_owner_name_not_string(self):
        """owner.nameが文字列でない（エラー）"""
        content = json.dumps(
            {
                "name": "my-marketplace",
                "owner": {"name": 123},
                "plugins": [{"name": "plugin-one", "source": "./plugins/plugin-one"}],
            }
        )
        result = validate_marketplace_json(Path("marketplace.json"), content)
        assert result.has_errors()
        assert any("owner.name" in e and "文字列が必要" in e for e in result.errors)

    def test_plugin_not_object(self):
        """プラグインエントリがオブジェクトでない（エラー）"""
        content = json.dumps(
            {
                "name": "my-marketplace",
                "owner": {"name": "Team Name"},
                "plugins": ["invalid-plugin"],
            }
        )
        result = validate_marketplace_json(Path("marketplace.json"), content)
        assert result.has_errors()
        assert any("plugins[0]" in e and "オブジェクトが必要" in e for e in result.errors)

    def test_plugin_name_not_string(self):
        """プラグインのnameが文字列でない（エラー）"""
        content = json.dumps(
            {
                "name": "my-marketplace",
                "owner": {"name": "Team Name"},
                "plugins": [{"name": 123, "source": "./plugins/plugin-one"}],
            }
        )
        result = validate_marketplace_json(Path("marketplace.json"), content)
        assert result.has_errors()
        assert any("plugins[0].name" in e and "文字列が必要" in e for e in result.errors)

    def test_plugin_source_invalid_type(self):
        """プラグインのsourceが文字列でもオブジェクトでもない（エラー）"""
        content = json.dumps(
            {
                "name": "my-marketplace",
                "owner": {"name": "Team Name"},
                "plugins": [{"name": "plugin-one", "source": 123}],
            }
        )
        result = validate_marketplace_json(Path("marketplace.json"), content)
        assert result.has_errors()
        assert any(
            "plugins[0].source" in e and "文字列またはオブジェクト" in e for e in result.errors
        )
