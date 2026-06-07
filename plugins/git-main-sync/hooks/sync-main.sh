#!/usr/bin/env bash
# 新規セッション開始時に、git 管理下のリポジトリで main ブランチを最新化する。
#   - 現在ブランチが既定ブランチ (origin/HEAD) と一致 → git pull --ff-only
#   - それ以外                                       → git fetch origin
# 失敗しても継続する (exit 0)。サイレントに動くため、結果は systemMessage で簡潔に通知。

set -u

cat >/dev/null 2>&1 || true

# JSON 文字列値として安全になるよう " と \ をエスケープして出力する。
# 第2引数にセッションタイトルを渡すと hookSpecificOutput.sessionTitle を設定する（v2.1.152以降）。
emit_json() {
  local msg="$1"
  local title="${2:-}"
  msg="${msg//\\/\\\\}"
  msg="${msg//\"/\\\"}"
  if [ -n "$title" ]; then
    title="${title//\\/\\\\}"
    title="${title//\"/\\\"}"
    printf '{"continue":true,"systemMessage":"%s","hookSpecificOutput":{"hookEventName":"SessionStart","sessionTitle":"%s"}}\n' \
      "${msg}" "${title}"
  else
    printf '{"continue":true,"systemMessage":"%s"}\n' "${msg}"
  fi
}

silent_exit() {
  printf '{"continue":true}\n'
  exit 0
}

cwd="${CLAUDE_PROJECT_DIR:-$PWD}"
cd "$cwd" 2>/dev/null || silent_exit

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  silent_exit
fi

if ! git remote get-url origin >/dev/null 2>&1; then
  silent_exit
fi

default_branch="$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's@^origin/@@')"
if [ -z "${default_branch}" ]; then
  default_branch="main"
fi

current_branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)" || silent_exit

repo_name="$(basename "$cwd")"
session_title="${repo_name} (${current_branch})"

if [ "${current_branch}" = "${default_branch}" ]; then
  before="$(git rev-parse HEAD 2>/dev/null)" || silent_exit
  if git pull --ff-only origin "${default_branch}" >/dev/null 2>&1; then
    after="$(git rev-parse HEAD 2>/dev/null)" || after="${before}"
    if [ "${before}" = "${after}" ]; then
      emit_json "[git-main-sync] ${default_branch} は既に最新です" "${session_title}"
    else
      emit_json "[git-main-sync] ${default_branch} を pull で最新化しました" "${session_title}"
    fi
  else
    emit_json "[git-main-sync] ${default_branch} の pull に失敗しました (ローカル変更や非fast-forwardの可能性)" "${session_title}"
  fi
else
  if git fetch origin >/dev/null 2>&1; then
    emit_json "[git-main-sync] origin を fetch しました (現在ブランチ: ${current_branch})" "${session_title}"
  else
    emit_json "[git-main-sync] origin の fetch に失敗しました" "${session_title}"
  fi
fi

exit 0
