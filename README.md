# Claude Code Marketplace

[![テスト](https://github.com/rfdnxbro/claude-code-marketplace/actions/workflows/test-scripts.yml/badge.svg)](https://github.com/rfdnxbro/claude-code-marketplace/actions/workflows/test-scripts.yml)
![カバレッジ](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/rfdnxbro/584b9ff17fd95a2c4aa38dcf30c5a391/raw/coverage.json)

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
| **LSPサーバー** | Language Server Protocolを使用したコード補完・診断 |

## 公開プラグイン

| プラグイン | 説明 | 状態 |
|-----------|------|------|
| [ai-dlc](plugins/ai-dlc/) | AI駆動開発ライフサイクル（AI-DLC）のスラッシュコマンド、サブエージェント、スキルを提供 | 🚧 設計中 |

## ディレクトリ構成

```text
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
│       ├── .lsp.json       # LSPサーバー設定
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
| LSP (`.lsp.json`) | プロジェクトルートの `.lsp.json` に統合 |

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
# 初回セットアップ（pre-commitの導入）
brew install pre-commit  # または pip install pre-commit
pre-commit install

# 全ファイルを検証
pre-commit run --all-files

# 個別にPythonスクリプトで検証
python3 scripts/validate_plugin.py plugins/my-plugin/**/*.md plugins/my-plugin/**/*.json

# テストを実行
uvx pytest scripts/tests/ -v
```

## 品質保証

### pre-commitによるローカルチェック

コミット時に以下のチェックが自動実行されます:

| チェック | 説明 |
|---------|------|
| gitleaks | 機密情報（APIキー、トークン等）の検出 |
| ruff | Python lint/format（`scripts/`配下） |
| markdownlint | Markdown構文チェック |
| yamllint | YAML構文チェック（`.github/workflows/`配下） |
| validate-plugin | プラグインファイル検証（`plugins/`配下） |
| pytest | テスト実行（push時のみ） |

### CIによる自動チェック

PRおよびpush時に以下が実行されます:

| ワークフロー | トリガー | 説明 |
|-------------|---------|------|
| プラグイン検証 | `plugins/**`変更時 | プラグインファイルのバリデーション |
| スクリプトテスト | `scripts/**`変更時 | pytest実行、カバレッジ測定 |
| Lint | 各種ファイル変更時 | ruff、markdownlint、yamllint |
| セキュリティスキャン | PR/push時 | gitleaksで機密情報検出 |
| CHANGELOG監視 | 日次 | Claude Code公式の変更検出 |

### 依存関係の自動更新

Dependabotにより、GitHub Actionsの依存関係が週次で自動更新されます。

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
- `.lsp.json` - LSPサーバー設定
- `README.md` - プラグインREADME
- `output-styles/*.md` - 出力スタイル

### スクリプトテスト

`scripts/`配下のファイルが変更されると、自動的にpytestが実行されます。

#### カバレッジバッジのセットアップ

カバレッジバッジを有効にするには以下の設定が必要です：

1. [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)で`gist`スコープのトークンを生成
2. リポジトリのSecrets（`GIST_SECRET`）にトークンを設定
3. リポジトリのVariables（`COVERAGE_GIST_ID`）に`584b9ff17fd95a2c4aa38dcf30c5a391`を設定

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

### サードパーティコンテンツ

`.changelog-snapshot.md` はClaude Code公式リポジトリのCHANGELOGのスナップショットであり、Anthropic, PBC の著作物です。このファイルはCHANGELOG監視機能の差分検出のために使用されており、元のライセンスはAnthropicに帰属します。

- 元ファイル: <https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md>
- 著作権: © Anthropic, PBC

---

**注意**: このリポジトリはコミュニティ主導のプロジェクトであり、Anthropic社の公式プロジェクトではありません。
