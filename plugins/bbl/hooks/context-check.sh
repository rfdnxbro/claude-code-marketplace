#!/bin/bash
# .bbl-context.ymlからコンテキスト情報を読み取り、additionalContextとして提供

if [[ ! -f ".bbl-context.yml" ]]; then
  echo '{"continue": true}'
  exit 0
fi

concept=$(grep "^concept:" .bbl-context.yml | cut -d' ' -f2-)
category=$(grep "^category:" .bbl-context.yml | cut -d' ' -f2-)
phase=$(grep "^phase:" .bbl-context.yml | cut -d' ' -f2-)

if [[ -z "$phase" ]]; then
  echo "Warning: phase フィールドが不正です。.bbl-context.yml を確認してください。" >&2
  echo '{"continue": true}'
  exit 0
fi

cat <<EOF
{
  "continue": true,
  "hookSpecificOutput": {
    "additionalContext": "📝 記事作成中: ${concept} (カテゴリ: ${category})\n7セクション構成を遵守してください。\n現在のフェーズ: ${phase}"
  }
}
EOF
