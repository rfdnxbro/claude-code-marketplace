"""
スラッシュコマンドのバリデーター
"""

from pathlib import Path

from .base import ValidationResult, parse_frontmatter


def validate_slash_command(file_path: Path, content: str) -> ValidationResult:
    """スラッシュコマンドを検証する"""
    result = ValidationResult()
    frontmatter, body = parse_frontmatter(content)

    # descriptionの確認
    if not frontmatter.get("description"):
        # 本文の最初の行がデフォルトになるが、明示的に設定することを推奨
        if body.strip():
            result.add_warning(f"{file_path.name}: descriptionが未設定（本文の最初の行がデフォルトで使用される）")
        else:
            result.add_error(f"{file_path.name}: descriptionが未設定で本文も空")

    # allowed-toolsの確認
    allowed_tools = frontmatter.get("allowed-tools", "")
    if allowed_tools:
        # Bash(*)のような広範なワイルドカードを警告
        if "Bash(*)" in allowed_tools:
            result.add_warning(f"{file_path.name}: allowed-toolsに広範なBash(*)が指定されています。より具体的なパターンを推奨")

    # disable-model-invocationの確認
    disable_model = frontmatter.get("disable-model-invocation", "false")
    # 危険そうなキーワードが含まれる場合は警告
    dangerous_keywords = ["deploy", "delete", "drop", "production", "本番"]
    if any(kw in body.lower() or kw in frontmatter.get("description", "").lower() for kw in dangerous_keywords):
        if disable_model.lower() != "true":
            result.add_warning(f"{file_path.name}: 危険な操作を含む可能性があります。disable-model-invocation: trueを検討してください")

    # modelの値チェック
    model = frontmatter.get("model", "")
    if model and not any(m in model for m in ["haiku", "sonnet", "opus"]):
        result.add_warning(f"{file_path.name}: modelの値が不明です: {model}")

    return result
