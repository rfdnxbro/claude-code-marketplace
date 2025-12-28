# Claude Code Marketplace

Claude Codeの機能を拡張するプラグイン（スラッシュコマンド、MCPサーバー、フック、サブエージェント）を共有・発見できるマーケットプレイスです。

## 概要

このリポジトリは、Claude Codeユーザーが作成したカスタムプラグインを集約し、コミュニティで共有するためのプラットフォームです。

### 対応プラグインタイプ

| タイプ | 説明 |
|--------|------|
| **スラッシュコマンド** | `/`で始まるカスタムコマンド（例: `/review`, `/commit`） |
| **MCPサーバー** | Model Context Protocolを使用した外部ツール連携 |
| **フック** | Claude Codeのイベントに応じて実行されるスクリプト |
| **サブエージェント** | 特定タスクに特化した専門エージェント |

## ディレクトリ構成

```
claude-code-marketplace/
├── commands/           # スラッシュコマンド
│   └── [category]/
│       └── [command-name].md
├── mcp-servers/        # MCPサーバー
│   └── [server-name]/
│       ├── README.md
│       └── .mcp.json
├── hooks/              # フック
│   └── [hook-name]/
│       ├── README.md
│       └── hooks.json
├── agents/             # サブエージェント
│   └── [agent-name].md
└── README.md
```

## ファイル形式

### スラッシュコマンド（`.md`）

Markdown + YAML Frontmatter形式：

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

### サブエージェント（`.md`）

Markdown + YAML Frontmatter形式：

```markdown
---
name: agent-name
description: エージェントの説明（必須）
tools: Read, Grep, Glob, Bash
model: inherit
---

エージェントのシステムプロンプト
```

### MCPサーバー（`.mcp.json`）

```json
{
  "mcpServers": {
    "server-name": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "server-package"],
      "env": {
        "API_KEY": "${API_KEY}"
      }
    }
  }
}
```

### フック（`hooks.json`）

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "script.sh"
          }
        ]
      }
    ]
  }
}
```

**対応イベント**: `PreToolUse`, `PostToolUse`, `UserPromptSubmit`, `Notification`, `Stop`, `SubagentStop` など

## プラグインの使い方

### スラッシュコマンドのインストール

1. 使いたいコマンドの`.md`ファイルをダウンロード
2. 以下のいずれかにコピー：
   - `.claude/commands/` （プロジェクト用・チーム共有）
   - `~/.claude/commands/` （個人用・全プロジェクト共通）
3. Claude Codeで`/[コマンド名]`を実行

### MCPサーバーのインストール

**CLIを使用（推奨）：**
```bash
# HTTPサーバー
claude mcp add --transport http <name> <url>

# Stdioサーバー
claude mcp add --transport stdio <name> -- <command> [args...]

# 環境変数付き
claude mcp add --transport stdio <name> --env API_KEY=xxx -- npx -y server
```

**手動設定：**
- プロジェクト用: `.mcp.json`
- 個人用: `~/.claude.json`

### フックのインストール

1. フック設定ファイルをダウンロード
2. 以下のいずれかに設定を追加：
   - `.claude/settings.json` （プロジェクト用）
   - `~/.claude/settings.json` （個人用）
   - `.claude/hooks/hooks.json` （別ファイル管理）

### サブエージェントのインストール

1. 使いたいエージェントの`.md`ファイルをダウンロード
2. 以下のいずれかにコピー：
   - `.claude/agents/` （プロジェクト用）
   - `~/.claude/agents/` （個人用）
3. Claude CodeがTaskツールで自動的に利用可能に

### プラグインとしてインストール

複数のコンポーネントをまとめてインストールする場合：

```bash
# マーケットプレイスを登録
/plugin marketplace add <marketplace-url>

# プラグインをインストール
/plugin install <plugin-name>

# ローカルでテスト
claude --plugin-dir ./path/to/plugin
```

## コントリビューション

プラグインの追加・改善は大歓迎です！

### プラグインの追加方法

1. このリポジトリをフォーク
2. 適切なディレクトリにプラグインを追加
3. READMEを含めてドキュメントを整備
4. プルリクエストを作成

### プラグイン作成ガイドライン

- 各プラグインには`README.md`を含める
- 使用方法、設定例、依存関係を明記する
- 可能であればスクリーンショットや使用例を追加する
- ライセンスを明記する（デフォルト: MIT）
- スラッシュコマンドとエージェントには`description`を必ず記載する

## 関連リンク

- [Claude Code 公式ドキュメント](https://docs.anthropic.com/en/docs/claude-code)
- [Claude Code GitHub](https://github.com/anthropics/claude-code)
- [Model Context Protocol](https://modelcontextprotocol.io/)

## ライセンス

MIT License

---

**注意**: このリポジトリはコミュニティ主導のプロジェクトであり、Anthropic社の公式プロジェクトではありません。
