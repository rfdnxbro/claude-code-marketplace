# Claude Code Marketplace

[![テスト](https://github.com/rfdnxbro/claude-code-marketplace/actions/workflows/test-scripts.yml/badge.svg)](https://github.com/rfdnxbro/claude-code-marketplace/actions/workflows/test-scripts.yml)
![カバレッジ](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/rfdnxbro/584b9ff17fd95a2c4aa38dcf30c5a391/raw/coverage.json)

Claude Codeの機能を拡張するプラグイン（スラッシュコマンド、MCPサーバー、フック、サブエージェント）を管理・配布するための個人プロジェクトです。

## 概要

このリポジトリは、Claude Code向けのカスタムプラグインを開発・管理するためのプラットフォームです。

### 対応プラグインタイプ

| タイプ | 説明 |
|--------|------|
| **スラッシュコマンド** | `/`で始まるカスタムコマンド（例: `/review`, `/commit`） |
| **サブエージェント** | 特定タスクに特化した専門エージェント |
| **スキル** | Claudeの知識を拡張する再利用可能な指示セット |
| **フック** | Claude Codeのイベントに応じて実行されるスクリプト |
| **MCPサーバー** | Model Context Protocolを使用した外部ツール連携 |
| **LSPサーバー** | Language Server Protocolを使用したコード補完・診断 |
| **出力スタイル** | Claudeの応答フォーマットをカスタマイズするスタイル定義 |
| **ステータスライン** | ターミナル下部の情報バーをカスタマイズするスクリプト |
| **モニター** | 常駐シェルコマンドのstdoutをClaudeへの通知として配信する仕組み（v2.1.105以降） |

## 公開プラグイン

| プラグイン | 説明 | 状態 |
|-----------|------|------|
| [pr-auto-fix](plugins/pr-auto-fix/) | PRのCI失敗・レビュー・コンフリクトを自動検知し、自明な範囲で修正してcommit & push | 🔧 開発中 |
| [claude-code-workflow](plugins/claude-code-workflow/) | Claude Codeの個人的な作業スタイル（エージェント編成、文体ガイド等）をスキルとして集約 | 🔧 開発中 |

## ディレクトリ構成

```text
claude-code-marketplace/
├── .claude/
│   ├── rules/              # ルールドキュメント
│   ├── skills/             # マーケットプレイス開発用スキル
│   │   └── create-plugin/
│   │       └── SKILL.md
│   └── settings.json       # プラグイン検証hookの設定
├── .claude-plugin/
│   └── marketplace.json    # マーケットプレイス設定（プラグイン一覧）
├── .github/
│   └── workflows/          # CI/CDワークフロー
├── plugins/                # プラグイン
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
│       ├── .claude/
│       │   └── output-styles/ # 出力スタイル
│       │       └── [style].md
│       ├── settings.json   # デフォルト設定
│       ├── docs/           # ドキュメント（オプション）
│       ├── scripts/        # スクリプト（オプション）
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
| ステータスライン | `.claude/settings.json` または `.claude/settings.local.json` に設定 |
| 出力スタイル (`.md`) | `.claude/output-styles/` または `~/.claude/output-styles/` |

## 開発

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

### ローカル検証（pre-commit）

コミット時に以下の検証が自動実行されます:

| 検証項目 | 説明 |
|---------|------|
| gitleaks | 機密情報（APIキー、トークン等）の検出 |
| ruff | Python lint/format（`scripts/`配下） |
| markdownlint | Markdown構文検証 |
| yamllint | YAML構文検証（`.github/workflows/`配下） |
| validate-plugin | プラグインファイル検証（`plugins/`配下） |
| pytest | テスト実行（push時のみ） |

初回セットアップ方法は[プラグインの検証](#プラグインの検証)セクションを参照してください。

### CI/CD

PRおよびpush時に以下のワークフローが実行されます:

| ワークフロー | トリガー | 説明 |
|-------------|---------|------|
| プラグイン検証 | `plugins/**`変更時 | プラグインファイルのバリデーション |
| テスト（scripts） | `scripts/**`変更時 | pytest実行、カバレッジ測定 |
| Lint | 各種ファイル変更時 | ruff、markdownlint、yamllint |
| セキュリティスキャン | PR/push時 | gitleaksで機密情報検出 |
| Claude Code Review | PR作成/更新時 | Claude Codeによるコードレビュー |
| Claude Code | Issueコメント/PR reviewコメント/Issue assign時 | Claude Codeによるタスク実行 |
| Claude Code自動更新対応 | Issue labeling時 | Claude Codeによるドキュメント・プラグイン更新 |
| PR自動アサイン | PR作成時 | リポジトリオーナーをassignee/reviewerに自動設定 |
| プラグイン改善チェック | PR close時 | プラグイン改善提案の検出 |
| Claude Code CHANGELOG監視 | 日次 | Claude Code公式の変更検出 |

#### プラグイン検証の対象

- `plugin.json` - プラグインマニフェスト
- `commands/*.md` - スラッシュコマンド
- `agents/*.md` - サブエージェント
- `SKILL.md` - スキル
- `hooks.json` - フック設定
- `.mcp.json` - MCPサーバー設定
- `.lsp.json` - LSPサーバー設定
- `README.md` - プラグインREADME
- `output-styles/*.md` - 出力スタイル
- `settings.json` / `settings.local.json` - ステータスライン設定

#### カバレッジバッジのセットアップ

カバレッジバッジを有効にするには以下の設定が必要です：

1. [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)で`gist`スコープのトークンを生成
2. リポジトリのSecrets（`GIST_SECRET`）にトークンを設定
3. リポジトリのVariables（`COVERAGE_GIST_ID`）に`584b9ff17fd95a2c4aa38dcf30c5a391`を設定

#### CHANGELOG監視

Claude Code公式リポジトリのCHANGELOGを毎日監視し、プラグイン関連の変更を自動検出します。

変更が検出されると：

1. 自動でIssueが作成される
2. 必要に応じてドキュメント修正のPRが作成される

セットアップ:

1. リポジトリのSecretsに `ANTHROPIC_API_KEY` を設定
2. GitHub Actionsを有効化

```bash
# 手動でワークフローを実行する場合
gh workflow run changelog-monitor.yml
```

検出対象:

- plugin.json / marketplace.json の仕様変更
- フロントマターの新規フィールドや変更
- 新しいコンポーネントタイプの追加
- 既存仕様の非推奨化や削除
- MCP、フック、スキル、エージェントの仕様変更

### 依存関係の自動更新

Dependabotにより、GitHub Actionsの依存関係が週次で自動更新されます。

## 関連リンク

- [Claude Code 公式ドキュメント](https://code.claude.com/docs/en)
- [Claude Code GitHub](https://github.com/anthropics/claude-code)
- [Model Context Protocol](https://modelcontextprotocol.io/)

## ライセンス

MIT License

### サードパーティコンテンツ

`.changelog-snapshot.md` はClaude Code公式リポジトリのCHANGELOGのスナップショットであり、Anthropic, PBC の著作物です。このファイルはCHANGELOG監視機能の差分検出のために使用されており、元のライセンスはAnthropicに帰属します。

- 元ファイル: <https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md>
- 著作権: © Anthropic, PBC

---

**注意**: このリポジトリは個人プロジェクトであり、Anthropic社の公式プロジェクトではありません。
