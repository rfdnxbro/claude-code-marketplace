#!/bin/bash
# サブエージェント完了時のログ記録

input=$(cat)
last_message=$(echo "$input" | jq -r '.last_assistant_message // ""')
timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

if [ -n "$last_message" ]; then
  echo "$timestamp [SubagentStop] $last_message" >> "${CLAUDE_PROJECT_DIR}/.ai-dlc-session.log"
fi

exit 0
