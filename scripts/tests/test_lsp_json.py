"""
lsp_json.py のテスト
"""

import json
from pathlib import Path

from scripts.validators.lsp_json import validate_lsp_json


class TestValidateLspJson:
    """LSP設定検証のテスト"""

    def test_valid_minimal(self):
        """最小限の有効な設定"""
        content = json.dumps({"go": {"command": "gopls", "extensionToLanguage": {".go": "go"}}})
        result = validate_lsp_json(Path(".lsp.json"), content)
        assert not result.has_errors()

    def test_valid_full(self):
        """すべてのオプションを含む有効な設定"""
        content = json.dumps(
            {
                "rust": {
                    "command": "rust-analyzer",
                    "args": ["--stdio"],
                    "transport": "stdio",
                    "extensionToLanguage": {".rs": "rust"},
                    "env": {"RUST_LOG": "${RUST_LOG:-info}"},
                    "initializationOptions": {"checkOnSave": {"command": "clippy"}},
                    "settings": {"rust-analyzer": {"cargo": {"allFeatures": True}}},
                    "workspaceFolder": "/workspace",
                    "startupTimeout": 30000,
                    "shutdownTimeout": 5000,
                    "restartOnCrash": True,
                    "maxRestarts": 3,
                }
            }
        )
        result = validate_lsp_json(Path(".lsp.json"), content)
        assert not result.has_errors()

    def test_valid_multiple_servers(self):
        """複数サーバーの設定"""
        content = json.dumps(
            {
                "go": {"command": "gopls", "extensionToLanguage": {".go": "go"}},
                "python": {
                    "command": "pyright-langserver",
                    "args": ["--stdio"],
                    "extensionToLanguage": {".py": "python", ".pyi": "python"},
                },
            }
        )
        result = validate_lsp_json(Path(".lsp.json"), content)
        assert not result.has_errors()

    def test_invalid_json(self):
        """不正なJSON"""
        content = "{ invalid json }"
        result = validate_lsp_json(Path(".lsp.json"), content)
        assert result.has_errors()
        assert any("JSON" in e for e in result.errors)

    def test_empty_config(self):
        """空の設定（警告）"""
        content = json.dumps({})
        result = validate_lsp_json(Path(".lsp.json"), content)
        assert not result.has_errors()
        assert any("空" in w for w in result.warnings)

    def test_missing_command(self):
        """commandがない（エラー）"""
        content = json.dumps({"go": {"extensionToLanguage": {".go": "go"}}})
        result = validate_lsp_json(Path(".lsp.json"), content)
        assert result.has_errors()
        assert any("command" in e for e in result.errors)

    def test_missing_extension_to_language(self):
        """extensionToLanguageがない（エラー）"""
        content = json.dumps({"go": {"command": "gopls"}})
        result = validate_lsp_json(Path(".lsp.json"), content)
        assert result.has_errors()
        assert any("extensionToLanguage" in e for e in result.errors)

    def test_invalid_extension_to_language_type(self):
        """extensionToLanguageが不正な型"""
        content = json.dumps({"go": {"command": "gopls", "extensionToLanguage": "invalid"}})
        result = validate_lsp_json(Path(".lsp.json"), content)
        assert result.has_errors()
        assert any("extensionToLanguage" in e and "オブジェクト" in e for e in result.errors)

    def test_extension_without_dot(self):
        """拡張子が.で始まっていない（警告）"""
        content = json.dumps({"go": {"command": "gopls", "extensionToLanguage": {"go": "go"}}})
        result = validate_lsp_json(Path(".lsp.json"), content)
        assert any(".で開始" in w for w in result.warnings)

    def test_empty_language_id(self):
        """言語IDが空（エラー）"""
        content = json.dumps({"go": {"command": "gopls", "extensionToLanguage": {".go": ""}}})
        result = validate_lsp_json(Path(".lsp.json"), content)
        assert result.has_errors()
        assert any("言語ID" in e for e in result.errors)

    def test_unknown_transport(self):
        """不明なtransport（警告）"""
        content = json.dumps(
            {
                "go": {
                    "command": "gopls",
                    "transport": "unknown",
                    "extensionToLanguage": {".go": "go"},
                }
            }
        )
        result = validate_lsp_json(Path(".lsp.json"), content)
        assert any("transport" in w for w in result.warnings)

    def test_valid_transport_socket(self):
        """socketトランスポートは有効"""
        content = json.dumps(
            {
                "go": {
                    "command": "gopls",
                    "transport": "socket",
                    "extensionToLanguage": {".go": "go"},
                }
            }
        )
        result = validate_lsp_json(Path(".lsp.json"), content)
        assert not result.has_errors()
        assert not result.warnings

    def test_invalid_args_type(self):
        """argsが配列でない（エラー）"""
        content = json.dumps(
            {"go": {"command": "gopls", "args": "--stdio", "extensionToLanguage": {".go": "go"}}}
        )
        result = validate_lsp_json(Path(".lsp.json"), content)
        assert result.has_errors()
        assert any("args" in e and "配列" in e for e in result.errors)

    def test_invalid_timeout_type(self):
        """タイムアウトが数値でない（エラー）"""
        content = json.dumps(
            {
                "go": {
                    "command": "gopls",
                    "extensionToLanguage": {".go": "go"},
                    "startupTimeout": "30000",
                }
            }
        )
        result = validate_lsp_json(Path(".lsp.json"), content)
        assert result.has_errors()
        assert any("startupTimeout" in e and "数値" in e for e in result.errors)

    def test_invalid_restart_on_crash_type(self):
        """restartOnCrashがブール値でない（エラー）"""
        content = json.dumps(
            {
                "go": {
                    "command": "gopls",
                    "extensionToLanguage": {".go": "go"},
                    "restartOnCrash": "true",
                }
            }
        )
        result = validate_lsp_json(Path(".lsp.json"), content)
        assert result.has_errors()
        assert any("restartOnCrash" in e and "ブール" in e for e in result.errors)

    def test_server_config_not_object(self):
        """サーバー設定がオブジェクトでない"""
        content = json.dumps({"go": "invalid"})
        result = validate_lsp_json(Path(".lsp.json"), content)
        assert result.has_errors()
        assert any("設定はオブジェクトが必要" in e for e in result.errors)

    def test_root_not_object(self):
        """ルートがオブジェクトでない"""
        content = json.dumps(["invalid"])
        result = validate_lsp_json(Path(".lsp.json"), content)
        assert result.has_errors()
        assert any("ルートはオブジェクト" in e for e in result.errors)

    def test_env_valid(self):
        """envがオブジェクトで有効"""
        content = json.dumps(
            {
                "go": {
                    "command": "gopls",
                    "extensionToLanguage": {".go": "go"},
                    "env": {"GOPATH": "/go", "GOROOT": "/usr/local/go"},
                }
            }
        )
        result = validate_lsp_json(Path(".lsp.json"), content)
        assert not result.has_errors()

    def test_env_invalid_type(self):
        """envがオブジェクトでない（エラー）"""
        content = json.dumps(
            {
                "go": {
                    "command": "gopls",
                    "extensionToLanguage": {".go": "go"},
                    "env": "invalid",
                }
            }
        )
        result = validate_lsp_json(Path(".lsp.json"), content)
        assert result.has_errors()
        assert any("env" in e and "オブジェクト" in e for e in result.errors)
