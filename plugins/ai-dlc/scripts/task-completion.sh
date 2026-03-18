#!/bin/bash
# タスク完了時のログ記録

input=$(cat)
timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

LOG_DIR="${CLAUDE_PLUGIN_DATA}/logs"
mkdir -p "$LOG_DIR"

echo "$timestamp [TaskCompleted] タスクが完了しました。" >> "${LOG_DIR}/session.log"

# 必要に応じてエージェントを停止させる条件を追加できる（v2.1.64以降）:
# echo '{"continue": false, "stopReason": "フェーズが完了しました。次のコマンドを実行してください。"}'
exit 0
