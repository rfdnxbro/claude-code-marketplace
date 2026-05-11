#!/usr/bin/env bash
# セッション終了時に watch-targets.json から監視中PRを読み出してログに記録する。
# 監視中のPRがある場合は systemMessage でユーザーに次回セッションでの再起動方法を通知する。

DATA="${CLAUDE_PLUGIN_DATA:-${HOME}/.claude/plugins/data/pr-auto-fix}"
TARGETS="$DATA/watch-targets.json"
LOG_FILE="$DATA/session.log"

mkdir -p "$DATA"

if ! command -v jq &>/dev/null; then
  exit 0
fi

input=$(cat)
session_id=$(printf '%s' "$input" | jq -r '.session_id // ""')
event=$(printf '%s' "$input" | jq -r '.hook_event_name // "SessionEnd"')

if [ ! -f "$TARGETS" ]; then
  exit 0
fi

count=$(jq 'length' "$TARGETS" 2>/dev/null || echo 0)
if [ "$count" -eq 0 ]; then
  exit 0
fi

timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
urls=$(jq -r '.[].pr_url' "$TARGETS" | tr '\n' ' ')
echo "$timestamp [$event] session=$session_id watching=$count PRs: $urls" >> "$LOG_FILE"

jq -nc \
  --argjson count "$count" \
  '{continue: true, systemMessage: ("pr-auto-fix: " + ($count | tostring) + "件のPRを監視中にセッションが終了しました。次回セッションで `pr-auto-fix:auto-fix-pr` を起動すると監視が再開されます。")}'
