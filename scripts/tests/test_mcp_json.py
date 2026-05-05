"""
mcp_json.py のテスト
"""

import json
from pathlib import Path

from scripts.validators.mcp_json import validate_mcp_json


class TestValidateMcpJson:
    """MCP設定検証のテスト"""

    def test_valid_stdio(self):
        content = json.dumps(
            {
                "mcpServers": {
                    "test-server": {
                        "type": "stdio",
                        "command": "node",
                        "args": ["server.js"],
                        "env": {"API_KEY": "${API_KEY}"},
                    }
                }
            }
        )
        result = validate_mcp_json(Path(".mcp.json"), content)
        assert not result.has_errors()

    def test_valid_http(self):
        content = json.dumps(
            {
                "mcpServers": {
                    "remote-server": {
                        "type": "http",
                        "url": "https://api.example.com/mcp",
                    }
                }
            }
        )
        result = validate_mcp_json(Path(".mcp.json"), content)
        assert not result.has_errors()

    def test_valid_sse(self):
        content = json.dumps(
            {
                "mcpServers": {
                    "sse-server": {
                        "type": "sse",
                        "url": "https://api.example.com/events",
                    }
                }
            }
        )
        result = validate_mcp_json(Path(".mcp.json"), content)
        assert not result.has_errors()

    def test_invalid_json(self):
        content = "{ invalid json }"
        result = validate_mcp_json(Path(".mcp.json"), content)
        assert result.has_errors()
        assert any("JSON" in e for e in result.errors)

    def test_empty_servers(self):
        content = json.dumps({"mcpServers": {}})
        result = validate_mcp_json(Path(".mcp.json"), content)
        assert not result.has_errors()
        assert any("空" in w for w in result.warnings)

    def test_stdio_missing_command(self):
        content = json.dumps({"mcpServers": {"test-server": {"type": "stdio"}}})
        result = validate_mcp_json(Path(".mcp.json"), content)
        assert result.has_errors()
        assert any("command" in e for e in result.errors)

    def test_http_missing_url(self):
        content = json.dumps({"mcpServers": {"test-server": {"type": "http"}}})
        result = validate_mcp_json(Path(".mcp.json"), content)
        assert result.has_errors()
        assert any("url" in e for e in result.errors)

    def test_sse_missing_url(self):
        content = json.dumps({"mcpServers": {"test-server": {"type": "sse"}}})
        result = validate_mcp_json(Path(".mcp.json"), content)
        assert result.has_errors()
        assert any("url" in e for e in result.errors)

    def test_unknown_server_type(self):
        content = json.dumps(
            {"mcpServers": {"test-server": {"type": "unknown", "command": "test"}}}
        )
        result = validate_mcp_json(Path(".mcp.json"), content)
        assert any("不明なサーバータイプ" in w for w in result.warnings)

    def test_valid_ws(self):
        """WebSocketタイプが有効であることを確認"""
        content = json.dumps(
            {
                "mcpServers": {
                    "ws-server": {
                        "type": "ws",
                        "url": "wss://api.example.com/mcp",
                    }
                }
            }
        )
        result = validate_mcp_json(Path(".mcp.json"), content)
        assert not result.has_errors()

    def test_ws_missing_url(self):
        """WebSocketタイプでurl未指定はエラー"""
        content = json.dumps({"mcpServers": {"test-server": {"type": "ws"}}})
        result = validate_mcp_json(Path(".mcp.json"), content)
        assert result.has_errors()
        assert any("url" in e for e in result.errors)

    def test_default_type_is_stdio(self):
        """typeを省略した場合はstdioとして扱われる"""
        content = json.dumps({"mcpServers": {"test-server": {"command": "node"}}})
        result = validate_mcp_json(Path(".mcp.json"), content)
        assert not result.has_errors()

    def test_always_load_true(self):
        """alwaysLoad: true は有効（v2.1.121以降）"""
        content = json.dumps(
            {
                "mcpServers": {
                    "test-server": {
                        "type": "stdio",
                        "command": "node",
                        "alwaysLoad": True,
                    }
                }
            }
        )
        result = validate_mcp_json(Path(".mcp.json"), content)
        assert not result.has_errors()

    def test_always_load_false(self):
        """alwaysLoad: false は有効（v2.1.121以降）"""
        content = json.dumps(
            {
                "mcpServers": {
                    "test-server": {
                        "type": "stdio",
                        "command": "node",
                        "alwaysLoad": False,
                    }
                }
            }
        )
        result = validate_mcp_json(Path(".mcp.json"), content)
        assert not result.has_errors()

    def test_always_load_non_boolean(self):
        """alwaysLoadがブール値以外の場合はエラー（v2.1.121以降）"""
        content = json.dumps(
            {
                "mcpServers": {
                    "test-server": {
                        "type": "stdio",
                        "command": "node",
                        "alwaysLoad": "true",
                    }
                }
            }
        )
        result = validate_mcp_json(Path(".mcp.json"), content)
        assert result.has_errors()
        assert any("alwaysLoad" in e for e in result.errors)

    def test_reserved_server_name_workspace(self):
        """予約済みサーバー名 'workspace' を使用するとエラー（v2.1.128以降）"""
        content = json.dumps(
            {
                "mcpServers": {
                    "workspace": {
                        "type": "stdio",
                        "command": "node",
                        "args": ["server.js"],
                    }
                }
            }
        )
        result = validate_mcp_json(Path(".mcp.json"), content)
        assert result.has_errors()
        assert any("予約済み" in e for e in result.errors)

    def test_non_reserved_server_name(self):
        """予約済みでないサーバー名はエラーにならない"""
        content = json.dumps(
            {
                "mcpServers": {
                    "my-workspace": {
                        "type": "stdio",
                        "command": "node",
                        "args": ["server.js"],
                    }
                }
            }
        )
        result = validate_mcp_json(Path(".mcp.json"), content)
        assert not result.has_errors()
