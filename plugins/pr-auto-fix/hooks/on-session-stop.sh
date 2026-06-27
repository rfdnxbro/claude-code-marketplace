#!/usr/bin/env bash
set -euo pipefail

DATA="${CLAUDE_PLUGIN_DATA:-${HOME}/.claude/plugins/data/pr-auto-fix}"
TARGETS="$DATA/watch-targets.json"

if [ ! -f "$TARGETS" ]; then
  exit 0
fi

count=$(jq 'length' "$TARGETS" 2>/dev/null || echo 0)
if [ "$count" -eq 0 ]; then
  exit 0
fi

jq -nc \
  --argjson n "$count" \
  '{
    "continue": true,
    "hookSpecificOutput": {
      "hookEventName": "Stop",
      "additionalContext": ("pr-auto-fix: " + ($n | tostring) + " 件のPRが監視対象に残っています。次回セッション開始時に `pr-auto-fix:auto-fix-pr` スキルを起動して監視を継続してください。")
    }
  }'
