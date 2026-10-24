"""
.mcp.json のバリデーター
"""

from pathlib import Path

from .base import ValidationResult, parse_json_safe
from .secret_detection import detect_hardcoded_secrets

RESERVED_SERVER_NAMES = {"workspace", "Claude Browser", "Claude Preview"}
# クラウドセッション・セルフホストランナーでのみ予約されるサーバー名
CLOUD_RESERVED_SERVER_NAMES = {"widgets"}


def validate_mcp_json(file_path: Path, content: str) -> ValidationResult:
    """MCPサーバー設定を検証する"""
    result = ValidationResult()

    data = parse_json_safe(content, file_path, result)
    if data is None:
        return result

    detect_hardcoded_secrets(result, file_path, content)

    servers = data.get("mcpServers", {})
    if not isinstance(servers, dict):
        result.add_error(f"{file_path.name}: mcpServersはオブジェクトが必要です")
        return result
    if not servers:
        result.add_warning(f"{file_path.name}: mcpServersが空です")
        return result

    for server_name, config in servers.items():
        if server_name in RESERVED_SERVER_NAMES:
            result.add_error(
                f"{file_path.name}: '{server_name}' は予約済みサーバー名です。"
                "使用すると警告とともにスキップされます"
            )
        elif server_name in CLOUD_RESERVED_SERVER_NAMES:
            result.add_warning(
                f"{file_path.name}: '{server_name}' はクラウドセッションと"
                "セルフホストランナーで予約済みのため、そこではロードされません"
            )

        if not isinstance(config, dict):
            result.add_error(f"{file_path.name}: {server_name}: 設定はオブジェクトが必要")
            continue

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
        # null も不正値として扱うため、キーの有無で判定する
        if "alwaysLoad" in config and not isinstance(config["alwaysLoad"], bool):
            result.add_error(f"{file_path.name}: {server_name}: alwaysLoadはブール値が必要です")

        # bareElicitationCapability はブール値のみ有効
        if "bareElicitationCapability" in config and not isinstance(
            config["bareElicitationCapability"], bool
        ):
            result.add_error(
                f"{file_path.name}: {server_name}: bareElicitationCapabilityはブール値が必要です"
            )

    return result
