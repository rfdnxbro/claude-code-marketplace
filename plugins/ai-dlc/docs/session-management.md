# セッション状態管理

AI-DLCセッションの状態を `current.yml` で管理します。

## current.yml の構造

```yaml
bolt: YYYYMMDD_<bolt-name>
type: greenfield | brownfield
phase: inception | construction | operation
step: <current-step>
updated: YYYY-MM-DDTHH:MM:SS
```

| フィールド | 説明 |
|-----------|------|
| `bolt` | ボルト識別子（日付_名前形式） |
| `type` | 開発タイプ（新規 or 既存システム改修） |
| `phase` | 現在のフェーズ |
| `step` | 現在のステップ |
| `updated` | 最終更新日時 |

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

## 使用例

```yaml
bolt: 20251230_user-auth
type: greenfield
phase: construction
step: code-gen
updated: 2025-12-30T14:30:00
```
