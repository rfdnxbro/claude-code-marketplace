#!/bin/bash
# タスク作成/完了時のログ記録

input=$(cat)
timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
hook_event=$(echo "$input" | jq -r '.hook_event_name // "TaskCompleted"')
task_subject=$(echo "$input" | jq -r '.task_subject // ""')

LOG_DIR="${CLAUDE_PLUGIN_DATA}/logs"
mkdir -p "$LOG_DIR"

if [ "$hook_event" = "TaskCreated" ]; then
  echo "$timestamp [TaskCreated] タスクが作成されました: $task_subject" >> "${LOG_DIR}/session.log"
else
  echo "$timestamp [TaskCompleted] タスクが完了しました: $task_subject" >> "${LOG_DIR}/session.log"
fi

# 必要に応じてエージェントを停止させる条件を追加できる（v2.1.64以降）:
# echo '{"continue": false, "stopReason": "フェーズが完了しました。次のコマンドを実行してください。"}'
exit 0
