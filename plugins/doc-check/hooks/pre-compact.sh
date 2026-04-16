#!/bin/bash
# コンパクション前にドキュメントチェックの状態をログに記録
# 長時間セッションでコンパクションが発生した場合に、チェック結果が失われないようにする

if [ -z "${CLAUDE_PLUGIN_DATA}" ]; then
  exit 0
fi
mkdir -p "${CLAUDE_PLUGIN_DATA}"
LOG_FILE="${CLAUDE_PLUGIN_DATA}/doc-check-session.log"

if ! command -v jq &>/dev/null; then
  echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") [DOC_CHECK_PRECOMPACT] (jq not found)" >> "$LOG_FILE"
  exit 0
fi

input=$(cat)
session_id=$(echo "$input" | jq -r '.session_id // ""')
trigger=$(echo "$input" | jq -r '.trigger // "unknown"')

if [ -n "$session_id" ]; then
  echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") [DOC_CHECK_PRECOMPACT] trigger=$trigger session_id=$session_id" >> "$LOG_FILE"
fi
