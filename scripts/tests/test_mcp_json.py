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

    def test_default_type_is_stdio(self):
        """typeを省略した場合はstdioとして扱われる"""
        content = json.dumps({"mcpServers": {"test-server": {"command": "node"}}})
        result = validate_mcp_json(Path(".mcp.json"), content)
        assert not result.has_errors()
