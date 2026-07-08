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

# source_type別の必須サブフィールド一覧（settingsは追加の必須フィールドなし）
REQUIRED_FIELDS_BY_SOURCE_TYPE = {
    "github": ["repo"],
    "url": ["url"],
    "npm": ["package"],
    "git-subdir": ["url", "path"],
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

    # オプションフィールド: renames（v2.1.193以降）
    renames = data.get("renames")
    if renames is not None:
        if not isinstance(renames, dict):
            result.add_error(f"{file_path.name}: renamesはオブジェクトが必要です")
        else:
            for old_name, new_name in renames.items():
                # JSONのオブジェクトキーは常に文字列のためkebab-caseのみ検証する
                kebab_error = validate_kebab_case(old_name)
                if kebab_error:
                    result.add_error(f"{file_path.name}: renames キー '{old_name}': {kebab_error}")
                if not isinstance(new_name, str):
                    result.add_error(
                        f"{file_path.name}: renames['{old_name}'] の値は文字列が必要です"
                    )
                else:
                    kebab_error = validate_kebab_case(new_name)
                    if kebab_error:
                        result.add_error(
                            f"{file_path.name}: renames['{old_name}'] 値: {kebab_error}"
                        )

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

            # defaultEnabled の確認（v2.1.154以降）
            default_enabled = plugin.get("defaultEnabled")
            if default_enabled is not None and not isinstance(default_enabled, bool):
                result.add_error(
                    f"{file_path.name}: plugins[{i}].defaultEnabledは"
                    "ブール値（true/false）が必要です"
                )

            # プラグインのsourceは必須
            source = plugin.get("source")
            if not source:
                result.add_error(f"{file_path.name}: plugins[{i}].sourceは必須です")
            elif not isinstance(source, (str, dict)):
                result.add_error(
                    f"{file_path.name}: plugins[{i}].sourceは文字列またはオブジェクトが必要です"
                )
            elif isinstance(source, dict):
                # オブジェクト形式のsourceタイプを検証
                source_type = source.get("source")
                valid_source_types = ["github", "url", "npm", "git-subdir", "settings"]
                if not source_type:
                    result.add_error(f"{file_path.name}: plugins[{i}].source.sourceは必須です")
                elif source_type not in valid_source_types:
                    types_str = "/".join(valid_source_types)
                    result.add_error(
                        f"{file_path.name}: plugins[{i}].source.sourceは無効な値です: "
                        f"{source_type}（{types_str}）"
                    )
                else:
                    # skipLfsフィールドの検証（github/urlソースのみ対応、v2.1.153以降）
                    skip_lfs = source.get("skipLfs")
                    if skip_lfs is not None and source_type in ("github", "url"):
                        if not isinstance(skip_lfs, bool):
                            result.add_error(
                                f"{file_path.name}: plugins[{i}].source.skipLfsはbooleanが必要です"
                            )

                    # source_type別の必須サブフィールドの検証
                    for field in REQUIRED_FIELDS_BY_SOURCE_TYPE.get(source_type, []):
                        field_value = source.get(field)
                        if not field_value:
                            result.add_error(
                                f"{file_path.name}: plugins[{i}].source.{field}は必須です"
                                f"（source: {source_type}）"
                            )
                        elif not isinstance(field_value, str):
                            result.add_error(
                                f"{file_path.name}: plugins[{i}].source.{field}は文字列が必要です"
                            )
                    # source_type == "settings" の場合、追加の必須フィールドなし

    return result
