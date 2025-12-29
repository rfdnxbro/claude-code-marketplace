"""
.mcp.json のバリデーター
"""

import json
import re
from pathlib import Path

from .base import ValidationResult


def validate_mcp_json(file_path: Path, content: str) -> ValidationResult:
    """MCPサーバー設定を検証する"""
    result = ValidationResult()

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        result.add_error(f"{file_path.name}: JSONパースエラー: {e}")
        return result

    servers = data.get("mcpServers", {})
    if not servers:
        result.add_warning(f"{file_path.name}: mcpServersが空です")
        return result

    for server_name, config in servers.items():
        server_type = config.get("type", "stdio")

        if server_type == "stdio":
            if not config.get("command"):
                result.add_error(f"{file_path.name}: {server_name}: stdioタイプにはcommandが必須です")
        elif server_type in ["http", "sse"]:
            if not config.get("url"):
                result.add_error(f"{file_path.name}: {server_name}: {server_type}タイプにはurlが必須です")
        else:
            result.add_warning(f"{file_path.name}: {server_name}: 不明なサーバータイプ: {server_type}")

        # 環境変数の直接記述をチェック
        env = config.get("env", {})
        for key, value in env.items():
            if isinstance(value, str) and not value.startswith("${"):
                # 既知の機密情報パターン（検出時はエラー）
                secret_patterns = [
                    (r"sk-[a-zA-Z0-9]{32,}", "OpenAI APIキー"),
                    (r"sk-proj-[a-zA-Z0-9]{32,}", "OpenAI Project APIキー"),
                    (r"ghp_[a-zA-Z0-9]{36}", "GitHub Personal Access Token"),
                    (r"gho_[a-zA-Z0-9]{36}", "GitHub OAuth Token"),
                    (r"ghu_[a-zA-Z0-9]{36}", "GitHub User Token"),
                    (r"ghs_[a-zA-Z0-9]{36}", "GitHub Server Token"),
                    (r"xoxb-[a-zA-Z0-9-]+", "Slack Bot Token"),
                    (r"xoxa-[a-zA-Z0-9-]+", "Slack App Token"),
                    (r"xoxp-[a-zA-Z0-9-]+", "Slack User Token"),
                    (r"AKIA[A-Z0-9]{16}", "AWS Access Key ID"),
                    (r"AIza[a-zA-Z0-9_-]{35}", "Google API Key"),
                ]

                for pattern, description in secret_patterns:
                    if re.search(pattern, value):
                        result.add_error(f"{file_path.name}: {server_name}: envの{key}に{description}が直接記述されています。${{VAR}}形式を使用してください")
                        break
                else:
                    # 既知パターンに一致しない場合、汎用チェック（警告）
                    if len(value) > 20 and re.match(r"^[a-zA-Z0-9_-]+$", value):
                        result.add_warning(f"{file_path.name}: {server_name}: envの{key}に機密情報が直接記述されている可能性があります。${{VAR}}形式を使用してください")

    return result
