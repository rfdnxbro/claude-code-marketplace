"""
スラッシュコマンドのバリデーター
"""

from pathlib import Path

from .base import ValidationResult, parse_frontmatter


def validate_slash_command(file_path: Path, content: str) -> ValidationResult:
    """スラッシュコマンドを検証する"""
    result = ValidationResult()
    frontmatter, body, yaml_warnings = parse_frontmatter(content)

    # YAML警告を追加
    for w in yaml_warnings:
        result.add_warning(f"{file_path.name}: {w}")

    # descriptionの確認
    if not frontmatter.get("description"):
        # 本文の最初の行がデフォルトになるが、明示的に設定することを推奨
        if body.strip():
            result.add_warning(
                f"{file_path.name}: descriptionが未設定（本文の最初の行がデフォルトで使用される）"
            )
        else:
            result.add_error(f"{file_path.name}: descriptionが未設定で本文も空")

    # allowed-toolsの確認
    allowed_tools = frontmatter.get("allowed-tools", "")
    if allowed_tools:
        # Bash(*)のような広範なワイルドカードを警告
        if "Bash(*)" in str(allowed_tools):
            result.add_warning(
                f"{file_path.name}: allowed-toolsにBash(*)が指定。具体的なパターンを推奨"
            )

    # disable-model-invocationの確認
    disable_model = frontmatter.get("disable-model-invocation", False)
    # 危険そうなキーワードが含まれる場合は警告
    dangerous_keywords = ["deploy", "delete", "drop", "production", "本番"]
    description = frontmatter.get("description", "")
    description_str = str(description) if description else ""
    if any(kw in body.lower() or kw in description_str.lower() for kw in dangerous_keywords):
        if disable_model is not True:
            result.add_warning(
                f"{file_path.name}: 危険な操作の可能性。disable-model-invocation: trueを検討"
            )

    # modelの値チェック（短縮形のみ許可、inheritは不可）
    model = frontmatter.get("model")
    model_str = str(model).strip() if model is not None else ""
    valid_models = {"sonnet", "opus", "haiku"}
    if model_str and model_str not in valid_models:
        result.add_warning(f"{file_path.name}: modelが不正: {model_str}（sonnet/opus/haiku）")

    return result
