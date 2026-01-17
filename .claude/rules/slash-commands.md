---
paths: plugins/*/commands/**/*.md, .claude/commands/**/*.md
---

# スラッシュコマンド

Markdown + YAML Frontmatter形式で記述します。

## スキルとの関係

スラッシュコマンドとスキルは統一されたコンセプトです（Claude Code v2.1.3以降）。

| 種類 | ファイル | 用途 |
|------|----------|------|
| スラッシュコマンド | `commands/**/*.md` | シンプルなプロンプト展開 |
| スキル | `skills/**/SKILL.md` | 複雑なワークフロー、サポートファイル付き |

どちらも同じfrontmatterオプション（`allowed-tools`、`hooks`等）を使用できます。詳細は[skill-authoring.md](skill-authoring.md)を参照。

## 形式

```markdown
---
description: コマンドの説明
allowed-tools: Bash(git add:*), Bash(git commit:*)
model: haiku
argument-hint: [message]
disable-model-invocation: false
context: main
---

コマンドの本体プロンプト

$ARGUMENTS で引数を受け取れます
```

## Frontmatterオプション

| フィールド | 必須 | 説明 | デフォルト |
|-----------|------|------|-----------|
| `description` | No | コマンドの説明（`/help`で表示） | プロンプトの最初の行 |
| `allowed-tools` | No | 使用可能なツール（カンマ/YAML形式） | 会話から継承 |
| `model` | No | 使用するモデル（`sonnet`, `opus`, `haiku`）| 未指定時は会話のモデルを使用 |
| `argument-hint` | No | 引数のヒント（オートコンプリート表示） | なし |
| `disable-model-invocation` | No | SlashCommandツール経由の実行を防止 | `false` |
| `context` | No | 実行コンテキスト（`main`, `fork`） | `main` |
| `hooks` | No | フック定義（[hooks.md](hooks.md)参照） | なし |

## 引数と環境変数

- `$ARGUMENTS` - 全ての引数をキャプチャ
- `$1`, `$2`, `$3`... - 個別の位置指定引数
- `${CLAUDE_SESSION_ID}` - 現在のセッションID（v2.1.9以降）

## allowed-tools のベストプラクティス

**必要最小限のツールのみ指定**（セキュリティ向上）:

カンマ区切り形式:

```yaml
# 良い例: 特定のコマンドパターンのみ許可
allowed-tools: Bash(git add:*), Bash(git commit:*)

# 避けるべき例: 広範なワイルドカード
allowed-tools: Bash(*)
```

YAML形式のリスト:

```yaml
# 良い例: 特定のツールのみ許可
allowed-tools:
  - Bash(git add:*)
  - Bash(git commit:*)
  - Read
  - Edit

# 避けるべき例: 広範なワイルドカード
allowed-tools:
  - Bash(*)
```

## context

実行コンテキストを指定:

```yaml
---
context: fork
---
```

- `main`（デフォルト）: メインスレッドで実行
- `fork`: フォークされたサブエージェントコンテキストで実行

## hooks

コマンド実行時のフックを定義。詳細は[hooks.md](hooks.md)を参照:

```yaml
---
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "${CLAUDE_PLUGIN_ROOT}/scripts/validate.sh"
  Stop:
    - hooks:
        - type: prompt
          prompt: "処理完了を確認"
---
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
| `dangerous-operation` | 危険なキーワード（deploy, delete, drop, production, 本番）検出時の警告 |
| `broad-bash-wildcard` | `Bash(*)`使用時の警告 |

**注意**: キーワード検出は大文字小文字を区別しません（`DELETE`も`delete`として検出）。

## フィールド命名規則について

フロントマターのフィールド名は**Claude Code本体の仕様**に従っています。

- `allowed-tools`, `argument-hint`, `disable-model-invocation`: kebab-case（Claude Code公式仕様）

この命名規則は当プロジェクト独自のものではなく、Claude Codeでそのまま使用できる形式です。`agents.md`の`permissionMode`（camelCase）も同様にClaude Code本体の仕様に従っています。
