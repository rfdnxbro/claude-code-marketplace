#!/bin/bash
# サブエージェント完了時のログ記録

input=$(cat)
last_message=$(echo "$input" | jq -r '.last_assistant_message // ""')
agent_id=$(echo "$input" | jq -r '.agent_id // ""')
agent_type=$(echo "$input" | jq -r '.agent_type // ""')
timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

if [ -n "$last_message" ]; then
  echo "$timestamp [SubagentStop] agent_id=${agent_id} agent_type=${agent_type} $last_message" >> "${CLAUDE_PROJECT_DIR}/.ai-dlc-session.log"
fi

exit 0
