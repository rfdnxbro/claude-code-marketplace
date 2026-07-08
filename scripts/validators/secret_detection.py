"""
機密情報（ハードコードされたAPIキー等）の検出

.mcp.json / .lsp.json 内にAPIキーやトークンが直接書かれていないかを
正規表現で検出する共通ヘルパー。
"""

import re
from pathlib import Path

from .base import ValidationResult

# 各パターンは (パターン名, 正規表現) のタプル
# ${VAR} のような環境変数プレースホルダーには決してマッチしないよう、
# `$`や`{`を含まない文字クラスのみを使用する
SECRET_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("OpenAI APIキー", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9]{20,}\b")),
    ("GitHub Token", re.compile(r"\bgh[pous]_[A-Za-z0-9]{20,}\b")),
    ("Slack Token", re.compile(r"\bxox[bap]-[A-Za-z0-9-]{10,}\b")),
    ("AWS Access Key ID", re.compile(r"\bAKIA[A-Z0-9]{16}\b")),
    ("Google APIキー", re.compile(r"\bAIza[A-Za-z0-9_-]{35}\b")),
]


def detect_hardcoded_secrets(result: ValidationResult, file_path: Path, content: str) -> None:
    """
    コンテンツ中にハードコードされた機密情報のパターンがないか検出する

    Args:
        result: 検証結果オブジェクト（検出時にエラーを追加）
        file_path: エラーメッセージ用のファイルパス
        content: 検査対象のファイル内容全体
    """
    for pattern_name, pattern in SECRET_PATTERNS:
        if pattern.search(content):
            result.add_error(
                f"{file_path.name}: {pattern_name}のようなハードコードされた機密情報を"
                "検出しました。${VAR}形式で環境変数から参照してください"
            )
