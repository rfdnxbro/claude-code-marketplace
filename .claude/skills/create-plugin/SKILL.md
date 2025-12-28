---
name: creating-plugins
description: Claude Codeマーケットプレイス用のプラグインを作成する。新規プラグイン作成、コマンド・エージェント・フック・MCPサーバーの追加時に使用。
---

# プラグイン作成

## ディレクトリ構造

```
plugins/[plugin-name]/
├── .claude-plugin/
│   └── plugin.json       # 必須
├── commands/
│   └── [command-name].md
├── agents/
│   └── [agent-name].md
├── hooks/
│   └── hooks.json
├── .mcp.json
└── README.md
```

## 命名規則

| 項目 | 規則 | 例 |
|------|------|-----|
| プラグイン名 | kebab-case | `my-awesome-plugin` |
| コマンドファイル | kebab-case.md | `review-code.md` |
| エージェントファイル | kebab-case.md | `code-reviewer.md` |

## ワークフロー

このチェックリストをコピー:

```
プラグイン作成:
- [ ] Step 1: プラグインディレクトリ作成
- [ ] Step 2: plugin.json作成
- [ ] Step 3: コンポーネント追加
- [ ] Step 4: README.md作成
- [ ] Step 5: 検証
```

**Step 1**: `plugins/[plugin-name]/` ディレクトリを作成

**Step 2**: `.claude-plugin/plugin.json` を作成（`name`フィールド必須）

**Step 3**: 必要なコンポーネントを追加:
- `commands/` - スラッシュコマンド
- `agents/` - サブエージェント
- `hooks/hooks.json` - フック
- `.mcp.json` - MCPサーバー

**Step 4**: `README.md` でプラグインを説明

**Step 5**: `claude plugin validate ./plugins/[plugin-name]` で検証

## 必須フィールド

- `plugin.json`: `name`（kebab-case）
- コマンド: frontmatterに`description`
- エージェント: frontmatterに`name`と`description`
