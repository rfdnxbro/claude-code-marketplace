#!/bin/bash
# 危険なコマンドの実行前に警告を表示

# コマンドライン引数から実行予定のコマンドを取得
COMMAND="$ARGUMENTS"

# 追加コンテキストで警告を返す
cat <<EOF
{
  "continue": true,
  "hookSpecificOutput": {
    "additionalContext": "⚠️ 警告: 破壊的な操作を実行しようとしています。コマンド: $COMMAND\n実行前に影響範囲を十分に確認してください。"
  }
}
EOF
exit 0
