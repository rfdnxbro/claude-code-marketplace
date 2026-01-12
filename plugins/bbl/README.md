# bbl (Business Basic Learning) プラグイン

ビジネス基礎知識学習教材の記事作成を支援するClaude Codeプラグインです。

## 概要

このプラグインは、ビジネス基礎知識の学習記事を効率的に作成するためのワークフローを提供します。ブレインストーミングから記事作成、レビューまでの一連の流れをサポートします。

## インストール

```bash
claude plugins:install bbl@custom-marketplace
```

## 使い方

1. `/bbl:brainstorm [概念名]` で概念についてブレインストーミングを開始
2. `/bbl:create-article` でアウトラインに基づいて記事を作成
3. `/bbl:review-article` で品質チェックと改善提案を実施

## ワークフロー

```mermaid
flowchart LR
    A["/bbl:brainstorm"] --> B["/bbl:create-article"]
    B --> C["/bbl:review-article"]
    C -->|修正が必要| B
    C -->|公開可能| D[完了]
```

### 1. ブレインストーミング

```bash
/bbl:brainstorm 心理的安全性
```

概念について対話を通じて内容を深掘りし、アウトラインを作成します。

- カテゴリ・サブカテゴリの決定
- 内容の深掘り（定義、重要性、理論、実務活用）
- アウトラインの作成
- `.bbl-context.yml` への状態保存

### 2. 記事作成

```bash
/bbl:create-article
```

アウトラインに基づいて7セクション構成の記事を作成します。

- 導入問題（実務シナリオベース）
- 考えるポイント
- 解説
- 詳細（Mermaid図を含む）
- 具体例（実在企業の事例）
- 関連概念
- 参考文献

### 3. レビュー

```bash
/bbl:review-article
```

記事の品質チェックと改善提案を行います。

- 構造チェック（7セクションの完備）
- 導入問題の品質
- 内容の正確性と明確さ
- 視覚化（Mermaid図）
- 参考文献の信頼性

## コマンド一覧

| コマンド | 説明 |
|---------|------|
| `/bbl:brainstorm [概念名]` | 概念についてブレインストーミングを実施 |
| `/bbl:create-article` | アウトラインに基づいて記事を作成 |
| `/bbl:review-article` | 記事の品質チェックと改善提案 |

## カテゴリ構成

記事は以下の4カテゴリ・8サブカテゴリで整理されます。

| カテゴリ | サブカテゴリ |
|---------|-------------|
| ヒト | 組織行動・リーダーシップ、人材マネジメント |
| モノ | マーケティング、経営戦略 |
| カネ | アカウンティング、ファイナンス |
| 思考・志 | クリティカルシンキング、ビジネス倫理 |

## 出力先

記事は以下のパスに配置されます：

```text
docs/<カテゴリ>/<サブカテゴリ>/<概念名>.md
```

例：
- `docs/ヒト/組織行動・リーダーシップ/心理的安全性.md`
- `docs/カネ/ファイナンス/NPV.md`

## 状態管理

プラグインは `.bbl-context.yml` ファイルで作業状態を管理します。

### phaseの遷移フロー

```
outline_created → article_created → completed
     ↑                    ↑
     |                    |
  brainstorm          create-article      review-article
```

### phaseの値と意味

| phase | 説明 | 対応するコマンド |
|-------|------|-----------------|
| `outline_created` | ブレインストーミング完了、アウトライン作成済み | `/bbl:brainstorm` 実行後 |
| `article_created` | 記事作成完了、レビュー待ち | `/bbl:create-article` 実行後 |
| `completed` | レビュー完了、公開可能 | `/bbl:review-article` 実行後 |

### コンテキストファイルの例

```yaml
concept: 心理的安全性
category: ヒト
subcategory: 組織行動・リーダーシップ
outline: |
  導入問題:
    シナリオ: チームメンバーが意見を言いにくい状況
    問い: どのように改善すべきか
  ...
file_path: docs/ヒト/組織行動・リーダーシップ/心理的安全性.md
phase: article_created  # 状態: 記事作成済み、レビュー待ち
review_score: 85        # (完了後) レビュースコア
updated: 2025-01-12T10:00:00
```

### エラー時の対応

各コマンドは以下の場合にエラーを報告します：

- **コンテキストファイル不在**: `/bbl:brainstorm [概念名]` を実行
- **phase不整合**: 現在のphaseに応じて適切なコマンドを案内
- **必須フィールド欠落**: `/bbl:brainstorm` を再実行して修正

## ライセンス

MIT
