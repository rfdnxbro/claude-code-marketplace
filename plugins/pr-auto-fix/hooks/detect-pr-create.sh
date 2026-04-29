#!/usr/bin/env bash
# gh pr create が成功した直後に呼ばれ、出力から PR URL を抽出して watch-targets.json に登録する。
# additionalContext で Claude に auto-fix-pr スキルの起動を促す。

set -euo pipefail

DATA="${CLAUDE_PLUGIN_DATA:-${HOME}/.claude/plugins/data/pr-auto-fix}"
mkdir -p "$DATA"
TARGETS="$DATA/watch-targets.json"

input=$(cat)

exit_code=$(printf '%s' "$input" | jq -r '.tool_response.exit_code // .tool_response.exitCode // 0')
if [ "$exit_code" != "0" ]; then
  exit 0
fi

command=$(printf '%s' "$input" | jq -r '.tool_input.command // ""')
if printf '%s' "$command" | grep -qE -- '--help|--dry-run'; then
  exit 0
fi

output=$(printf '%s' "$input" | jq -r '.tool_response.output // .tool_response.stdout // ""')
pr_url=$(printf '%s' "$output" | grep -oE 'https://github\.com/[^/]+/[^/]+/pull/[0-9]+' | head -n1 || true)
if [ -z "$pr_url" ]; then
  exit 0
fi

if [ -f "$TARGETS" ]; then
  existing=$(cat "$TARGETS")
else
  existing='[]'
fi

if printf '%s' "$existing" | jq -e --arg url "$pr_url" '[.[] | select(.pr_url == $url)] | length > 0' >/dev/null 2>&1; then
  jq -nc \
    --arg url "$pr_url" \
    '{continue: true, hookSpecificOutput: {hookEventName: "PostToolUse", additionalContext: ("pr-auto-fix: PR " + $url + " は既に監視対象に登録済みです。")}}'
  exit 0
fi

repo=$(printf '%s' "$pr_url" | sed -E 's|https://github\.com/([^/]+/[^/]+)/pull/[0-9]+|\1|')
number=$(printf '%s' "$pr_url" | sed -E 's|.*/pull/([0-9]+)|\1|')
registered_at=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

new_entry=$(jq -nc \
  --arg url "$pr_url" \
  --arg repo "$repo" \
  --argjson number "$number" \
  --arg registered_at "$registered_at" \
  '{pr_url: $url, repo: $repo, number: $number, registered_at: $registered_at, last_head_sha: null}')

printf '%s' "$existing" | jq --argjson e "$new_entry" '. + [$e]' > "$TARGETS.tmp"
mv "$TARGETS.tmp" "$TARGETS"

jq -nc \
  --arg url "$pr_url" \
  '{continue: true, hookSpecificOutput: {hookEventName: "PostToolUse", additionalContext: ("pr-auto-fix: PR " + $url + " を監視対象に登録しました。`pr-auto-fix:auto-fix-pr` スキルを起動して CI/レビュー/コンフリクトの自動監視を開始してください。")}}'
