# ルールドキュメント索引

このディレクトリにはClaude Codeプラグイン開発のためのルールドキュメントが含まれています。

## ファイル一覧

| ファイル | 概要 |
|---------|------|
| [plugin-manifest.md](plugin-manifest.md) | プラグインの定義ファイル（`plugin.json`）の仕様 |
| [marketplace.md](marketplace.md) | マーケットプレイス設定（`marketplace.json`）の仕様 |
| [agents.md](agents.md) | サブエージェントの定義方法 |
| [hooks.md](hooks.md) | フック（イベントハンドラ）の定義方法 |
| [mcp-servers.md](mcp-servers.md) | MCPサーバーの設定方法 |
| [lsp-servers.md](lsp-servers.md) | LSPサーバーの設定方法 |
| [skill-authoring.md](skill-authoring.md) | スキル作成のベストプラクティス |
| [slash-commands.md](slash-commands.md) | スラッシュコマンドの定義方法 |
| [plugin-readme.md](plugin-readme.md) | プラグインREADMEの作成ガイドライン |
| [output-styles.md](output-styles.md) | 出力スタイルの定義方法 |
| [statusline.md](statusline.md) | ステータスラインのカスタマイズ方法 |

## 用語集

| 用語 | 説明 |
|------|------|
| kebab-case | 単語をハイフンで繋ぐ命名規則。例: `my-plugin-name` |
| フロントマター | Markdownファイル冒頭の`---`で囲まれたYAMLメタデータ領域 |
| MCP | Model Context Protocol。Claude Codeが外部サービスと通信するためのプロトコル |
| SSE | Server-Sent Events。サーバーからクライアントへの一方向ストリーミング通信 |
| LSP | Language Server Protocol。エディタと言語サーバー間の標準プロトコル |
| PRFAQ | Press Release/Frequently Asked Questions。Amazonで生まれた製品企画手法 |
| DDD | Domain-Driven Design（ドメイン駆動設計）。複雑なソフトウェア設計のアプローチ |

## 環境変数リファレンス

プラグイン内で使用可能な環境変数:

| 変数 | 説明 | 使用箇所 |
|------|------|----------|
| `${CLAUDE_PLUGIN_ROOT}` | プラグインルートへの絶対パス | hooks, mcp-servers, lsp-servers, allowed-tools |
| `${CLAUDE_PROJECT_DIR}` | プロジェクトルートへの絶対パス | hooks |
| `${CLAUDE_SESSION_ID}` | 現在のセッションID | skills, slash-commands |
| `$ARGUMENTS` | フック入力JSON / コマンド引数（全体） | hooks, slash-commands |
| `$ARGUMENTS[0]`, `$ARGUMENTS[1]`... | インデックス指定引数（ブラケット記法） | slash-commands |
| `$0` | コマンド名自体（v2.1.19以降） | slash-commands |
| `$1`, `$2`, `$3`... | 位置指定引数のショートハンド（v2.1.19以降） | slash-commands |
| `${VAR}` | 任意の環境変数を展開 | mcp-servers, lsp-servers |
| `${VAR:-default}` | デフォルト値付き環境変数 | mcp-servers, lsp-servers |
| `CLAUDE_CODE_PLUGIN_GIT_TIMEOUT_MS` | Gitクローンのタイムアウト（ミリ秒）。デフォルト120000（120秒）（v2.1.51以降） | marketplace |
