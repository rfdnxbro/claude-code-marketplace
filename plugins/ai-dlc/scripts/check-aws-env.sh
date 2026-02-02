#!/bin/bash
# AWS環境を検出して追加コンテキストを提供

ENV=$(aws sts get-caller-identity --query 'Account' --output text 2>/dev/null)

if [[ "$ENV" == "123456789012" ]]; then  # 本番アカウントID（要カスタマイズ）
  cat <<EOF
{
  "continue": true,
  "hookSpecificOutput": {
    "additionalContext": "⚠️ 注意: 本番環境（Account: $ENV）での操作です。AWSウェルアーキテクトフレームワークの6つの柱を遵守してください。"
  }
}
EOF
else
  cat <<EOF
{
  "continue": true,
  "hookSpecificOutput": {
    "additionalContext": "開発環境（Account: $ENV）での操作です。"
  }
}
EOF
fi
