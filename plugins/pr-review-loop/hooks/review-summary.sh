#!/bin/bash
LOG_FILE="${CLAUDE_PLUGIN_DATA}/pr-review-loop.log"
if ! command -v jq &>/dev/null; then
  echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") [pr-review-loop] Stop: (jq not found)" >> "$LOG_FILE"
  exit 0
fi
input=$(cat)
timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
event_name=$(echo "$input" | jq -r '.hook_event_name // "Stop"')
last_message=$(echo "$input" | jq -r '.last_assistant_message // ""' | tr '\n' ' ')

if [ -n "$last_message" ]; then
  echo "$timestamp [pr-review-loop] $event_name: $last_message" >> "$LOG_FILE"
elif [ "$event_name" = "StopFailure" ]; then
  echo "$timestamp [pr-review-loop] $event_name: (no assistant message)" >> "$LOG_FILE"
fi
