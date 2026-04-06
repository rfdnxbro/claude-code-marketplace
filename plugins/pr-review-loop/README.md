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
2. 各コメントを「修正が必要」「スキップ（対応不要）」「判断保留」に分類
3. コメント単位で対応サイクルを実行:
   - **修正が必要** → コードを修正し、コメントに「✅ 対応済み」と返信
   - **スキップ** → コメントに「⏭️ スキップ」と理由を返信
   - **判断保留** → 返信せず、ユーザーに判断を委ねる
4. 修正がある場合はまとめてコミット・プッシュ
5. 全指摘対応完了でループ停止を提案

## 設定（オプション）

以下の設定でプラグインの動作をカスタマイズできます:

| 設定キー | デフォルト | 説明 |
|---------|-----------|------|
| `targetBots` | （空） | 対応対象のbotユーザー名（カンマ区切り）。空の場合は全botが対象 |
| `autoSkipStyleIssues` | `false` | `true` にするとスタイル・フォーマット系の指摘を自動スキップ |

### 設定例

特定のbotのみ対応する場合:

```yaml
targetBots: github-actions[bot],devin-ai-integration[bot]
```

スタイル指摘を自動スキップする場合:

```yaml
autoSkipStyleIssues: true
```
