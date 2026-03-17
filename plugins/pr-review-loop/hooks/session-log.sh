#!/bin/bash
LOG_FILE="${CLAUDE_PLUGIN_DATA}/pr-review-loop.log"
if ! command -v jq &>/dev/null; then
  echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") [pr-review-loop] SubagentStop: (jq not found)" >> "$LOG_FILE"
  exit 0
fi
input=$(cat)
timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
last_message=$(echo "$input" | jq -r '.last_assistant_message // ""' | tr '\n' ' ')
echo "$timestamp [pr-review-loop] SubagentStop: $last_message" >> "$LOG_FILE"
