#!/bin/bash
# セッション終了時に最後のアシスタントメッセージをログに記録

input=$(cat)
last_message=$(echo "$input" | jq -r '.last_assistant_message // ""')
timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

if [ -n "$last_message" ]; then
  echo "$timestamp $last_message" >> "${CLAUDE_PROJECT_DIR}/.bbl-session.log"
fi
