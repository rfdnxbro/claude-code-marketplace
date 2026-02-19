---
paths: plugins/*/agents/**/*.md, .claude/agents/**/*.md
---

# サブエージェント

Markdown + YAML Frontmatter形式で記述します。

## ファイル配置

エージェント定義ファイルは以下のパスに配置します:

- `plugins/*/agents/**/*.md` - プラグイン内のエージェント
- `.claude/agents/**/*.md` - プロジェクト固有のエージェント

**注意（v2.1.39以降）**:

- `.claude/agents/`ディレクトリ内には、エージェント定義以外のMarkdownファイル（README.mdなど）も配置できます
- エージェント定義として認識されるのは、frontmatterに`name`フィールドを持つMarkdownファイルのみです
- ドキュメント用のMarkdownファイルには警告は表示されません

## 形式

```markdown
---
name: agent-name
description: エージェントの説明。いつ使うべきかを明確に記述。
tools: Read, Grep, Glob, Bash
model: sonnet
permissionMode: default
skills: skill-name
---

エージェントのシステムプロンプト
```

## Frontmatterオプション

| フィールド | 必須 | 説明 |
|-----------|------|------|
| `name` | Yes | 識別子（小文字・ハイフンのみ） |
| `description` | Yes | 目的と使用タイミングを説明 |
| `tools` | No | アクセス可能なツール（カンマ/YAML形式）。省略時は全ツール継承 |
| `disallowedTools` | No | 使用禁止ツール（カンマ/YAML形式） |
| `model` | No | `sonnet`, `opus`, `haiku`, `inherit`。省略時は`sonnet` |
| `permissionMode` | No | `default`, `acceptEdits`, `bypassPermissions`, `plan`, `ignore` |
| `skills` | No | 自動ロードするスキル名（カンマ/YAML形式）。プラグインスキルは完全修飾名（`plugin-name:skill-name`）で指定 |
| `hooks` | No | フック定義（[hooks.md](hooks.md)参照） |
| `memory` | No | 永続的メモリのスコープ：`user`, `project`, `local`（v2.1.33以降） |

## description のベストプラクティス

- **いつ使うべきか**を明確に記述
- 具体的なキーワードを含める（自動委譲の判断に使用）

良い例:

```yaml
description: コードレビュー専門家。品質・セキュリティ・保守性を確認。コード変更後に積極的に使用。
```

悪い例:

```yaml
description: コードレビュー  # 曖昧で自動委譲されにくい
```

## tools のガイドライン

- 省略時: 親スレッドの全ツールを継承（MCPツール含む）
- 指定時: 指定したツールのみアクセス可能
- **最小限のツールを付与**することを推奨（セキュリティ向上）

カンマ区切り形式:

```yaml
tools: Read, Grep, Glob, Bash(git:*)
```

YAML形式のリスト:

```yaml
tools:
  - Read
  - Grep
  - Glob
  - Bash(git:*)
```

**注意 (v2.1.20以降)**: `Bash(*)`は`Bash`と同等に扱われます。すべてのBashコマンドへのアクセスを許可する場合は、どちらの記法でも同じ意味になります。セキュリティ上の理由から、可能な限り具体的なパターンを指定することを推奨します。

### サブエージェントの制限（v2.1.33以降）

`Task(agent_type)` 構文を使用して、起動可能なサブエージェントを制限できます。

**カンマ区切り形式:**

```yaml
tools: Read, Grep, Task(code-reviewer), Task(test-runner)
```

**YAML形式のリスト:**

```yaml
tools:
  - Read
  - Grep
  - Task(code-reviewer)
  - Task(test-runner)
```

この設定により、エージェントは `code-reviewer` と `test-runner` という名前のサブエージェントのみを起動できます。他のサブエージェントを起動しようとすると、権限エラーが発生します。

**使用例:**

```yaml
---
name: restricted-reviewer
description: 特定のサブエージェントのみ起動可能なレビューエージェント
tools:
  - Read
  - Grep
  - Task(security-checker)
  - Task(style-checker)
---

コードレビューを実行し、必要に応じて security-checker または style-checker のみを起動します。
```

**セキュリティのベストプラクティス:**

- エージェントが必要とするサブエージェントのみを明示的に許可
- `Task` を無制限に許可すると、任意のサブエージェントを起動できてしまうため注意
- ワークフロー全体のツール使用を制御する場合に有効

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

## memory（v2.1.33以降）

エージェントに永続的なメモリを付与し、セッション間で情報を保持できます。

```yaml
---
name: stateful-agent
description: 状態を保持するエージェント
memory: project
---
```

### スコープの種類

| スコープ | 説明 | 保存範囲 | 使用例 |
|---------|------|----------|--------|
| `user` | ユーザー全体で共有 | すべてのプロジェクト | ユーザー設定、学習した好み |
| `project` | プロジェクト内で共有 | 現在のプロジェクト | プロジェクト固有の知識、パターン |
| `local` | セッション固有 | 現在のセッション | 一時的な作業メモ、状態管理 |

### 使用例

**プロジェクト固有の知識を保持:**

```yaml
---
name: architecture-expert
description: プロジェクトのアーキテクチャ知識を保持する専門家
memory: project
tools:
  - Read
  - Grep
---

プロジェクトのアーキテクチャ設計を理解し、過去の決定事項を記憶します。
```

**ユーザー設定を保持:**

```yaml
---
name: personal-assistant
description: ユーザーの好みを学習するアシスタント
memory: user
---

ユーザーのコーディングスタイルや好みを学習し、すべてのプロジェクトで活用します。
```

### ベストプラクティス

- **userスコープ**: 個人的な設定や好みの保存に使用
- **projectスコープ**: プロジェクト固有のパターンや決定事項の記録に使用
- **localスコープ**: セッション内の一時的な状態管理に使用
- メモリには必要最小限の情報のみを保存（パフォーマンスへの影響を考慮）

## skills の完全修飾名（v2.1.47以降）

プラグインエージェントでスキルを参照する場合は、ベア名（例: `my-skill`）ではなく、完全修飾プラグイン名（例: `my-plugin:my-skill`）を使用してください。

**理由**: ベア名での参照は黙って失敗することがありましたが、v2.1.47以降ではこの仕様が正しく動作するようになっています。確実にスキルをロードするために、完全修飾名の使用を推奨します。

**推奨（完全修飾名）:**

```yaml
---
name: my-agent
description: プラグインスキルを使用するエージェント
skills:
  - my-plugin:my-skill        # 完全修飾名（推奨）
  - other-plugin:other-skill
---
```

**非推奨（ベア名）:**

```yaml
---
name: my-agent
description: プラグインスキルを使用するエージェント
skills:
  - my-skill        # ベア名（ロードに失敗する可能性あり）
---
```

**注意**: 同一プラグイン内のスキルであってもプラグイン名を明示することを推奨します。

## hooks

エージェント実行時のフックを定義。詳細は[hooks.md](hooks.md)を参照:

```yaml
---
name: code-reviewer
description: コードレビュー専門家
hooks:
  PreToolUse:
    - matcher: "Edit|Write"
      hooks:
        - type: command
          command: "${CLAUDE_PLUGIN_ROOT}/scripts/check-style.sh"
  Stop:
    - hooks:
        - type: prompt
          prompt: "レビュー結果を要約"
---
```
