#!/bin/bash
# セッション終了時のログ記録

input=$(cat)
session_id=$(echo "$input" | jq -r '.session_id // "unknown"')
timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

LOG_DIR="${CLAUDE_PLUGIN_DATA}/logs"
mkdir -p "$LOG_DIR"

echo "$timestamp [SessionEnd] session_id=$session_id" >> "${LOG_DIR}/session.log"

exit 0
