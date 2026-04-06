#!/bin/bash
# AI-DLC実行に必要なツールのチェック

CLOUD_PROVIDER="${CLAUDE_USER_CONFIG_cloudProvider:-AWS}"

case "$CLOUD_PROVIDER" in
  AWS)   REQUIRED_TOOLS=("aws") ;;
  GCP)   REQUIRED_TOOLS=("gcloud") ;;
  Azure) REQUIRED_TOOLS=("az") ;;
  *)     REQUIRED_TOOLS=() ;;
esac
REQUIRED_TOOLS+=("terraform")

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
