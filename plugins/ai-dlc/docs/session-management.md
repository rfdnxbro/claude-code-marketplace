# セッション状態管理

AI-DLCセッションの状態を `current.yml` で管理します。

## current.yml の配置

```
aidlc-docs/
└── YYYYMMDD_<bolt-name>/
    └── current.yml
```

## current.yml スキーマ

### フィールド定義

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `bolt` | string | ○ | ボルト識別子（`YYYYMMDD_<name>`形式） |
| `type` | enum | ○ | 開発タイプ |
| `phase` | enum | ○ | 現在のフェーズ |
| `step` | string | ○ | 現在のステップ |
| `updated` | datetime | ○ | 最終更新日時（ISO 8601形式） |

### フィールド詳細

#### bolt

ボルトの一意識別子。`/ai-dlc:setup` 実行時に生成。

- 形式: `YYYYMMDD_<kebab-case-name>`
- 例: `20251230_user-auth`, `20260101_payment-system`

#### type

開発タイプを示す。setupで選択。

| 値 | 説明 |
|----|------|
| `greenfield` | 新規システムの開発 |
| `brownfield` | 既存システムへの機能追加・改善 |

#### phase

現在のフェーズ。ステップ遷移に応じて自動更新。

| 値 | 説明 |
|----|------|
| `inception` | 要件定義・ユニット分解 |
| `construction` | 設計・実装 |
| `operation` | デプロイ・運用（今後実装） |

#### step

現在のステップ名。各スキル完了時に次のステップに更新。

| 値 | フェーズ | 対応スキル |
|----|---------|-----------|
| `user-stories` | inception | `/ai-dlc:inception:user-stories` |
| `units` | inception | `/ai-dlc:inception:units` |
| `domain-model` | construction | `/ai-dlc:construction:domain-model` |
| `code-gen` | construction | `/ai-dlc:construction:code-gen` |
| `architecture` | construction | `/ai-dlc:construction:architecture` |
| `api` | construction | `/ai-dlc:construction:api` |

#### updated

最終更新日時。ISO 8601形式（タイムゾーンなし、ローカル時刻）。

- 形式: `YYYY-MM-DDTHH:MM:SS`
- 例: `2025-12-30T14:30:00`

> **注**: タイムゾーン情報は含めない。ローカル時刻として扱う。

### 完全な例

```yaml
bolt: 20251230_user-auth
type: greenfield
phase: construction
step: code-gen
updated: 2025-12-30T14:30:00
```

## ステップ遷移表

| フェーズ | ステップ | 次のステップ |
|---------|---------|-------------|
| inception | user-stories | units |
| inception | units | domain-model（→construction） |
| construction | domain-model | code-gen |
| construction | code-gen | architecture |
| construction | architecture | api |
| construction | api | deploy（→operation、今後実装） |

## 状態更新ルール

各コマンド完了後、必ず `current.yml` を更新：

1. `step` を次のステップ名に変更
2. `updated` を現在時刻に更新
3. フェーズが変わる場合は `phase` も更新
