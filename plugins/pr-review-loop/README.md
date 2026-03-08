# pr-review-loop

## 概要

PRのbotレビューコメント（Devin、Claude Code等）を定期的に確認し、妥当な指摘を自動修正するスラッシュコマンドを提供するプラグインです。
`/loop` と組み合わせることで、レビュー指摘の確認→修正→プッシュのサイクルを自動化できます。

## インストール

マーケットプレイス経由:

```bash
claude plugin install --marketplace ./path/to/claude-code-marketplace pr-review-loop
```

ローカルで直接指定する場合:

```bash
claude plugin install ./plugins/pr-review-loop
```

## 使い方

### 単発実行

```text
/pr-review-loop:resolve-reviews 42
```

PR #42 のbotレビューコメントを確認し、妥当な指摘を修正してコミット・プッシュします。

### 定期実行（推奨）

```text
/loop 3m /pr-review-loop:resolve-reviews 42
```

3分ごとにbotコメントを確認し、未対応の指摘がなくなるまで自動で修正を繰り返します。

### 動作フロー

1. `gh api` でPRのbotレビューコメントを取得（`user.type == "Bot"` で全bot対象）
2. 指摘を「修正が必要」「対応不要」「判断保留」に分類
3. 妥当な指摘についてコードを修正
4. 変更をコミット・プッシュ
5. 全指摘対応完了でループ停止を提案
