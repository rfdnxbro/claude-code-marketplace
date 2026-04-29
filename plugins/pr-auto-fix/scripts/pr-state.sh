#!/usr/bin/env bash
# pr-auto-fix: state ファイルへの read/write 共通関数。source して使う。

DATA_DIR="${CLAUDE_PLUGIN_DATA:-${HOME}/.claude/plugins/data/pr-auto-fix}"
mkdir -p "$DATA_DIR"

WATCH_TARGETS_FILE="$DATA_DIR/watch-targets.json"
SEEN_FILE="$DATA_DIR/seen.json"
ATTEMPTS_FILE="$DATA_DIR/attempts.json"
ESCALATIONS_FILE="$DATA_DIR/escalations.json"

state_init() {
  [ -f "$WATCH_TARGETS_FILE" ] || echo '[]' > "$WATCH_TARGETS_FILE"
  [ -f "$SEEN_FILE" ] || echo '[]' > "$SEEN_FILE"
  [ -f "$ATTEMPTS_FILE" ] || echo '{}' > "$ATTEMPTS_FILE"
  [ -f "$ESCALATIONS_FILE" ] || echo '[]' > "$ESCALATIONS_FILE"
}

state_targets() {
  cat "$WATCH_TARGETS_FILE" 2>/dev/null || echo '[]'
}

state_remove_target() {
  local pr_url="$1"
  jq --arg u "$pr_url" 'map(select(.pr_url != $u))' "$WATCH_TARGETS_FILE" > "$WATCH_TARGETS_FILE.tmp" \
    && mv "$WATCH_TARGETS_FILE.tmp" "$WATCH_TARGETS_FILE"
}

# 引数: pr_url, kind, signature → sha256 先頭16文字
state_event_hash() {
  local pr_url="$1" kind="$2" signature="$3"
  if command -v shasum >/dev/null 2>&1; then
    printf '%s|%s|%s' "$pr_url" "$kind" "$signature" | shasum -a 256 | cut -c1-16
  else
    printf '%s|%s|%s' "$pr_url" "$kind" "$signature" | sha256sum | cut -c1-16
  fi
}

state_seen() {
  local h="$1"
  jq -e --arg h "$h" 'index($h) != null' "$SEEN_FILE" >/dev/null 2>&1
}

state_mark_seen() {
  local h="$1"
  jq --arg h "$h" '. + [$h] | unique' "$SEEN_FILE" > "$SEEN_FILE.tmp" \
    && mv "$SEEN_FILE.tmp" "$SEEN_FILE"
}

# transient な失敗（現ブランチ不一致 / dirty worktree など、状況が変わったら再試行したい）
# の場合に、Agent から呼んで seen.json から自分の hash を削除する。
# これにより次回 poll で同じ通知が再発火する。
state_unmark_seen() {
  local h="$1"
  jq --arg h "$h" 'map(select(. != $h))' "$SEEN_FILE" > "$SEEN_FILE.tmp" \
    && mv "$SEEN_FILE.tmp" "$SEEN_FILE"
}
