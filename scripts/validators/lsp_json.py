"""
.lsp.json のバリデーター
"""

from pathlib import Path

from .base import ValidationResult, parse_json_safe

# 有効なtransport値
VALID_TRANSPORTS = {"stdio", "socket"}


def validate_lsp_json(file_path: Path, content: str) -> ValidationResult:
    """LSPサーバー設定を検証する"""
    result = ValidationResult()

    data = parse_json_safe(content, file_path, result)
    if data is None:
        return result

    if not data:
        result.add_warning(f"{file_path.name}: LSPサーバー設定が空です")
        return result

    if not isinstance(data, dict):
        result.add_error(f"{file_path.name}: ルートはオブジェクトである必要があります")
        return result

    for server_name, config in data.items():
        if not isinstance(config, dict):
            result.add_error(f"{file_path.name}: {server_name}: 設定はオブジェクトが必要")
            continue

        # 必須フィールド: command
        if not config.get("command"):
            result.add_error(f"{file_path.name}: {server_name}: commandは必須です")

        # 必須フィールド: extensionToLanguage
        ext_to_lang = config.get("extensionToLanguage")
        if not ext_to_lang:
            result.add_error(f"{file_path.name}: {server_name}: extensionToLanguageは必須です")
        elif not isinstance(ext_to_lang, dict):
            result.add_error(
                f"{file_path.name}: {server_name}: extensionToLanguageはオブジェクトが必要"
            )
        else:
            # 拡張子の形式をチェック
            for ext, lang_id in ext_to_lang.items():
                if not ext.startswith("."):
                    result.add_warning(f"{file_path.name}: {server_name}: 拡張子は.で開始: {ext}")
                if not isinstance(lang_id, str) or not lang_id:
                    result.add_error(
                        f"{file_path.name}: {server_name}: 言語IDは空でない文字列: {ext}"
                    )

        # transport のバリデーション
        transport = config.get("transport")
        if transport and transport not in VALID_TRANSPORTS:
            result.add_warning(
                f"{file_path.name}: {server_name}: 不明なtransport: {transport}（stdio/socket）"
            )

        # args のバリデーション
        args = config.get("args")
        if args is not None and not isinstance(args, list):
            result.add_error(f"{file_path.name}: {server_name}: argsは配列が必要")

        # 数値フィールドのバリデーション
        for field in ["startupTimeout", "shutdownTimeout", "maxRestarts"]:
            value = config.get(field)
            if value is not None and not isinstance(value, int | float):
                result.add_error(f"{file_path.name}: {server_name}: {field}は数値が必要")

        # ブールフィールドのバリデーション
        restart_on_crash = config.get("restartOnCrash")
        if restart_on_crash is not None and not isinstance(restart_on_crash, bool):
            result.add_error(f"{file_path.name}: {server_name}: restartOnCrashはブール値が必要")

    return result
