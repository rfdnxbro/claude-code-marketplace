---
paths: plugins/*/agents/**/*.md
---

# サブエージェント

Markdown + YAML Frontmatter形式で記述します。

## 形式

```markdown
---
name: agent-name
description: エージェントの説明（必須）
tools: Read, Grep, Glob, Bash
model: inherit
---

エージェントのシステムプロンプト
```

## Frontmatterオプション

| フィールド | 必須 | 説明 | 値の例 |
|-----------|------|------|--------|
| `name` | Yes | エージェント識別子（kebab-case） | `code-reviewer` |
| `description` | Yes | エージェントの説明 | `Use for code reviews` |
| `tools` | No | アクセス可能なツール（カンマ区切り） | `Read, Edit, Bash` |
| `model` | No | 使用するモデル | `sonnet`, `opus`, `haiku`, `inherit` |
