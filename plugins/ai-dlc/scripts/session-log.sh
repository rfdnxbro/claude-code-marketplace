#!/bin/bash
# セッション終了時のログ記録（last_assistant_message を活用）

input=$(cat)
last_message=$(echo "$input" | jq -r '.last_assistant_message // ""')
timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

if [ -n "$last_message" ]; then
  echo "$timestamp [Stop] $last_message" >> "${CLAUDE_PROJECT_DIR}/.ai-dlc-session.log"
fi

exit 0
