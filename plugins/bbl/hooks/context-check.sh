#!/bin/bash
# .bbl-context.ymlからコンテキスト情報を読み取り、additionalContextとして提供

if [[ -f ".bbl-context.yml" ]]; then
  concept=$(grep "^concept:" .bbl-context.yml | cut -d' ' -f2-)
  category=$(grep "^category:" .bbl-context.yml | cut -d' ' -f2-)

  cat <<EOF
{
  "continue": true,
  "hookSpecificOutput": {
    "additionalContext": "📝 記事作成中: ${concept} (カテゴリ: ${category})\n7セクション構成を遵守してください。"
  }
}
EOF
else
  echo '{"continue": true}'
fi
