#!/usr/bin/env bash
# pr-auto-fix: Monitor 本体。watch-targets.json を poll し、CI 失敗 / レビュー / コンフリクトを JSON Lines で通知する。

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./pr-state.sh
source "$SCRIPT_DIR/pr-state.sh"
# shellcheck source=./classify-event.sh
source "$SCRIPT_DIR/classify-event.sh"

INTERVAL="${user_config_pollIntervalSec:-${POLL_INTERVAL_SEC:-45}}"
BOT_PATTERN="${user_config_botPattern:-${BOT_PATTERN:-copilot|coderabbit|claude.*review}}"

state_init

if ! command -v gh >/dev/null 2>&1; then
  emit_event "auth_error" '{"reason":"gh CLI not found"}'
fi

backoff_count=0
auth_warned=0

while :; do
  targets=$(state_targets)
  count=$(printf '%s' "$targets" | jq 'length' 2>/dev/null || echo 0)

  if [ "$count" -eq 0 ]; then
    sleep "$INTERVAL"
    continue
  fi

  printf '%s' "$targets" | jq -c '.[]' | while read -r entry; do
    pr_url=$(printf '%s' "$entry" | jq -r '.pr_url')

    if ! meta=$(gh pr view "$pr_url" --json state,mergeable,mergeStateStatus,headRefName,headRefOid 2>/dev/null); then
      backoff_count=$((backoff_count + 1))
      if [ "$auth_warned" -eq 0 ]; then
        emit_event "auth_error" "$(jq -nc --arg url "$pr_url" '{pr: $url, reason: "gh pr view failed"}')"
        auth_warned=1
      fi
      continue
    fi
    backoff_count=0
    auth_warned=0

    state=$(printf '%s' "$meta" | jq -r '.state')
    head_sha=$(printf '%s' "$meta" | jq -r '.headRefOid')
    head_ref=$(printf '%s' "$meta" | jq -r '.headRefName')

    if [ "$state" = "CLOSED" ] || [ "$state" = "MERGED" ]; then
      emit_event "closed" "$(jq -nc --arg url "$pr_url" --arg s "$state" '{pr: $url, state: $s, action: "unwatch"}')"
      state_remove_target "$pr_url"
      continue
    fi

    # CI 失敗
    if checks=$(gh pr checks "$pr_url" --json name,state,conclusion 2>/dev/null); then
      printf '%s' "$checks" | jq -c '.[] | select(.conclusion == "FAILURE" or .conclusion == "TIMED_OUT")' | while read -r check; do
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
      done
    fi

    # レビュー / コメント
    if reviews=$(gh pr view "$pr_url" --json comments,reviews 2>/dev/null); then
      printf '%s' "$reviews" | jq -c '
        ([(.comments // [])[] | {kind:"comment", id:((.id // .databaseId) | tostring), author:(.author.login // .user.login // "unknown"), body:(.body // ""), createdAt:(.createdAt // "")}]
         + [(.reviews // [])[] | {kind:"review", id:((.id // .databaseId) | tostring), author:(.author.login // .user.login // "unknown"), body:(.body // ""), createdAt:(.createdAt // .submittedAt // "")}])[]' \
        | while read -r cmt; do
        author=$(printf '%s' "$cmt" | jq -r '.author')
        cmt_id=$(printf '%s' "$cmt" | jq -r '.id')
        body=$(printf '%s' "$cmt" | jq -r '.body')
        # 完全に空の本文はスキップ（noise 抑制）
        if [ -z "$body" ] || [ "$body" = "null" ]; then
          continue
        fi
        sig="$cmt_id"
        h=$(state_event_hash "$pr_url" "review" "$sig")
        if ! state_seen "$h"; then
          state_mark_seen "$h"
          if printf '%s' "$author" | grep -qiE -- "(${BOT_PATTERN}|\\[bot\\])"; then
            author_kind="bot"
          else
            author_kind="human"
          fi
          excerpt=$(printf '%s' "$body" | head -c 240)
          emit_event "review" "$(jq -nc \
            --arg url "$pr_url" \
            --arg author "$author" \
            --arg kind "$author_kind" \
            --arg cmt_id "$cmt_id" \
            --arg sha "$head_sha" \
            --arg excerpt "$excerpt" \
            --arg sig "$sig" \
            --arg hash "$h" \
            '{pr: $url, author: $author, author_kind: $kind, comment_id: $cmt_id, head_sha: $sha, body_excerpt: $excerpt, signature: $sig, hash: $hash, action: "classify obvious vs judgment, then act"}')"
        fi
      done
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
  done

  sleep "$INTERVAL"
done
