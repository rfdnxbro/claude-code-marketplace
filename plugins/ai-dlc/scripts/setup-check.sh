#!/bin/bash
# AI-DLC実行に必要なツールのチェック

REQUIRED_TOOLS=("aws" "terraform" "cdk")
MISSING_TOOLS=()

for tool in "${REQUIRED_TOOLS[@]}"; do
  if ! command -v "$tool" &> /dev/null; then
    MISSING_TOOLS+=("$tool")
  fi
done

if [ ${#MISSING_TOOLS[@]} -gt 0 ]; then
  echo "警告: 以下のツールがインストールされていません: ${MISSING_TOOLS[*]}"
  echo "AI-DLCの全機能を利用するには、これらのツールのインストールを検討してください。"
fi

exit 0
