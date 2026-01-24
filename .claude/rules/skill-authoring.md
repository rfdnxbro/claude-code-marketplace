---
paths: plugins/*/skills/**/SKILL.md, .claude/skills/**/SKILL.md
---

# スキル作成ベストプラクティス

## スラッシュコマンドとの関係

スキルとスラッシュコマンドは統一されたコンセプトです（Claude Code v2.1.3以降）。

| 種類 | ファイル | 用途 |
|------|----------|------|
| スキル | `skills/**/SKILL.md` | 複雑なワークフロー、サポートファイル付き |
| スラッシュコマンド | `commands/**/*.md` | シンプルなプロンプト展開 |

どちらも同じfrontmatterオプション（`allowed-tools`、`hooks`等）を使用できます。詳細は[slash-commands.md](slash-commands.md)を参照。

## 基本原則

**簡潔に**: コンテキストウィンドウは共有リソース。Claudeが既に知っている情報は含めない。

**自由度を適切に設定**:

| 自由度 | 使用場面 | 例 |
|--------|----------|-----|
| 高 | 複数アプローチが有効、コンテキスト依存 | コードレビュー手順 |
| 中 | 推奨パターンあり、一部変動可 | パラメータ付きスクリプト |
| 低 | 脆弱な操作、一貫性が重要 | DB マイグレーション |

**複数モデルでテスト**: Haiku/Sonnet/Opusで動作確認。Opusで動くものがHaikuでは詳細が必要な場合がある。

## Frontmatter

```yaml
---
name: processing-something
description: XとYを処理する。ユーザーがZについて言及した時やWが必要な時に使用。
user-invocable: true
agent: general-purpose
context: main
allowed-tools:
  - Read
  - Grep
  - Bash
---
```

### 必須フィールド

**name**:

- 最大64文字
- 小文字、数字、ハイフンのみ
- 動名詞形を推奨（`processing-pdfs`）、名詞形も可（`pdf-processing`）
- 予約語禁止: `anthropic`, `claude`

**description**:

- 最大1024文字
- 三人称で記述（「ファイルを処理する」、「私がファイルを処理します」ではない）
- 何をするか AND いつ使うかを含める
- 発見性のため具体的なキーワードを含める

### オプションフィールド

**user-invocable** (デフォルト: `true`):

- `true`: スラッシュコマンドメニューに表示
- `false`: メニューから非表示（プログラマティックに呼び出し可能）

```yaml
# スキルをメニューから非表示にする
user-invocable: false
```

**agent**:

使用するエージェントタイプを指定。指定しない場合は会話コンテキストで実行。

```yaml
# 特定のエージェントタイプで実行
agent: Explore
```

**context** (デフォルト: `main`):

- `main`: メインスレッドで実行
- `fork`: フォークされたサブエージェントコンテキストで実行

```yaml
# フォークされたコンテキストで実行
context: fork
```

**allowed-tools**:

スキル実行時に使用可能なツールを制限。省略時は会話から継承。

カンマ区切り形式:

```yaml
allowed-tools: Read, Grep, Bash(git:*)
```

YAML形式のリスト:

```yaml
allowed-tools:
  - Read
  - Grep
  - Bash(git:*)
```

**hooks**:

スキル実行時のフックを定義。詳細は[hooks.md](hooks.md)を参照。

```yaml
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "${CLAUDE_PLUGIN_ROOT}/scripts/validate.sh"
```

## スキルの承認要件

スキルの実行時にユーザー承認が必要かどうかは、スキルが持つ権限やフックによって決まります（v2.1.19以降）。

### 自動承認されるスキル

以下の条件をすべて満たすスキルは、ユーザー承認なしで実行されます:

- `allowed-tools`フィールドが指定されていない、または会話から継承
- `hooks`フィールドが指定されていない

**例（承認不要）:**

```yaml
---
name: code-review-helper
description: コードレビューのガイドラインを提供する
---

以下のコードレビューガイドラインに従ってください...
```

### 承認が必要なスキル

以下のいずれかの条件を満たすスキルは、実行前にユーザー承認が必要です:

- `allowed-tools`で追加の権限を要求している
- `hooks`が定義されている

**例（承認必要）:**

```yaml
---
name: git-commit-helper
description: Gitコミットを作成する
allowed-tools:
  - Bash(git add:*)
  - Bash(git commit:*)
---

変更をコミットします...
```

この仕組みにより、シンプルなプロンプト展開のみを行うスキルはスムーズに実行され、権限を必要とするスキルのみ承認フローを経ることになります。

## 環境変数

スキル内で使用可能な環境変数:

| 変数 | 説明 | 使用例 |
|------|------|--------|
| `${CLAUDE_SESSION_ID}` | 現在のセッションID | セッション固有のログファイル名生成 |
| `${CLAUDE_PLUGIN_ROOT}` | プラグインルートへの絶対パス | スクリプト実行パスの指定 |

**使用例:**

```yaml
---
name: session-logger
description: セッション固有のログを記録する
allowed-tools:
  - Bash(echo:*,tee:*)
---

セッション${CLAUDE_SESSION_ID}のログを記録します。

ログファイルパス: `/tmp/claude-session-${CLAUDE_SESSION_ID}.log`

すべての出力をログファイルに保存してください。
```

## ディレクトリ構造

スキルはSKILL.mdを中心に、必要に応じてサポートファイルを配置:

```text
my-skill/
├── SKILL.md           # 必須: エントリーポイント
├── reference.md       # オプション: 詳細リファレンス
├── examples.md        # オプション: コード例集
└── scripts/           # オプション: 実行可能スクリプト
    ├── helper.py
    └── validate.sh
```

### スキルの自動検出

Claude Codeは`.claude/skills`ディレクトリ内のスキルを自動的に検出します（v2.1.6以降）:

- **親ディレクトリからの検出**: サブディレクトリ内のファイルで作業している場合でも、親ディレクトリの`.claude/skills`が自動的に検出される
- **ネストされたスキル**: `.claude/skills`配下に任意の階層でスキルを配置可能（`skills/category/my-skill/SKILL.md`等）
- **プラグイン内のスキル**: プラグインの`skills/`ディレクトリ内のスキルも同様に検出される

検出されるスキルの例:

```text
project/
├── .claude/
│   └── skills/
│       ├── skill-a/SKILL.md           # 検出される
│       └── category/
│           └── skill-b/SKILL.md       # 検出される（ネスト）
└── src/
    └── feature/
        └── .claude/
            └── skills/
                └── skill-c/SKILL.md   # 検出される（サブディレクトリ）
```

### ファイル分割の基準

- **SKILL.md**: 500行以下。クイックスタートと基本的なワークフロー
- **別ファイルに分割すべき場合**:
  - 詳細なAPIリファレンス → `reference.md`
  - 複数のコード例 → `examples.md`
  - 繰り返し参照する定義 → 専用ファイル

### scripts/ ディレクトリ

`scripts/` 内のファイルはClaudeのコンテキストには読み込まれない。Claudeが実行するためのヘルパースクリプトを配置する。

```markdown
## 検証スクリプト
`scripts/validate.sh` を実行して設定を検証:
\`\`\`bash
bash scripts/validate.sh
\`\`\`
```

## コンテンツガイドライン

**簡潔に**: Claudeは賢い。Claudeが知らない情報のみ追加する。

**SKILL.md本文**: 500行以下に抑える。超える場合は別ファイルに分割。

**参照**: SKILL.mdから1階層のみ。ネストした参照は避ける。

**用語**: 一貫した用語を使用（"API endpoint"と"URL"を混在させない）。

**パス**: 常にスラッシュを使用（`scripts/helper.py`、`scripts\helper.py`ではない）。

## 構造パターン

**ワークフローパターン** - 複数ステップのタスク向け:

```markdown
このチェックリストをコピー:
- [ ] Step 1: Xを実行
- [ ] Step 2: Yを実行
- [ ] Step 3: 検証
```

**段階的開示** - 詳細へのリンク:

```markdown
## クイックスタート
[必須コンテンツ]

**詳細**: [reference.md](reference.md) を参照
```

**テンプレートパターン** - 出力形式を指定:

```markdown
## レポート構造
必ずこの構造を使用:

# [タイトル]
## 概要
[1段落の要約]
## 主な発見
- 発見1
- 発見2
```

**例示パターン** - 入力/出力ペアで期待を明示:

```markdown
## コミットメッセージ形式

**例1:**
入力: ユーザー認証をJWTで追加
出力: feat(auth): JWT認証を実装

**例2:**
入力: 日付表示のバグを修正
出力: fix(ui): 日付フォーマットを修正
```

**条件分岐パターン** - 状況に応じた分岐:

```markdown
## ワークフロー

1. タイプを判定:
   - **新規作成?** → 「作成フロー」へ
   - **既存編集?** → 「編集フロー」へ
```

**長いファイルには目次**: 100行超のリファレンスファイルは冒頭に目次を追加。

## 実行可能スクリプト（高度）

**エラーはスクリプトで処理**: Claudeに任せず、スクリプト内で明示的にエラー処理。

**ユーティリティスクリプトの利点**:

- 生成コードより信頼性が高い
- トークン節約（コンテキストに含めない）
- 使用の一貫性を保証

**MCPツール参照**: 完全修飾名を使用（`ServerName:tool_name`）。

**依存パッケージを明示**: 必要なパッケージをSKILL.mdに記載。

## 避けるべきこと

- 時間依存の情報（"2025年8月以前は..."）
- 選択肢が多すぎる（"XかYかZを使用..."）→ デフォルトを提供
- 曖昧な説明（"ファイルを処理する"）
- Claudeが既に知っていることの過剰説明
- Windowsスタイルのパス（`\`）→ 常に `/` を使用
- 深いネスト参照 → SKILL.mdから1階層のみ

## チェックリスト

公開前に確認:

- [ ] descriptionに「何をするか」と「いつ使うか」が含まれている
- [ ] SKILL.md本文が500行以下
- [ ] 参照ファイルが1階層のみ
- [ ] 用語が一貫している
- [ ] 具体的な例がある
- [ ] ワークフローに明確なステップがある
- [ ] 時間依存の情報がない
