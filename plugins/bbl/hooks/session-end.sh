#!/bin/bash
# セッション終了時にセッション情報をログに記録
# 注意: SessionEnd/StopFailureイベントではlast_assistant_messageは利用不可（Stop/SubagentStop専用）
# 代わりにsession_idとtranscript_pathを記録する

input=$(cat)
session_id=$(echo "$input" | jq -r '.session_id // ""')
transcript_path=$(echo "$input" | jq -r '.transcript_path // ""')
event_name=$(echo "$input" | jq -r '.hook_event_name // "session_end"')
timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

if [ -n "${CLAUDE_PLUGIN_DATA}" ] && [ -n "$session_id" ]; then
  mkdir -p "${CLAUDE_PLUGIN_DATA}"
  echo "$timestamp $event_name session_id=$session_id transcript=$transcript_path" >> "${CLAUDE_PLUGIN_DATA}/bbl-session.log"
fi
