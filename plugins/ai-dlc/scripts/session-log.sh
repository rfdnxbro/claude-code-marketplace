#!/bin/bash
# セッション終了時のログ記録

input=$(cat)
session_id=$(echo "$input" | jq -r '.session_id // "unknown"')
timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

echo "$timestamp [SessionEnd] session_id=$session_id" >> "${CLAUDE_PROJECT_DIR}/.ai-dlc-session.log"

exit 0
