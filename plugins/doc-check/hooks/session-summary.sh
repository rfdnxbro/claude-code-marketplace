#!/bin/bash
input=$(cat)
last_message=$(echo "$input" | jq -r '.last_assistant_message // ""')

if [ -n "$last_message" ]; then
  echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") [DOC_CHECK_SESSION] $last_message" >> /tmp/doc-check-session.log
fi
