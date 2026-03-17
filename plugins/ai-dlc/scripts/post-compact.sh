#!/bin/bash
# コンパクション後にDLCコンテキストを復元する

LOG_FILE="${CLAUDE_PROJECT_DIR}/.ai-dlc-session.log"
last_task=""
if [[ -f "$LOG_FILE" ]]; then
  last_task=$(tail -1 "$LOG_FILE")
fi

cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PostCompact",
    "additionalContext": "（コンパクション完了）AI-DLCセッションを継続中です。最後の状態: ${last_task}"
  }
}
EOF
