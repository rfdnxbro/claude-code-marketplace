#!/bin/bash
# bblプラグインの初期セットアップ

# 必要なディレクトリ構造を作成
CATEGORIES=("ヒト" "モノ" "カネ" "思考・志")
SUBCATEGORIES=(
  "組織行動・リーダーシップ"
  "人材マネジメント"
  "マーケティング"
  "経営戦略"
  "アカウンティング"
  "ファイナンス"
  "クリティカルシンキング"
  "ビジネス倫理"
)

for category in "${CATEGORIES[@]}"; do
  for subcategory in "${SUBCATEGORIES[@]}"; do
    mkdir -p "docs/${category}/${subcategory}"
  done
done

echo "✓ bblプラグインのセットアップが完了しました。"
echo "✓ ディレクトリ構造: docs/<カテゴリ>/<サブカテゴリ>/"
