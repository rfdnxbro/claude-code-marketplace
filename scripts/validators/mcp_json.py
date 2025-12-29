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
                # APIキーっぽい文字列をチェック
                if len(value) > 20 and re.match(r"^[a-zA-Z0-9_-]+$", value):
                    result.add_warning(f"{file_path.name}: {server_name}: envの{key}に機密情報が直接記述されている可能性があります。${{VAR}}形式を使用してください")

    return result
