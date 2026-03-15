#!/bin/bash
set -euo pipefail

# リモート環境（Claude Code on the web）のみで実行
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# pre-commitのインストール（--userフラグで権限問題を回避）
if ! command -v pre-commit &> /dev/null; then
  pip install --user pre-commit
  # --userインストール先をPATHに追加
  export PATH="$HOME/.local/bin:$PATH"
fi

cd "$CLAUDE_PROJECT_DIR"

# .pre-commit-config.yamlの存在を確認
if [ ! -f .pre-commit-config.yaml ]; then
  echo "警告: .pre-commit-config.yaml が見つかりません。スキップします。" >&2
  exit 0
fi

# pre-commitのGitフック登録と環境セットアップ
pre-commit install
pre-commit install-hooks
