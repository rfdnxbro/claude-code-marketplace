"""
スラッシュコマンドのバリデーター
"""

from pathlib import Path

from .base import (
    WARNING_DANGEROUS_OPERATION,
    MarkdownValidationContext,
    ValidationResult,
    coerce_str,
    validate_agent_ref_field,
    validate_allowed_tools_field,
    validate_context_field,
    validate_effort_field,
    validate_enum_field,
)


def validate_slash_command(file_path: Path, content: str) -> ValidationResult:
    """スラッシュコマンドを検証する"""
    ctx = MarkdownValidationContext(file_path, content)
    result = ctx.result
    frontmatter = ctx.frontmatter

    # descriptionの確認
    if not frontmatter.get("description"):
        # 本文の最初の行がデフォルトになるが、明示的に設定することを推奨
        if ctx.body.strip():
            result.add_warning(
                f"{file_path.name}: descriptionが未設定（本文の最初の行がデフォルトで使用される）"
            )
        else:
            result.add_error(f"{file_path.name}: descriptionが未設定で本文も空")

    # argument-hintの確認（文字列型）
    argument_hint = frontmatter.get("argument-hint")
    if argument_hint is not None:
        if not isinstance(argument_hint, str) or not argument_hint.strip():
            result.add_warning(f"{file_path.name}: argument-hintは空でない文字列が必要です")

    # allowed-toolsの確認
    validate_allowed_tools_field(frontmatter, file_path, result, ctx.disabled_warnings)

    # contextの確認
    validate_context_field(frontmatter, file_path, result)

    # agentの確認
    validate_agent_ref_field(frontmatter, file_path, result)

    # disable-model-invocationの確認
    disable_model = frontmatter.get("disable-model-invocation", False)
    # 危険そうなキーワードが含まれる場合は警告
    dangerous_keywords = ["deploy", "delete", "drop", "production", "本番"]
    description_str = coerce_str(frontmatter.get("description", ""))
    if any(kw in ctx.body.lower() or kw in description_str.lower() for kw in dangerous_keywords):
        if disable_model is not True:
            if WARNING_DANGEROUS_OPERATION not in ctx.disabled_warnings:
                result.add_warning(
                    f"{file_path.name}: 危険な操作の可能性。disable-model-invocation: trueを検討"
                )

    # modelの値チェック（短縮形のみ許可、inheritは不可）
    validate_enum_field(
        frontmatter,
        "model",
        ["sonnet", "opus", "haiku"],
        file_path,
        result,
        level="warning",
        label="sonnet/opus/haiku",
    )

    # effortの確認
    validate_effort_field(frontmatter, file_path, result)

    return result
