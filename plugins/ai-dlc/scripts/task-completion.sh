#!/bin/bash
# タスク完了時のログ記録

timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
echo "$timestamp [TaskCompleted] タスクが完了しました。" >> "${CLAUDE_PROJECT_DIR}/.ai-dlc-session.log"

exit 0
