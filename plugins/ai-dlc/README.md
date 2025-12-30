# AI-DLC Plugin

AI駆動開発ライフサイクル（AI-DLC）のスラッシュコマンド、サブエージェント、スキルを提供するプラグインです。

## 概要

AI-DLCは、Amazon Web ServicesのRaja SP氏が提唱するAIネイティブな開発方法論です。従来のSDLCやアジャイル手法にAIを後付けするのではなく、AIを中心に据えた開発ライフサイクルを再構築することを目指しています。

## 独自の工夫（ホワイトペーパーからの拡張）

本プラグインは、[AI-DLCホワイトペーパー](https://prod.d13rzhkk8cj2z0.amplifyapp.com/)に基本的に準拠しつつ、以下の独自の工夫を加えています。

### 1. コマンドのフェーズ別ディレクトリ構造

ホワイトペーパーのコマンドをフェーズ別に整理し、コマンド名を `ai-dlc:<phase>:<command>` 形式にしています。

**理由**: AI-DLCの3フェーズ（インセプション、コンストラクション、オペレーション）を明示的に表現し、ユーザーが今どのフェーズで作業しているかを意識しやすくするため。

### 2. 複数ボルト対応

ホワイトペーパーでは「1つのユニットを1つ以上のボルトで実行」と記載されていますが、具体的な実装方法は示されていません。本プラグインでは、ボルトごとにディレクトリを分けて管理します。

**ディレクトリ命名規則**: `aidlc-docs/YYYYMMDD_<bolt-name>/` 形式

- 例: `aidlc-docs/20251230_user-auth/`, `aidlc-docs/20251231_payment/`

### 3. グリーンフィールド/ブラウンフィールド対応

`/ai-dlc:setup` 時に開発タイプを選択し、後続コマンドの挙動を自動的に切り替えます。

- **グリーンフィールド**: 新規アプリケーション開発。標準フローでドメインモデル設計から開始。
- **ブラウンフィールド**: 既存システムへの機能追加・改修。コンストラクションフェーズで先に既存コードのエレベーション（静的/動的モデル作成）を実施。

### 4. セッション状態管理

ボルトディレクトリ内に `current.yml` ファイルを作成し、現在のセッション状態を追跡します。

```yaml
bolt: 20251230_user-auth
type: greenfield  # or brownfield
phase: inception
step: user-stories
updated: 2025-12-30T10:00:00
```

`/ai-dlc:guide:current` コマンドで現在のステップと次に実行すべきコマンドを確認できます。

## インストール

```bash
claude plugins install ai-dlc
```

## 使い方

### スラッシュコマンド

| コマンド | 説明 | 対応フェーズ |
|---------|------|-------------|
| `/ai-dlc:setup` | AI-DLCセッションの初期化（ボルトディレクトリ作成、グリーン/ブラウン選択） | 共通 |
| `/ai-dlc:guide:current` | 現在のステップと次のアクションを表示 | 共通 |
| `/ai-dlc:inception:user-stories` | ユーザーストーリー作成 | インセプション |
| `/ai-dlc:inception:units` | ユニット分解 | インセプション |
| `/ai-dlc:construction:domain-model` | ドメインモデル作成 | コンストラクション |
| `/ai-dlc:construction:code-gen` | コード生成 | コンストラクション |
| `/ai-dlc:construction:architecture` | アーキテクチャ設計 | コンストラクション |
| `/ai-dlc:construction:api` | REST API作成 | コンストラクション |

### 基本的なワークフロー

```bash
# 1. ボルトのセットアップ（グリーンフィールド/ブラウンフィールド選択）
/ai-dlc:setup

# 2. 現在のステップを確認
/ai-dlc:guide:current

# 3. ユーザーストーリー作成（インセプションフェーズ）
/ai-dlc:inception:user-stories レコメンデーションエンジンを構築する

# 4. ユニット分解
/ai-dlc:inception:units

# 5. ドメインモデル作成（コンストラクションフェーズ）
# ブラウンフィールドの場合は自動的に既存コードのエレベーションを先に実施
/ai-dlc:construction:domain-model aidlc-docs/20251230_recommendation-engine

# 6. コード生成
/ai-dlc:construction:code-gen aidlc-docs/20251230_recommendation-engine
```

## ドキュメント

### docs/whitepaper.md（英語版）

AI-DLCホワイトペーパーの原文を参考資料として保管しています。

### docs/whitepaper-ja.md（日本語版）

AI-DLCホワイトペーパーの日本語訳を参考資料として保管しています。

> **著作権について**
>
> `docs/whitepaper.md` および `docs/whitepaper-ja.md` は Amazon Web Services の Raja SP 氏による著作物（および翻訳）です。
> 本プラグインでは、AI-DLC方法論の実装における参考資料として保管しています。
> 原典: <https://prod.d13rzhkk8cj2z0.amplifyapp.com/>

## AI-DLCの主要概念

| 用語 | 説明 |
|------|------|
| インテント | 達成すべき高レベルの目的（ビジネスゴール、機能、技術的成果） |
| ユニット | インテントから派生した、凝集度の高い独立した作業単位（DDDのサブドメインやスクラムのエピックに相当） |
| ボルト | 最小の反復単位。時間〜日単位の高速なビルド・検証サイクル（スクラムのスプリントに相当） |

## AI-DLCのフェーズ

1. **インセプションフェーズ**: モブエラボレーションリチュアルを通じてインテントをユニットに分解
2. **コンストラクションフェーズ**: ドメイン設計→論理設計→コード生成→テストの反復
3. **オペレーションフェーズ**: デプロイ、監視、運用の自動化

## 参考リンク

- [AI-DLC Whitepaper](https://prod.d13rzhkk8cj2z0.amplifyapp.com/)
