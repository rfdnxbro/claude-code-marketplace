#!/bin/bash
# コンパクション後にPRレビューコンテキストを提供
input=$(cat)
compact_summary=$(echo "$input" | jq -r '.compact_summary // ""')

# セッションログから最新のPRレビュー情報を取得して追加コンテキストを提供
cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PostCompact",
    "additionalContext": "（コンパクション完了）PRレビューセッションを継続中です。レビュー作業を再開してください。"
  }
}
EOF
