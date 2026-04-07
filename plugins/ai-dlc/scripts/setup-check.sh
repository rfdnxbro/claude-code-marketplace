#!/bin/bash
# AI-DLC実行に必要なツールのチェック

CLOUD_PROVIDER="${CLAUDE_USER_CONFIG_cloudProvider:-AWS}"
CLOUD_PROVIDER=$(echo "$CLOUD_PROVIDER" | tr '[:lower:]' '[:upper:]')

case "$CLOUD_PROVIDER" in
  AWS)   REQUIRED_TOOLS=("aws") ;;
  GCP)   REQUIRED_TOOLS=("gcloud") ;;
  AZURE) REQUIRED_TOOLS=("az") ;;
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

# CDKはオプション（AWSの場合のみ案内）
if [ "$CLOUD_PROVIDER" = "AWS" ] && ! command -v cdk &> /dev/null; then
  echo "情報: AWS CDKがインストールされていません。IaCにCDKを使用する場合はインストールを検討してください。"
fi

exit 0
