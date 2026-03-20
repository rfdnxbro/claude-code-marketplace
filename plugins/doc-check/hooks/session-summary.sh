#!/bin/bash
if [ -z "${CLAUDE_PLUGIN_DATA}" ]; then
  exit 0
fi
mkdir -p "${CLAUDE_PLUGIN_DATA}"
LOG_FILE="${CLAUDE_PLUGIN_DATA}/doc-check-session.log"

if ! command -v jq &>/dev/null; then
  echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") [DOC_CHECK_SESSION] (jq not found)" >> "$LOG_FILE"
  exit 0
fi
input=$(cat)
last_message=$(echo "$input" | jq -r '.last_assistant_message // ""' | tr '\n' ' ')

if [ -n "$last_message" ]; then
  echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") [DOC_CHECK_SESSION] $last_message" >> "$LOG_FILE"
fi
