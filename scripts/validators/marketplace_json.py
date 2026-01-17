"""
marketplace.json のバリデーター
"""

from pathlib import Path

from .base import ValidationResult, parse_json_safe, validate_kebab_case

# 予約済み名前（使用不可）
RESERVED_NAMES = {
    "claude-code-marketplace",
    "claude-code-plugins",
    "claude-plugins-official",
    "anthropic-marketplace",
    "anthropic-plugins",
    "agent-skills",
    "life-sciences",
}


def validate_marketplace_json(file_path: Path, content: str) -> ValidationResult:
    """marketplace.jsonを検証する"""
    result = ValidationResult()

    data = parse_json_safe(content, file_path, result)
    if data is None:
        return result

    if not isinstance(data, dict):
        result.add_error(f"{file_path.name}: ルートはオブジェクトである必要があります")
        return result

    # 必須フィールド: name
    name = data.get("name")
    if not name:
        result.add_error(f"{file_path.name}: nameは必須です")
    elif not isinstance(name, str):
        result.add_error(f"{file_path.name}: nameは文字列が必要です")
    else:
        # kebab-caseチェック
        kebab_error = validate_kebab_case(name)
        if kebab_error:
            result.add_error(f"{file_path.name}: {kebab_error}")
        # 予約語チェック
        if name in RESERVED_NAMES:
            result.add_error(f"{file_path.name}: nameは予約済みです: {name}")

    # 必須フィールド: owner
    owner = data.get("owner")
    if not owner:
        result.add_error(f"{file_path.name}: ownerは必須です")
    elif not isinstance(owner, dict):
        result.add_error(f"{file_path.name}: ownerはオブジェクトが必要です")
    else:
        # owner.name は必須
        owner_name = owner.get("name")
        if not owner_name:
            result.add_error(f"{file_path.name}: owner.nameは必須です")
        elif not isinstance(owner_name, str):
            result.add_error(f"{file_path.name}: owner.nameは文字列が必要です")

    # 必須フィールド: plugins
    plugins = data.get("plugins")
    if plugins is None:
        result.add_error(f"{file_path.name}: pluginsは必須です")
    elif not isinstance(plugins, list):
        result.add_error(f"{file_path.name}: pluginsは配列が必要です")
    else:
        # 各プラグインエントリを検証
        for i, plugin in enumerate(plugins):
            if not isinstance(plugin, dict):
                result.add_error(f"{file_path.name}: plugins[{i}]はオブジェクトが必要です")
                continue

            # プラグインのnameは必須
            plugin_name = plugin.get("name")
            if not plugin_name:
                result.add_error(f"{file_path.name}: plugins[{i}].nameは必須です")
            elif not isinstance(plugin_name, str):
                result.add_error(f"{file_path.name}: plugins[{i}].nameは文字列が必要です")
            else:
                # kebab-caseチェック
                kebab_error = validate_kebab_case(plugin_name)
                if kebab_error:
                    result.add_error(f"{file_path.name}: plugins[{i}]: {kebab_error}")

            # プラグインのsourceは必須
            source = plugin.get("source")
            if not source:
                result.add_error(f"{file_path.name}: plugins[{i}].sourceは必須です")
            elif not isinstance(source, (str, dict)):
                result.add_error(
                    f"{file_path.name}: plugins[{i}].sourceは文字列またはオブジェクトが必要です"
                )

    return result
