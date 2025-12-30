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
├── .claude/
│   ├── rules/              # ルールドキュメント
│   ├── skills/             # マーケットプレイス開発用スキル
│   │   └── create-plugin/
│   │       └── SKILL.md
│   └── settings.json       # プラグイン検証hookの設定
├── .github/
│   └── workflows/          # CI/CDワークフロー
├── plugins/                # 公開プラグイン（コントリビューション先）
│   └── [plugin-name]/
│       ├── .claude-plugin/
│       │   └── plugin.json # プラグインマニフェスト（必須）
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
├── scripts/                # プラグイン検証スクリプト
│   ├── validators/         # 検証ロジック
│   └── tests/              # テスト
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
# Pythonスクリプトで検証
python3 scripts/validate_plugin.py ./plugins/my-plugin

# テストを実行
uvx pytest scripts/tests/ -v
```

## CI/CD

### プラグイン検証

`plugins/`配下のファイルが変更されると、自動的に検証スクリプトが実行されます。

検証対象:

- `plugin.json` - プラグインマニフェスト
- `commands/*.md` - スラッシュコマンド
- `agents/*.md` - サブエージェント
- `SKILL.md` - スキル
- `hooks.json` - フック設定
- `.mcp.json` - MCPサーバー設定

### スクリプトテスト

`scripts/`配下のファイルが変更されると、自動的にpytestが実行されます。

### CHANGELOG監視

Claude Code公式リポジトリのCHANGELOGを毎日監視し、プラグイン関連の変更を自動検出します。

変更が検出されると：
1. 自動でIssueが作成される
2. 必要に応じてドキュメント修正のPRが作成される

#### セットアップ

1. リポジトリのSecretsに `ANTHROPIC_API_KEY` を設定
2. GitHub Actionsを有効化

```bash
# 手動でワークフローを実行する場合
gh workflow run changelog-monitor.yml
```

#### 検出対象

- plugin.json / marketplace.json の仕様変更
- フロントマターの新規フィールドや変更
- 新しいコンポーネントタイプの追加
- 既存仕様の非推奨化や削除
- MCP、フック、スキル、エージェントの仕様変更

## 関連リンク

- [Claude Code 公式ドキュメント](https://docs.anthropic.com/en/docs/claude-code)
- [Claude Code GitHub](https://github.com/anthropics/claude-code)
- [Model Context Protocol](https://modelcontextprotocol.io/)

## ライセンス

MIT License

---

**注意**: このリポジトリはコミュニティ主導のプロジェクトであり、Anthropic社の公式プロジェクトではありません。
