#!/usr/bin/env bash
# 新規セッション開始時に、git 管理下のリポジトリで main ブランチを最新化する。
#   - 現在ブランチが既定ブランチ (origin/HEAD) と一致 → git pull --ff-only
#   - それ以外                                       → git fetch origin
# 失敗しても継続する (exit 0)。サイレントに動くため、結果は systemMessage で簡潔に通知。

set -u

cat >/dev/null 2>&1 || true

emit_json() {
  python3 - "$1" <<'PY'
import json, sys
print(json.dumps({"continue": True, "systemMessage": sys.argv[1]}))
PY
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

if [ "${current_branch}" = "${default_branch}" ]; then
  if output="$(git pull --ff-only origin "${default_branch}" 2>&1)"; then
    if printf '%s' "${output}" | grep -q "Already up to date"; then
      emit_json "[git-main-sync] ${default_branch} は既に最新です"
    else
      emit_json "[git-main-sync] ${default_branch} を pull で最新化しました"
    fi
  else
    emit_json "[git-main-sync] ${default_branch} の pull に失敗しました (ローカル変更や非fast-forwardの可能性)"
  fi
else
  if git fetch origin >/dev/null 2>&1; then
    emit_json "[git-main-sync] origin を fetch しました (現在ブランチ: ${current_branch})"
  else
    emit_json "[git-main-sync] origin の fetch に失敗しました"
  fi
fi

exit 0
