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
context: fork
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
| `context` | No | 実行コンテキスト（`fork`でサブエージェント実行） | 省略時はメインコンテキスト |
| `agent` | No | 使用するサブエージェント名 | なし |
| `hooks` | No | フック定義（[hooks.md](hooks.md)参照） | なし |
| `effort` | No | モデルエフォートレベル（`low`, `normal`, `high`）（v2.1.80以降） | 会話から継承 |

## 引数と環境変数

コマンド内で以下の構文で引数にアクセスできます:

| 構文 | 説明 | 例 |
|------|------|-----|
| `$ARGUMENTS` | 全ての引数を1つの文字列として取得 | `hello world` |
| `$ARGUMENTS[0]` | 最初の引数を取得（ブラケット記法） | `hello` |
| `$ARGUMENTS[1]` | 2番目の引数を取得 | `world` |
| `$0` | コマンド名自体（v2.1.19以降） | `/mycommand` |
| `$1`, `$2`, `$3`... | 個別の位置指定引数のショートハンド（v2.1.19以降） | `$1` = `hello` |
| `${CLAUDE_SESSION_ID}` | 現在のセッションID（v2.1.9以降） | セッション固有ID |

**使用例:**

```markdown
---
description: 引数を処理するコマンド
---

コマンド名: $0
全引数: $ARGUMENTS
1番目の引数: $1（または $ARGUMENTS[0]）
2番目の引数: $2（または $ARGUMENTS[1]）
```

`/mycommand hello world`を実行すると:

- `$0` = `/mycommand`
- `$ARGUMENTS` = `hello world`
- `$1` または `$ARGUMENTS[0]` = `hello`
- `$2` または `$ARGUMENTS[1]` = `world`

## 環境変数

スラッシュコマンド内で使用可能な環境変数:

| 変数 | 説明 | 使用例 |
|------|------|--------|
| `${CLAUDE_SESSION_ID}` | 現在のセッションID | セッション固有のログファイル名生成 |
| `${CLAUDE_PLUGIN_ROOT}` | プラグインルートへの絶対パス | スクリプト実行パスの指定 |

**使用例:**

```markdown
---
description: セッション固有のログを記録する
allowed-tools:
  - Bash(echo:*,tee:*)
---

セッション${CLAUDE_SESSION_ID}のログを記録します。

ログファイルパス: `/tmp/claude-session-${CLAUDE_SESSION_ID}.log`

すべての出力をログファイルに保存してください。
```

## allowed-tools のベストプラクティス

**必要最小限のツールのみ指定**（セキュリティ向上）:

カンマ区切り形式:

```yaml
# 良い例: 特定のコマンドパターンのみ許可
allowed-tools: Bash(git add:*), Bash(git commit:*)

# 注意: 広範なワイルドカード（Bash(*)はBashと同等に扱われる）
allowed-tools: Bash(*)  # Bashと同じ意味
```

YAML形式のリスト:

```yaml
# 良い例: 特定のツールのみ許可
allowed-tools:
  - Bash(git add:*)
  - Bash(git commit:*)
  - Read
  - Edit

# 注意: 広範なワイルドカード（Bash(*)はBashと同等に扱われる）
allowed-tools:
  - Bash(*)  # Bashと同じ意味
```

**注意 (v2.1.20以降)**: `Bash(*)`は`Bash`と同等に扱われます。すべてのBashコマンドへのアクセスを許可する場合は、どちらの記法でも同じ意味になります。セキュリティ上の理由から、可能な限り具体的なパターンを指定することを推奨します。

**パーミッション優先順位（v2.1.27以降）:**

content-level（具体的パターン）の`ask`設定は、tool-level（ツール全体）の`allow`設定より優先されます。

```json
{
  "allow": ["Bash"],
  "ask": ["Bash(rm *)"]
}
```

上記の設定では:

- `Bash`ツール全体は許可（`allow`）されていますが
- `rm`コマンドは確認プロンプトが表示されます（`ask`が優先）

この仕組みにより、ツール全体を許可しつつ、危険な操作のみ個別に制限できます。

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

## インラインシェル実行の無効化（v2.1.91以降）

スラッシュコマンドやプラグインコマンド内で `` !`command` `` 構文を使用したインラインシェル実行は、`disableSkillShellExecution` 設定により無効化できます。

この設定はユーザー側（`settings.json`）で制御するものです。プラグイン開発者は、インラインシェル実行が無効化されている環境でもコマンドが適切に動作するよう設計することを推奨します。

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
| `broad-bash-wildcard` | `Bash(*)`使用時の警告（v2.1.20以降、`Bash(*)`は`Bash`と同等に扱われますが、より具体的なパターンの使用を推奨） |

**注意**:

- キーワード検出は大文字小文字を区別しません（`DELETE`も`delete`として検出）。
- v2.1.20以降、`Bash(*)`は`Bash`と同等に扱われます。バリデーターは依然として警告を出しますが、これはより具体的なパターンの使用を推奨するためです。

### HTML コメントと CLAUDE.md 自動注入（v2.1.72以降）

v2.1.72以降、CLAUDE.md が Claude に自動注入される際、`<!-- ... -->` 形式の HTML コメントは Claude から**隠されます**。`Read` ツールで明示的にファイルを読む場合は引き続き表示されます。

**影響:**

- `<!-- validator-disable dangerous-operation -->` 等のバリデーター無効化コメントは、自動注入時に Claude には見えなくなります
- バリデーターはファイルを直接読んで検証するため、バリデーション自体には影響ありません
- コメントはファイル内に引き続き存在し、`Read` ツールで確認可能です

**用途:**

この仕様を活用して、Claude に見せたくない開発者向けのメモや設定を HTML コメントとして CLAUDE.md や `.claude/rules/*.md` に記述できます。

## サンドボックスモードでの制限（v2.1.38以降）

サンドボックスモードで実行されるスラッシュコマンドは、`.claude/skills`ディレクトリへの書き込みがブロックされます。

**制限される操作:**

- `.claude/skills`ディレクトリ内のスキルファイルの作成・変更・削除
- スラッシュコマンドからのスキル動的生成

**代替アプローチ:**

- スキルの動的生成が必要な場合は、プラグインの`Setup`フックを使用して初期セットアップ時に生成する
- 実行時の設定変更は、`.claude/skills`外のディレクトリに保存する
- スラッシュコマンドは既存のスキルを参照するのみにとどめる

詳細は[skill-authoring.md](skill-authoring.md)および[hooks.md](hooks.md)のセキュリティ注意事項を参照してください。

## バンドルコマンドとの名前衝突に関する注意

Claude Codeには組み込みのバンドルコマンド（`/clear`, `/model`, `/memory`, `/simplify`, `/batch` 等）が存在します。バンドルコマンドとユーザー定義コマンドで名前が衝突した場合の動作は保証されないため、これらと同名のコマンドをプラグインで定義することは避けてください。

## frontmatterフィールドにYAMLブール値キーワードを使う場合の注意

YAMLのブール値として解釈されるキーワード（`true`、`false`、`on`、`off`、`yes`、`no` 等）をfrontmatterの文字列フィールドに使用する場合は、文字列として引用符で囲む必要があります（v2.1.98で関連バグが修正済み）。

```yaml
# 正しい: 引用符で囲む
name: "on"
description: "off"

# 注意: YAMLではブール値として解釈される可能性がある
name: on
description: off
```

これはYAMLの仕様に由来する制約です。特に `on`、`off`、`yes`、`no` はYAML 1.1でブール値として扱われるため、コマンド名や説明文として使用する際は引用符で囲んでください。

## フィールド命名規則について

フロントマターのフィールド名は**Claude Code本体の仕様**に従っています。

- `allowed-tools`, `argument-hint`, `disable-model-invocation`: kebab-case（Claude Code公式仕様）

この命名規則は当プロジェクト独自のものではなく、Claude Codeでそのまま使用できる形式です。`agents.md`の`permissionMode`（camelCase）も同様にClaude Code本体の仕様に従っています。
