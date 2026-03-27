#!/usr/bin/env python3
"""
プラグイン検証スクリプト

使用方法:
  1. hookモード（デフォルト）: stdinからJSON形式でhook入力を受け取る
  2. CLIモード: コマンドライン引数でファイルパスを指定
     python validate_plugin.py path/to/file1 path/to/file2 ...
     --strict: 警告もエラーとして扱う
"""

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path

from validators import (
    ValidationResult,
    validate_agent,
    validate_hooks_json,
    validate_lsp_json,
    validate_marketplace_json,
    validate_mcp_json,
    validate_output_style,
    validate_plugin_json,
    validate_readme,
    validate_skill,
    validate_slash_command,
)

# バリデータレジストリ: (判定関数, バリデータ関数) のリスト
# 上から順に評価され、最初にマッチしたバリデータが使用される
_VALIDATOR_REGISTRY: list[
    tuple[Callable[[Path], bool], Callable[[Path, str], ValidationResult]]
] = [
    (lambda p: p.name == "SKILL.md", validate_skill),
    (lambda p: "commands" in p.parts and p.suffix == ".md", validate_slash_command),
    (lambda p: "agents" in p.parts and p.suffix == ".md", validate_agent),
    (lambda p: p.name == "hooks.json", validate_hooks_json),
    (lambda p: p.name == ".mcp.json", validate_mcp_json),
    (lambda p: p.name == ".lsp.json", validate_lsp_json),
    (
        lambda p: p.name == "plugin.json" and ".claude-plugin" in p.parts,
        validate_plugin_json,
    ),
    (
        lambda p: p.name == "marketplace.json" and ".claude-plugin" in p.parts,
        validate_marketplace_json,
    ),
    (lambda p: "output-styles" in p.parts and p.suffix == ".md", validate_output_style),
    (lambda p: p.name == "README.md" and "plugins" in p.parts, validate_readme),
]


def _read_file_content(file_path: Path, result: ValidationResult) -> str | None:
    """ファイルをUTF-8で読み込む。エラー時はNoneを返す"""
    try:
        return file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        result.add_error(f"{file_path.name}: ファイルがUTF-8でエンコードされていません")
        return None
    except FileNotFoundError:
        result.add_error(f"{file_path.name}: ファイルが見つかりません")
        return None
    except Exception as e:
        result.add_error(f"{file_path.name}: ファイル読み込みエラー: {e}")
        return None


def validate_file(file_path: Path) -> ValidationResult:
    """単一ファイルを検証し、結果を返す"""
    result = ValidationResult()

    for matcher, validator in _VALIDATOR_REGISTRY:
        if matcher(file_path):
            content = _read_file_content(file_path, result)
            if content is not None:
                result = validator(file_path, content)
            return result

    return result


def run_cli_mode(args: argparse.Namespace) -> int:
    """CLIモードで複数ファイルを検証"""
    has_errors = False
    has_warnings = False

    for file_path_str in args.files:
        file_path = Path(file_path_str)
        result = validate_file(file_path)

        if result.has_errors():
            has_errors = True
            print(f"❌ {file_path}", file=sys.stderr)
            for error in result.errors:
                print(f"   エラー: {error}", file=sys.stderr)

        if result.warnings:
            has_warnings = True
            if not result.has_errors():
                print(f"⚠️  {file_path}", file=sys.stderr)
            for warning in result.warnings:
                print(f"   警告: {warning}", file=sys.stderr)

    if has_errors:
        return 1
    if has_warnings and args.strict:
        return 1
    return 0


def run_hook_mode() -> int:
    """hookモードでstdinからJSON入力を処理"""
    # stdinからhook入力を取得
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        # JSONでない場合はスキップ
        return 0

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # Edit/Writeツールのみ処理
    if tool_name not in ["Edit", "Write"]:
        return 0

    file_path_str = tool_input.get("file_path", "")
    if not file_path_str:
        return 0

    file_path = Path(file_path_str)
    result = validate_file(file_path)

    # 結果を出力
    if result.has_errors() or result.warnings:
        output = {"continue": True, "systemMessage": result.to_message()}
        print(json.dumps(output, ensure_ascii=False))

    return 0


def main():
    """メインエントリーポイント"""
    parser = argparse.ArgumentParser(description="プラグインファイルを検証する")
    parser.add_argument(
        "files", nargs="*", help="検証するファイルのパス（指定しない場合はhookモード）"
    )
    parser.add_argument("--strict", action="store_true", help="警告もエラーとして扱う")

    args = parser.parse_args()

    if args.files:
        # CLIモード
        sys.exit(run_cli_mode(args))
    else:
        # hookモード
        sys.exit(run_hook_mode())


if __name__ == "__main__":
    main()
