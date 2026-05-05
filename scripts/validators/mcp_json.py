"""
.mcp.json のバリデーター
"""

from pathlib import Path

from .base import ValidationResult, parse_json_safe

RESERVED_SERVER_NAMES = {"workspace"}


def validate_mcp_json(file_path: Path, content: str) -> ValidationResult:
    """MCPサーバー設定を検証する"""
    result = ValidationResult()

    data = parse_json_safe(content, file_path, result)
    if data is None:
        return result

    servers = data.get("mcpServers", {})
    if not servers:
        result.add_warning(f"{file_path.name}: mcpServersが空です")
        return result

    for server_name, config in servers.items():
        if server_name in RESERVED_SERVER_NAMES:
            result.add_error(
                f"{file_path.name}: '{server_name}' は予約済みサーバー名です（v2.1.128以降）。"
                "使用すると警告とともにスキップされます"
            )
        server_type = config.get("type", "stdio")

        if server_type == "stdio":
            if not config.get("command"):
                result.add_error(
                    f"{file_path.name}: {server_name}: stdioタイプにはcommandが必須です"
                )
        elif server_type in ["http", "sse", "ws"]:
            if not config.get("url"):
                result.add_error(
                    f"{file_path.name}: {server_name}: {server_type}タイプにはurlが必須です"
                )
        else:
            result.add_warning(
                f"{file_path.name}: {server_name}: 不明なサーバータイプ: {server_type}"
            )

        # alwaysLoad はブール値のみ有効（v2.1.121以降）
        always_load = config.get("alwaysLoad")
        if always_load is not None and not isinstance(always_load, bool):
            result.add_error(f"{file_path.name}: {server_name}: alwaysLoadはブール値が必要です")

    return result
