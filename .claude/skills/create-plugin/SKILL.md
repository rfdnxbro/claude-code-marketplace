---
name: creating-plugins
description: Claude Codeマーケットプレイス用のプラグインを作成する。新規プラグイン作成、コマンド・エージェント・フック・MCPサーバーの追加時に使用。
---

# プラグイン作成

## ディレクトリ構造

```text
plugins/[plugin-name]/
├── .claude-plugin/
│   └── plugin.json       # 必須
├── commands/
│   └── [command-name].md
├── agents/
│   └── [agent-name].md
├── skills/
│   └── [skill-name]/
│       └── SKILL.md
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
| スキルディレクトリ | kebab-case | `pdf-processing` |
| スキルファイル | SKILL.md（大文字） | `SKILL.md` |

## ワークフロー

以下のチェックリストを**すべて完了するまで**順に実施すること。各ステップ完了時にチェックを入れて進捗を報告する。

```text
プラグイン作成チェックリスト:
- [ ] Step 1: プラグインディレクトリ作成
- [ ] Step 2: plugin.json作成
- [ ] Step 3: コンポーネント追加
- [ ] Step 4: README.md作成（必須セクション3つ）
- [ ] Step 5: marketplace.json登録
- [ ] Step 6: バリデーション実行
```

**Step 1**: `plugins/[plugin-name]/` ディレクトリを作成

**Step 2**: `.claude-plugin/plugin.json` を作成（`name`フィールド必須）

**Step 3**: 必要なコンポーネントを追加:

- `commands/` - スラッシュコマンド
- `agents/` - サブエージェント
- `skills/` - スキル
- `hooks/hooks.json` - フック
- `.mcp.json` - MCPサーバー

**Step 4**: `README.md` を作成。以下の3セクションは**必須**（`.claude/rules/plugin-readme.md` 参照）:

- `## 概要` または `## Overview` — プラグインが何をするか
- `## インストール` または `## Installation` — インストール手順
- `## 使い方` または `## Usage` — 基本的な使用方法

**Step 5**: `.claude-plugin/marketplace.json` の `plugins` 配列にエントリを追加（`.claude/rules/marketplace.md` 参照）:

- `name`: プラグイン名（kebab-case）
- `source`: `./plugins/[plugin-name]`
- `description`: プラグインの説明

その他オプションフィールド（`version`, `author`, `homepage`, `repository`, `license`, `keywords`, `category`）も既存エントリに合わせて記載する。

**Step 6**: バリデーションを実行し、エラー・警告がないことを確認:

```bash
python3 scripts/validate_plugin.py plugins/[plugin-name]/README.md plugins/[plugin-name]/commands/*.md plugins/[plugin-name]/.claude-plugin/plugin.json .claude-plugin/marketplace.json
```

ファイル構成に応じて引数は調整すること（agents/, hooks/ 等がある場合は追加）。

## 必須フィールド

- `plugin.json`: `name`（kebab-case）
- コマンド: frontmatterに`description`
- エージェント: frontmatterに`name`と`description`
- `README.md`: 概要・インストール・使い方の3セクション
- `marketplace.json`: `name`と`source`
