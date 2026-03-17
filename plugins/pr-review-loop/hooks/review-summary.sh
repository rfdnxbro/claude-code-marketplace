#!/bin/bash
LOG_FILE="${CLAUDE_PLUGIN_DATA}/pr-review-loop.log"
if ! command -v jq &>/dev/null; then
  echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") [pr-review-loop] Stop: (jq not found)" >> "$LOG_FILE"
  exit 0
fi
input=$(cat)
timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
last_message=$(echo "$input" | jq -r '.last_assistant_message // ""' | tr '\n' ' ')

if [ -n "$last_message" ]; then
  echo "$timestamp [pr-review-loop] Stop: $last_message" >> "$LOG_FILE"
fi
