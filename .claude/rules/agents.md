---
paths: plugins/*/agents/**/*.md, .claude/agents/**/*.md
---

# サブエージェント

Markdown + YAML Frontmatter形式で記述します。

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
| `tools` | No | アクセス可能なツール（カンマ区切り）。省略時は全ツール継承 |
| `model` | No | `sonnet`, `opus`, `haiku`, `inherit`。省略時は`sonnet` |
| `permissionMode` | No | `default`, `acceptEdits`, `bypassPermissions`, `plan`, `ignore` |
| `skills` | No | 自動ロードするスキル名（カンマ区切り） |

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
