#!/bin/bash
# サブエージェント完了時のログ記録

input=$(cat)
last_message=$(echo "$input" | jq -r '.last_assistant_message // ""')
timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

LOG_DIR="${CLAUDE_PLUGIN_DATA}/logs"
mkdir -p "$LOG_DIR"

if [ -n "$last_message" ]; then
  echo "$timestamp [SubagentStop] $last_message" >> "${LOG_DIR}/session.log"
fi

exit 0
