"""
.lsp.json のバリデーター
"""

import json
import re
from pathlib import Path

from .base import ValidationResult

# 有効なtransport値
VALID_TRANSPORTS = {"stdio", "socket"}


def validate_lsp_json(file_path: Path, content: str) -> ValidationResult:
    """LSPサーバー設定を検証する"""
    result = ValidationResult()

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        result.add_error(f"{file_path.name}: JSONパースエラー: {e}")
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
            if value is not None and not isinstance(value, (int, float)):
                result.add_error(f"{file_path.name}: {server_name}: {field}は数値が必要")

        # ブールフィールドのバリデーション
        restart_on_crash = config.get("restartOnCrash")
        if restart_on_crash is not None and not isinstance(restart_on_crash, bool):
            result.add_error(f"{file_path.name}: {server_name}: restartOnCrashはブール値が必要")

        # 環境変数の直接記述をチェック
        env = config.get("env", {})
        if isinstance(env, dict):
            _check_env_secrets(result, file_path, server_name, env)

        # loggingConfigのenvもチェック
        logging_config = config.get("loggingConfig", {})
        if isinstance(logging_config, dict):
            logging_env = logging_config.get("env", {})
            if isinstance(logging_env, dict):
                _check_env_secrets(result, file_path, server_name, logging_env)

    return result


def _check_env_secrets(
    result: ValidationResult, file_path: Path, server_name: str, env: dict
) -> None:
    """環境変数に機密情報が直接記述されていないかチェック"""
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
                    result.add_error(
                        f"{file_path.name}: {server_name}: "
                        f"envの{key}に{description}が直接記述。${{{{VAR}}}}形式を使用"
                    )
                    break
            else:
                # 既知パターンに一致しない場合、汎用チェック（警告）
                if len(value) > 20 and re.match(r"^[a-zA-Z0-9_-]+$", value):
                    result.add_warning(
                        f"{file_path.name}: {server_name}: "
                        f"envの{key}に機密情報の可能性。${{{{VAR}}}}形式を使用"
                    )
