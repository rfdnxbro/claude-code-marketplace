#!/bin/bash
# セッション終了時にセッション情報をログに記録
# 注意: SessionEnd/StopFailureイベントではlast_assistant_messageは利用不可（Stop/SubagentStop専用）
# 代わりにsession_idとtranscript_pathを記録する

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
session_id=$(echo "$input" | jq -r '.session_id // ""')
transcript_path=$(echo "$input" | jq -r '.transcript_path // ""')
event_name=$(echo "$input" | jq -r '.hook_event_name // "SessionEnd"')

if [ -n "$session_id" ]; then
  echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") [DOC_CHECK_SESSION] $event_name session_id=$session_id transcript=$transcript_path" >> "$LOG_FILE"
fi
