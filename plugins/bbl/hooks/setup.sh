#!/bin/bash
# bblプラグインの初期セットアップ

# 記事出力先ディレクトリ（userConfigのarticlesDirを参照、未設定時はcontent）
ARTICLES_DIR="${CLAUDE_USER_CONFIG_articlesDir:-content}"

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
    mkdir -p "${ARTICLES_DIR}/${category}/${subcategory}"
  done
done

echo "✓ bblプラグインのセットアップが完了しました。"
echo "✓ ディレクトリ構造: ${ARTICLES_DIR}/<カテゴリ>/<サブカテゴリ>/"
