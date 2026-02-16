#!/bin/bash
# AWS環境を検出して追加コンテキストを提供

# アカウントIDから環境を判定
ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text 2>/dev/null)

# EC2インスタンスのタグから環境を検出（オプション）
ENV_TAG=$(aws ec2 describe-instances --query 'Reservations[0].Instances[0].Tags[?Key==`Environment`].Value' --output text 2>/dev/null)

if [[ -z "$ACCOUNT_ID" ]]; then
  ACCOUNT_ID="unknown"
fi

if [[ -z "$ENV_TAG" ]]; then
  ENV_TAG="unknown"
fi

# 本番環境の判定（アカウントIDまたはタグで判定）
if [[ "$ACCOUNT_ID" == "123456789012" ]] || [[ "$ENV_TAG" == "production" ]]; then
  cat <<EOF >&2
Error: 本番環境でのAWS操作は禁止されています
現在の環境: Account=$ACCOUNT_ID, Tag=$ENV_TAG
EOF
  exit 2
fi

# 本番以外の環境では追加コンテキストを提供
cat <<EOF
{
  "continue": true,
  "hookSpecificOutput": {
    "additionalContext": "AWS環境チェック完了。現在の環境: Account=$ACCOUNT_ID, Tag=$ENV_TAG。操作を続行します。"
  }
}
EOF
exit 0
