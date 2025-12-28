# プラグイン作成スキル

Claude Codeマーケットプレイス用のプラグインを作成します。

## ディレクトリ構造

プラグインは以下の構造で `plugins/` に配置します：

```
plugins/[plugin-name]/
├── .claude-plugin/
│   └── plugin.json       # 必須：プラグインマニフェスト
├── commands/             # スラッシュコマンド
│   └── [command-name].md
├── agents/               # サブエージェント
│   └── [agent-name].md
├── hooks/                # フック
│   └── hooks.json
├── .mcp.json             # MCPサーバー設定
└── README.md             # プラグイン説明
```

## 命名規則

| 項目 | 規則 | 例 |
|------|------|-----|
| プラグイン名 | kebab-case | `my-awesome-plugin` |
| コマンドファイル | kebab-case.md | `review-code.md` |
| エージェントファイル | kebab-case.md | `code-reviewer.md` |

## 作成手順

1. `plugins/[plugin-name]/` ディレクトリを作成
2. `.claude-plugin/plugin.json` を作成（必須）
3. 必要なコンポーネントを追加：
   - `commands/` - スラッシュコマンド
   - `agents/` - サブエージェント
   - `hooks/hooks.json` - フック
   - `.mcp.json` - MCPサーバー
4. `README.md` でプラグインを説明

## 必須要件

- `.claude-plugin/plugin.json` に `name` フィールドが必須
- コマンドとエージェントには `description` フィールドが必須

## 検証

作成後は以下のコマンドで検証：

```bash
claude plugin validate ./plugins/[plugin-name]
```
