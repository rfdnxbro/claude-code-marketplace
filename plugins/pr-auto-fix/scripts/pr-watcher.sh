#!/usr/bin/env bash
# pr-auto-fix: Monitor 本体。watch-targets.json を poll し、CI 失敗 / レビュー / コンフリクトを JSON Lines で通知する。
#
# 引数（monitors.json から渡す）:
#   $1: pollIntervalSec  デフォルト 45
#   $2: botPattern       デフォルト "copilot|coderabbit|claude.*review"
#
# `${user_config.<key>}` 構文は monitors.json の command 文字列内でしか展開されないため、
# このスクリプト内では位置引数として受け取る。

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./pr-state.sh
source "$SCRIPT_DIR/pr-state.sh"
# shellcheck source=./emit-event.sh
source "$SCRIPT_DIR/emit-event.sh"

INTERVAL="${1:-45}"
BOT_PATTERN="${2:-copilot|coderabbit|claude.*review}"
EMPTY_TARGET_EXIT_CYCLES="${PR_AUTO_FIX_EMPTY_TARGET_EXIT_CYCLES:-3}"

state_init

if ! command -v gh >/dev/null 2>&1; then
  emit_event "auth_error" '{"reason":"gh CLI not found","action":"install gh CLI and re-enable plugin"}'
  exit 1
fi
if ! command -v jq >/dev/null 2>&1; then
  emit_event "auth_error" '{"reason":"jq not found","action":"install jq and re-enable plugin"}'
  exit 1
fi

# PR URL → owner / repo / number に分解
pr_split() {
  local url="$1"
  printf '%s' "$url" | sed -E 's|https://github\.com/([^/]+)/([^/]+)/pull/([0-9]+).*|\1 \2 \3|'
}

# 1 件のレビューコメント（PR トップレベル / インライン共通）を通知。
# 引数: source, pr_url, head_sha, comment_id, author, body, path, line
# source: "issue_comment" | "review" | "inline"（GitHub は各種別で別 ID シーケンスを
# 使うため、prefix を付けないと数値衝突時に通知が落ちる可能性がある）
emit_review_one() {
  local source="$1" pr_url="$2" head_sha="$3" cmt_id="$4" author="$5" body="$6" path="$7" line="$8"
  local sig h author_kind excerpt

  if [ -z "$body" ] || [ "$body" = "null" ]; then
    return 0
  fi

  sig="${source}:${cmt_id}"
  h=$(state_event_hash "$pr_url" "review" "$sig")
  if state_seen "$h"; then
    return 0
  fi
  state_mark_seen "$h"

  if printf '%s' "$author" | grep -qiE -- "(${BOT_PATTERN}|\\[bot\\])"; then
    author_kind="bot"
  else
    author_kind="human"
  fi
  excerpt=$(printf '%s' "$body" | jq -Rs -r '.[0:240]')

  emit_event "review" "$(jq -nc \
    --arg url "$pr_url" \
    --arg author "$author" \
    --arg kind "$author_kind" \
    --arg source "$source" \
    --arg cmt_id "$cmt_id" \
    --arg sha "$head_sha" \
    --arg path "$path" \
    --arg line "$line" \
    --arg excerpt "$excerpt" \
    --arg sig "$sig" \
    --arg hash "$h" \
    '{pr: $url, author: $author, author_kind: $kind, comment_source: $source, comment_id: $cmt_id, head_sha: $sha, path: $path, line: $line, body_excerpt: $excerpt, signature: $sig, hash: $hash, action: "classify obvious vs judgment, then act"}')"
}

auth_warned=0
empty_target_cycles=0

while :; do
  targets=$(state_targets)
  count=$(printf '%s' "$targets" | jq 'length' 2>/dev/null || echo 0)

  if [ "$count" -eq 0 ]; then
    empty_target_cycles=$((empty_target_cycles + 1))
    if [ "$empty_target_cycles" -ge "$EMPTY_TARGET_EXIT_CYCLES" ]; then
      exit 0
    fi
    sleep "$INTERVAL"
    continue
  fi
  empty_target_cycles=0

  # process substitution で subshell 化を回避し、auth_warned をメインループに伝播させる
  while read -r entry; do
    pr_url=$(printf '%s' "$entry" | jq -r '.pr_url')
    read -r owner repo number <<< "$(pr_split "$pr_url")"

    if ! meta=$(gh pr view "$pr_url" --json state,mergeable,mergeStateStatus,headRefName,headRefOid 2>/dev/null); then
      if [ "$auth_warned" -eq 0 ]; then
        emit_event "auth_error" "$(jq -nc --arg url "$pr_url" '{pr: $url, reason: "gh pr view failed"}')"
        auth_warned=1
      fi
      continue
    fi
    auth_warned=0

    state=$(printf '%s' "$meta" | jq -r '.state')
    head_sha=$(printf '%s' "$meta" | jq -r '.headRefOid')
    head_ref=$(printf '%s' "$meta" | jq -r '.headRefName')

    if [ "$state" = "CLOSED" ] || [ "$state" = "MERGED" ]; then
      emit_event "closed" "$(jq -nc --arg url "$pr_url" --arg s "$state" '{pr: $url, state: $s, action: "unwatch"}')"
      state_remove_target "$pr_url"
      continue
    fi

    # CI 失敗（gh pr checks の --json は `bucket` を返す: pass/fail/pending/skipping/cancel）
    if checks=$(gh pr checks "$pr_url" --json name,state,bucket 2>/dev/null); then
      while read -r check; do
        check_name=$(printf '%s' "$check" | jq -r '.name')
        sig="${check_name}|${head_sha}"
        h=$(state_event_hash "$pr_url" "ci_failure" "$sig")
        if ! state_seen "$h"; then
          state_mark_seen "$h"
          emit_event "ci_failure" "$(jq -nc \
            --arg url "$pr_url" \
            --arg check "$check_name" \
            --arg sha "$head_sha" \
            --arg ref "$head_ref" \
            --arg sig "$sig" \
            --arg hash "$h" \
            '{pr: $url, check: $check, head_sha: $sha, head_ref: $ref, signature: $sig, hash: $hash, action: "invoke pr-auto-fixer agent"}')"
        fi
      done < <(printf '%s' "$checks" | jq -c '.[] | select(.bucket == "fail")')
    fi

    # PR トップレベルコメント (issue comment)。--paginate --slurp で全ページを処理する。
    if [ -n "$owner" ] && [ -n "$repo" ] && [ -n "$number" ]; then
      if issue_comments=$(gh api "repos/${owner}/${repo}/issues/${number}/comments" --paginate --slurp 2>/dev/null); then
        while read -r cmt; do
          cmt_id=$(printf '%s' "$cmt" | jq -r '.id')
          author=$(printf '%s' "$cmt" | jq -r '.author')
          body=$(printf '%s' "$cmt" | jq -r '.body')
          emit_review_one "issue_comment" "$pr_url" "$head_sha" "$cmt_id" "$author" "$body" "" ""
        done < <(printf '%s' "$issue_comments" | jq -c '
          .[][]? | {id:(.id | tostring), author:(.user.login // "unknown"), body:(.body // "")}')
      fi

      if reviews=$(gh api "repos/${owner}/${repo}/pulls/${number}/reviews" --paginate --slurp 2>/dev/null); then
        while read -r cmt; do
          cmt_id=$(printf '%s' "$cmt" | jq -r '.id')
          author=$(printf '%s' "$cmt" | jq -r '.author')
          body=$(printf '%s' "$cmt" | jq -r '.body')
          emit_review_one "review" "$pr_url" "$head_sha" "$cmt_id" "$author" "$body" "" ""
        done < <(printf '%s' "$reviews" | jq -c '
          .[][]? | {id:(.id | tostring), author:(.user.login // "unknown"), body:(.body // "")}')
      fi
    fi

    # PR インライン review コメント（line-level）
    if [ -n "$owner" ] && [ -n "$repo" ] && [ -n "$number" ]; then
      if inline=$(gh api "repos/${owner}/${repo}/pulls/${number}/comments" --paginate --slurp 2>/dev/null); then
        while read -r cmt; do
          cmt_id=$(printf '%s' "$cmt" | jq -r '.id')
          author=$(printf '%s' "$cmt" | jq -r '.author')
          body=$(printf '%s' "$cmt" | jq -r '.body')
          path=$(printf '%s' "$cmt" | jq -r '.path')
          line=$(printf '%s' "$cmt" | jq -r '.line')
          emit_review_one "inline" "$pr_url" "$head_sha" "$cmt_id" "$author" "$body" "$path" "$line"
        done < <(printf '%s' "$inline" | jq -c '
          .[][]? | {id:(.id | tostring), author:(.user.login // "unknown"), body:(.body // ""), path:(.path // ""), line:((.line // .original_line // "") | tostring)}')
      fi
    fi

    # コンフリクト
    merge_state=$(printf '%s' "$meta" | jq -r '.mergeStateStatus')
    mergeable=$(printf '%s' "$meta" | jq -r '.mergeable')
    if [ "$merge_state" = "DIRTY" ] || [ "$mergeable" = "CONFLICTING" ]; then
      sig="${merge_state}|${head_sha}"
      h=$(state_event_hash "$pr_url" "conflict" "$sig")
      if ! state_seen "$h"; then
        state_mark_seen "$h"
        emit_event "conflict" "$(jq -nc \
          --arg url "$pr_url" \
          --arg ms "$merge_state" \
          --arg sha "$head_sha" \
          --arg sig "$sig" \
          --arg hash "$h" \
          '{pr: $url, merge_state: $ms, head_sha: $sha, signature: $sig, hash: $hash, action: "try rebase, escalate if non-trivial"}')"
      fi
    fi
  done < <(printf '%s' "$targets" | jq -c '.[]')

  sleep "$INTERVAL"
done
