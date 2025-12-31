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
model: haiku
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
| `model` | No | 使用するモデル（`sonnet`, `opus`, `haiku`）| 未指定時は会話のモデルを使用 |
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

## バリデーター警告のスキップ

バリデーターが出す警告を意図的にスキップするには、本文中にHTMLコメントを追加します:

```markdown
---
description: REST API作成
---

<!-- validator-disable dangerous-operation -->

APIエンドポイントを作成...
```

### 警告ID一覧

| 警告ID | 説明 |
|--------|------|
| `dangerous-operation` | 危険なキーワード（deploy, delete等）検出時の警告 |
| `broad-bash-wildcard` | `Bash(*)`使用時の警告 |

## フィールド命名規則について

フロントマターのフィールド名は**Claude Code本体の仕様**に従っています。

- `allowed-tools`, `argument-hint`, `disable-model-invocation`: kebab-case（Claude Code公式仕様）

この命名規則は当プロジェクト独自のものではなく、Claude Codeでそのまま使用できる形式です。`agents.md`の`permissionMode`（camelCase）も同様にClaude Code本体の仕様に従っています。
