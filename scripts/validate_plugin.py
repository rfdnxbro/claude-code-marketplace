#!/usr/bin/env python3
"""
プラグイン検証スクリプト
ファイル編集後にhookで呼び出され、プラグインのベストプラクティスを検証する
"""

import json
import sys
from pathlib import Path

from validators import (
    ValidationResult,
    validate_slash_command,
    validate_agent,
    validate_skill,
    validate_hooks_json,
    validate_mcp_json,
    validate_plugin_json,
)


def main():
    # stdinからhook入力を取得
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        # JSONでない場合はスキップ
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # Edit/Writeツールのみ処理
    if tool_name not in ["Edit", "Write"]:
        sys.exit(0)

    file_path_str = tool_input.get("file_path", "")
    if not file_path_str:
        sys.exit(0)

    file_path = Path(file_path_str)
    result = ValidationResult()

    # パスベースでバリデーターを選択
    path_parts = file_path.parts

    def read_file_content(path: Path) -> str | None:
        """ファイルをUTF-8で読み込む。エラー時はNoneを返す"""
        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            result.add_error(f"{path.name}: ファイルがUTF-8でエンコードされていません")
            return None
        except FileNotFoundError:
            result.add_error(f"{path.name}: ファイルが見つかりません")
            return None
        except Exception as e:
            result.add_error(f"{path.name}: ファイル読み込みエラー: {e}")
            return None

    if file_path.name == "SKILL.md":
        # スキルファイル
        content = read_file_content(file_path)
        if content is not None:
            result = validate_skill(file_path, content)
    elif "commands" in path_parts and file_path.suffix == ".md":
        # スラッシュコマンド
        content = read_file_content(file_path)
        if content is not None:
            result = validate_slash_command(file_path, content)
    elif "agents" in path_parts and file_path.suffix == ".md":
        # サブエージェント
        content = read_file_content(file_path)
        if content is not None:
            result = validate_agent(file_path, content)
    elif file_path.name == "hooks.json":
        # hooks設定
        content = read_file_content(file_path)
        if content is not None:
            result = validate_hooks_json(file_path, content)
    elif file_path.name == ".mcp.json":
        # MCP設定
        content = read_file_content(file_path)
        if content is not None:
            result = validate_mcp_json(file_path, content)
    elif file_path.name == "plugin.json" and ".claude-plugin" in path_parts:
        # プラグインマニフェスト
        content = read_file_content(file_path)
        if content is not None:
            result = validate_plugin_json(file_path, content)
    else:
        # 対象外ファイル
        sys.exit(0)

    # 結果を出力
    if result.has_errors() or result.warnings:
        output = {
            "continue": True,
            "systemMessage": result.to_message()
        }
        print(json.dumps(output, ensure_ascii=False))

    sys.exit(0)


if __name__ == "__main__":
    main()
