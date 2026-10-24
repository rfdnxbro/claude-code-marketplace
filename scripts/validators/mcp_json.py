"""
.mcp.json のバリデーター
"""

import ipaddress
import re
from pathlib import Path
from urllib.parse import urlsplit

from .base import ValidationResult, parse_json_safe
from .secret_detection import detect_hardcoded_secrets

RESERVED_SERVER_NAMES = {"workspace", "Claude Browser", "Claude Preview"}
# ${user_config.KEY} 形式の参照
USER_CONFIG_REFERENCE_PATTERN = re.compile(r"\$\{user_config\.([A-Za-z0-9_-]+)\}")

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
                validate_server_url(result, file_path, server_name, config["url"])
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


def _is_loopback_host(host: str) -> bool:
    if host == "localhost" or host.endswith(".localhost"):
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def validate_server_url(
    result: ValidationResult, file_path: Path, server_name: str, url: object
) -> None:
    """リモートMCPサーバーの url を検証する（claude plugin validate と同じ観点）

    - 絶対URLでない url はエラー（`${...}` を含む場合は展開後に決まるため対象外）
    - ループバック以外のホストへの http:// / ws:// は警告
    """
    if not isinstance(url, str) or "${" in url:
        return
    try:
        parts = urlsplit(url)
        hostname = parts.hostname
    except ValueError:
        # 閉じていない IPv6 の角括弧などは解析時に例外になる
        hostname = None
        parts = None
    if parts is None or parts.scheme not in ("http", "https", "ws", "wss") or not hostname:
        result.add_error(
            f"{file_path.name}: {server_name}: urlが有効な絶対URLではありません: {url}"
        )
        return
    if parts.scheme in ("http", "ws") and not _is_loopback_host(hostname):
        result.add_warning(
            f"{file_path.name}: {server_name}: ループバック以外のホストへの"
            f"暗号化されていない接続（{parts.scheme}://）です: {url}"
        )


def find_user_config_references(value: object) -> set[str]:
    """設定値の中で参照されている ${user_config.KEY} のキー名を集める"""
    if isinstance(value, str):
        return set(USER_CONFIG_REFERENCE_PATTERN.findall(value))
    if isinstance(value, dict):
        values = list(value.values())
    elif isinstance(value, list):
        values = value
    else:
        return set()
    found: set[str] = set()
    for item in values:
        found |= find_user_config_references(item)
    return found
