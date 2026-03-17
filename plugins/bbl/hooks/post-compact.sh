#!/bin/bash
CONTEXT_FILE="${CLAUDE_PROJECT_DIR}/.bbl-context.yml"

if [[ ! -f "$CONTEXT_FILE" ]]; then
  exit 0
fi

concept=$(grep "^concept:" "$CONTEXT_FILE" | cut -d' ' -f2-)
category=$(grep "^category:" "$CONTEXT_FILE" | cut -d' ' -f2-)
phase=$(grep "^phase:" "$CONTEXT_FILE" | cut -d' ' -f2-)

cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PostCompact",
    "additionalContext": "（コンパクション後）現在作成中の記事: ${concept}（カテゴリ: ${category}）、フェーズ: ${phase}。7セクション構成を継続してください。"
  }
}
EOF
