#!/bin/bash
if ! command -v jq &>/dev/null; then
  echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") [DOC_CHECK_SESSION] (jq not found)" >> /tmp/doc-check-session.log
  exit 0
fi
input=$(cat)
last_message=$(echo "$input" | jq -r '.last_assistant_message // ""' | tr '\n' ' ')

if [ -n "$last_message" ]; then
  echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") [DOC_CHECK_SESSION] $last_message" >> /tmp/doc-check-session.log
fi
