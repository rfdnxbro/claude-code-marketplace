---
paths: plugins/*/commands/**/*.md, .claude/commands/**/*.md
---

# スラッシュコマンド

Markdown + YAML Frontmatter形式で記述します。

## 形式

```markdown
---
description: コマンドの説明（必須）
allowed-tools: Bash(git *), Read, Edit
model: claude-3-5-haiku-20241022
argument-hint: [引数のヒント]
---

コマンドの本体プロンプト

$ARGUMENTS で引数を受け取れます
$1, $2 で個別の引数も使用可能
```

## Frontmatterオプション

| フィールド | 必須 | 説明 |
|-----------|------|------|
| `description` | Yes | コマンドの説明 |
| `allowed-tools` | No | 使用可能なツール |
| `model` | No | 使用するモデル |
| `argument-hint` | No | 引数のヒント表示 |

## 引数

- `$ARGUMENTS` - 全ての引数をキャプチャ
- `$1`, `$2`, `$3`... - 個別の位置指定引数
