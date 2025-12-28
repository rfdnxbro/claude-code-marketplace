---
paths: plugins/*/commands/**/*.md, .claude/commands/**/*.md
---

# スラッシュコマンド

Markdown + YAML Frontmatter形式で記述します。

## 形式

```markdown
---
description: コマンドの説明
allowed-tools: Bash(git add:*), Bash(git commit:*)
model: claude-3-5-haiku-20241022
argument-hint: [message]
disable-model-invocation: false
---

コマンドの本体プロンプト

$ARGUMENTS で引数を受け取れます
```

## Frontmatterオプション

| フィールド | 必須 | 説明 | デフォルト |
|-----------|------|------|-----------|
| `description` | No | コマンドの説明（`/help`で表示） | プロンプトの最初の行 |
| `allowed-tools` | No | 使用可能なツール（カンマ区切り） | 会話から継承 |
| `model` | No | 使用するモデル | 会話から継承 |
| `argument-hint` | No | 引数のヒント（オートコンプリート表示） | なし |
| `disable-model-invocation` | No | SlashCommandツール経由の実行を防止 | `false` |

## 引数

- `$ARGUMENTS` - 全ての引数をキャプチャ
- `$1`, `$2`, `$3`... - 個別の位置指定引数

## allowed-tools のベストプラクティス

**必要最小限のツールのみ指定**（セキュリティ向上）:

```yaml
# 良い例: 特定のコマンドパターンのみ許可
allowed-tools: Bash(git add:*), Bash(git commit:*)

# 避けるべき例: 広範なワイルドカード
allowed-tools: Bash(*)
```

## disable-model-invocation

危険な操作を手動実行のみに制限:

```yaml
---
disable-model-invocation: true
description: 本番デプロイ（手動実行のみ）
allowed-tools: Bash(deploy:*)
---
```

- `true`: Claudeの自動実行を禁止（ユーザーの手動実行のみ可能）
- `false`: Claudeが会話中に自動実行可能
