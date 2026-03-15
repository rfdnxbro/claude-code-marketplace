#!/bin/bash
set -euo pipefail

# リモート環境（Claude Code on the web）のみで実行
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# pre-commitのインストール
if ! command -v pre-commit &> /dev/null; then
  pip install pre-commit
fi

# pre-commitのGitフック登録と環境セットアップ
cd "$CLAUDE_PROJECT_DIR"
pre-commit install
pre-commit install-hooks
