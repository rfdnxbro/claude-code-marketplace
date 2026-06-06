#!/usr/bin/env bash
# pr-auto-fix: 通知 JSON Lines を stdout に emit するヘルパー。source して使う。

# 引数: kind, JSON-encoded extra (例: '{"check":"x","head_sha":"y"}')
# 第 2 引数省略時は空オブジェクトとして扱う。
emit_event() {
  local kind="$1"
  local extra="${2:-}"
  if [ -z "$extra" ]; then
    extra='{}'
  fi
  jq -nc \
    --arg plugin "pr-auto-fix" \
    --arg kind "$kind" \
    --argjson extra "$extra" \
    '{plugin: $plugin, kind: $kind} + $extra'
}
