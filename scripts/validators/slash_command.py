"""
スラッシュコマンドのバリデーター
"""

from pathlib import Path

from .base import (
    WARNING_BROAD_BASH_WILDCARD,
    WARNING_DANGEROUS_OPERATION,
    ValidationResult,
    get_disabled_warnings,
    parse_frontmatter,
)


def validate_slash_command(file_path: Path, content: str) -> ValidationResult:
    """スラッシュコマンドを検証する"""
    result = ValidationResult()
    frontmatter, body, yaml_warnings = parse_frontmatter(content)
    disabled_warnings = get_disabled_warnings(content)

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

    # allowed-toolsの確認（リスト形式対応）
    allowed_tools = frontmatter.get("allowed-tools")
    if allowed_tools is not None:
        # リスト形式または文字列形式をチェック
        tools_str = ""
        if isinstance(allowed_tools, list):
            tools_str = ", ".join(str(t) for t in allowed_tools)
        else:
            tools_str = str(allowed_tools)

        # Bash(*)のような広範なワイルドカードを警告
        if "Bash(*)" in tools_str:
            if WARNING_BROAD_BASH_WILDCARD not in disabled_warnings:
                result.add_warning(
                    f"{file_path.name}: allowed-toolsにBash(*)が指定。具体的なパターンを推奨"
                )

    # contextの確認（forkのみサポート、省略時はメインコンテキスト）
    context = frontmatter.get("context")
    if context is not None:
        context_str = str(context) if context else ""
        if context_str and context_str != "fork":
            result.add_error(
                f"{file_path.name}: contextの値が不正です: {context_str}（forkのみ有効）"
            )

    # agentの確認（空でない文字列）
    agent = frontmatter.get("agent")
    if agent is not None:
        agent_str = str(agent) if agent else ""
        if not agent_str:
            result.add_error(f"{file_path.name}: agentは空でない文字列が必要です")

    # disable-model-invocationの確認
    disable_model = frontmatter.get("disable-model-invocation", False)
    # 危険そうなキーワードが含まれる場合は警告
    dangerous_keywords = ["deploy", "delete", "drop", "production", "本番"]
    description = frontmatter.get("description", "")
    description_str = str(description) if description else ""
    if any(kw in body.lower() or kw in description_str.lower() for kw in dangerous_keywords):
        if disable_model is not True:
            if WARNING_DANGEROUS_OPERATION not in disabled_warnings:
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
