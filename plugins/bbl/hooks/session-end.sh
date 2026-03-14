#!/bin/bash
# セッション終了時にセッション情報をログに記録
# 注意: SessionEndイベントではlast_assistant_messageは利用不可（Stop/SubagentStop専用）
# 代わりにsession_idとtranscript_pathを記録する

input=$(cat)
session_id=$(echo "$input" | jq -r '.session_id // ""')
transcript_path=$(echo "$input" | jq -r '.transcript_path // ""')
timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

if [ -n "$session_id" ]; then
  echo "$timestamp session_end session_id=$session_id transcript=$transcript_path" >> "${CLAUDE_PROJECT_DIR}/.bbl-session.log"
fi
