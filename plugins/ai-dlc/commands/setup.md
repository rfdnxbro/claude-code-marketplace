---
description: AI-DLCセッションを初期化し、ボルトを作成
allowed-tools: Bash(mkdir:*), Bash(date:*), Write, Read
argument-hint: [bolt-name]
---

# AI-DLCセッション初期化

AI-DLC方法論に基づく開発セッションを開始します。

## 手順

1. ボルト名の確認
2. 開発タイプの選択（グリーンフィールド/ブラウンフィールド）
3. 必要なディレクトリ構造の作成
4. current.yml（セッション状態ファイル）の作成

## 実行

### ステップ1: ボルト名の決定

引数 `$ARGUMENTS` または `$1` でボルト名を取得。空の場合はユーザーに質問：
「このボルトの名前を教えてください（例: user-auth, payment-system）」

### ステップ2: 開発タイプの選択

ユーザーに質問：
- **グリーンフィールド**: 新規システムの開発
- **ブラウンフィールド**: 既存システムへの機能追加・改善

### ステップ3: ディレクトリ構造の作成

```
aidlc-docs/
└── YYYYMMDD_<bolt-name>/
    ├── plans/              # 計画ドキュメント
    ├── requirements/       # 要件・機能変更ドキュメント
    ├── story-artifacts/    # ユーザーストーリー
    ├── design-artifacts/   # アーキテクチャ・設計ドキュメント
    └── current.yml         # セッション状態管理
```

### ステップ4: current.ymlの作成

```yaml
bolt: YYYYMMDD_<bolt-name>
type: greenfield  # または brownfield
phase: inception
step: user-stories
updated: YYYY-MM-DDTHH:MM:SS
```

## 完了メッセージ

**AI-DLCセッションを初期化しました**

- ボルト: `YYYYMMDD_<bolt-name>`
- タイプ: グリーンフィールド/ブラウンフィールド
- フェーズ: インセプション

**次のステップ:**
`/ai-dlc:inception:user-stories` を実行してユーザーストーリーを作成してください
