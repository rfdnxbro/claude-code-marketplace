"""
.mcp.json のバリデーター
"""

from pathlib import Path

from .base import ValidationResult, check_env_secrets, parse_json_safe


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
        server_type = config.get("type", "stdio")

        if server_type == "stdio":
            if not config.get("command"):
                result.add_error(
                    f"{file_path.name}: {server_name}: stdioタイプにはcommandが必須です"
                )
        elif server_type in ["http", "sse"]:
            if not config.get("url"):
                result.add_error(
                    f"{file_path.name}: {server_name}: {server_type}タイプにはurlが必須です"
                )
        else:
            result.add_warning(
                f"{file_path.name}: {server_name}: 不明なサーバータイプ: {server_type}"
            )

        # 環境変数の直接記述をチェック
        env = config.get("env", {})
        check_env_secrets(result, file_path, server_name, env)

    return result
