---
description: 現在のAI-DLCセッション状態を確認し、次のステップを提案
allowed-tools: Read, Glob
---

# AI-DLC 現在の状態確認

current.ymlを参照し、現在のセッション状態と次に実行すべきコマンドを提案します。

## 手順

### ステップ1: current.ymlの検索と読み込み

`aidlc-docs/*/current.yml` を検索し、最新のセッション状態を読み込んでください。
複数のボルトが存在する場合は、`updated`フィールドが最新のものを使用。

**セッション確認（オプション）:**
- `session_id`フィールドが存在し、かつ現在のセッションID（`${CLAUDE_SESSION_ID}`）と異なる場合は警告を表示
- 警告例: 「このボルトは別のセッション（ID: xxx）で作成されました。続行しますか？」

### ステップ2: 状態の表示

| 項目 | 値 |
|------|-----|
| ボルト | `<bolt>` |
| セッションID | `<session_id>` (存在する場合) |
| タイプ | グリーンフィールド/ブラウンフィールド |
| フェーズ | インセプション/コンストラクション |
| ステップ | `<step>` |
| 最終更新 | `<updated>` |

### ステップ3: 次のステップの提案

#### インセプションフェーズ
| ステップ | 次のコマンド |
|---------|-------------|
| `user-stories` | `/ai-dlc:inception:user-stories` |
| `units` | `/ai-dlc:inception:units` |

#### コンストラクションフェーズ
| ステップ | 次のコマンド |
|---------|-------------|
| `domain-model` | `/ai-dlc:construction:domain-model` |
| `code-gen` | `/ai-dlc:construction:code-gen` |
| `architecture` | `/ai-dlc:construction:architecture` |
| `api` | `/ai-dlc:construction:api` |

## エラーハンドリング

current.ymlが見つからない場合：
「セッションが見つかりません。まず `/ai-dlc:setup` を実行してください。」
