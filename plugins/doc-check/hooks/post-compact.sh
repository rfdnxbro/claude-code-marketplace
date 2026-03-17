#!/bin/bash
# コンパクション後にドキュメントチェックコンテキストを提供
LOG_FILE="/tmp/doc-check-session.log"
recent_checks=""
if [[ -f "$LOG_FILE" ]]; then
  recent_checks=$(tail -3 "$LOG_FILE" | tr '\n' '; ')
fi

cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PostCompact",
    "additionalContext": "（コンパクション完了）ドキュメント整合性チェックセッションを継続中。ファイル変更時はREADME.mdやCLAUDE.mdの整合性チェックを続けてください。最近のチェック: ${recent_checks}"
  }
}
EOF
