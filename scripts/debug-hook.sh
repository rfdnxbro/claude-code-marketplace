#!/bin/bash
# Web環境でのhook動作検証用デバッグスクリプト
# 全hookイベントからstdin JSONを読み取り、/tmp/claude-hook-debug.log にログ出力する

LOG_FILE="/tmp/claude-hook-debug.log"

# stdinからJSON入力を読み取る
input=$(cat)

# hook_event_nameを取得（jqが使えない環境用にgrepフォールバック）
if command -v jq &> /dev/null; then
  hook_event=$(echo "$input" | jq -r '.hook_event_name // "unknown"')
  tool_name=$(echo "$input" | jq -r '.tool_name // ""')
  session_id=$(echo "$input" | jq -r '.session_id // ""' | head -c 8)
else
  hook_event=$(echo "$input" | grep -o '"hook_event_name":"[^"]*"' | cut -d'"' -f4)
  tool_name=$(echo "$input" | grep -o '"tool_name":"[^"]*"' | cut -d'"' -f4)
  session_id="n/a"
fi

timestamp=$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ" 2>/dev/null || date -u +"%Y-%m-%dT%H:%M:%SZ")

# ツール名がある場合は付加
detail=""
if [ -n "$tool_name" ]; then
  detail=" tool=$tool_name"
fi

echo "[$timestamp] [$hook_event]${detail} session=${session_id}" >> "$LOG_FILE"

exit 0
