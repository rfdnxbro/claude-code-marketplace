# Claude Code Marketplace

Claude Codeの機能を拡張するプラグイン（スラッシュコマンド、MCPサーバー、フック、サブエージェント）を共有・発見できるマーケットプレイスです。

## 概要

このリポジトリは、Claude Codeユーザーが作成したカスタムプラグインを集約し、コミュニティで共有するためのプラットフォームです。

### 対応プラグインタイプ

| タイプ | 説明 |
|--------|------|
| **スラッシュコマンド** | `/`で始まるカスタムコマンド（例: `/review`, `/commit`） |
| **サブエージェント** | 特定タスクに特化した専門エージェント |
| **スキル** | Claudeの知識を拡張する再利用可能な指示セット |
| **フック** | Claude Codeのイベントに応じて実行されるスクリプト |
| **MCPサーバー** | Model Context Protocolを使用した外部ツール連携 |

## ディレクトリ構成

```
claude-code-marketplace/
├── .claude-plugin/
│   └── marketplace.json    # マーケットプレイス設定
├── plugins/
│   └── [plugin-name]/      # 各プラグイン
│       ├── .claude-plugin/
│       │   └── plugin.json # プラグインマニフェスト
│       ├── commands/       # スラッシュコマンド
│       │   └── [command].md
│       ├── agents/         # サブエージェント
│       │   └── [agent].md
│       ├── skills/         # スキル
│       │   └── [skill-name]/
│       │       └── SKILL.md
│       ├── hooks/          # フック
│       │   └── hooks.json
│       ├── .mcp.json       # MCPサーバー設定
│       └── README.md
└── README.md
```

## プラグインの使い方

### CLIでインストール（推奨）

```bash
# このマーケットプレイスを登録
/plugin marketplace add <このリポジトリのURL>

# プラグイン一覧を表示
/plugin install

# プラグインをインストール
/plugin install <plugin-name>

# スコープを指定してインストール
/plugin install <plugin-name> --scope project  # プロジェクト共有
/plugin install <plugin-name> --scope user     # 個人用（デフォルト）
```

### ローカルでテスト

```bash
# プラグインディレクトリを指定して起動
claude --plugin-dir ./plugins/my-plugin
```

### 手動インストール

個別のコンポーネントのみ使用する場合：

| コンポーネント | コピー先 |
|--------------|---------|
| コマンド (`.md`) | `.claude/commands/` または `~/.claude/commands/` |
| エージェント (`.md`) | `.claude/agents/` または `~/.claude/agents/` |
| スキル (`SKILL.md`) | `.claude/skills/[name]/` または `~/.claude/skills/[name]/` |
| フック (`hooks.json`) | `.claude/settings.json` に統合 |
| MCP (`.mcp.json`) | プロジェクトルートの `.mcp.json` に統合 |

## コントリビューション

プラグインの追加・改善は大歓迎です！

### プラグインの追加方法

1. このリポジトリをフォーク
2. `plugins/` に新しいプラグインディレクトリを作成
3. `.claude-plugin/plugin.json` を作成（必須）
4. 必要なコンポーネント（commands/, agents/, skills/, hooks/, .mcp.json）を追加
5. README.mdを含めてドキュメントを整備
6. プルリクエストを作成

### プラグイン作成ガイドライン

- `.claude-plugin/plugin.json` に `name` を必ず記載（kebab-case）
- 各プラグインには `README.md` を含める
- スラッシュコマンドとエージェントには `description` を必ず記載
- 使用方法、設定例、依存関係を明記する
- ライセンスを明記する（デフォルト: MIT）

### プラグインの検証

```bash
claude plugin validate ./plugins/my-plugin
```

## 関連リンク

- [Claude Code 公式ドキュメント](https://docs.anthropic.com/en/docs/claude-code)
- [Claude Code GitHub](https://github.com/anthropics/claude-code)
- [Model Context Protocol](https://modelcontextprotocol.io/)

## ライセンス

MIT License

---

**注意**: このリポジトリはコミュニティ主導のプロジェクトであり、Anthropic社の公式プロジェクトではありません。
