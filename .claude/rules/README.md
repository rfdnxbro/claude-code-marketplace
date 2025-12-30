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
| [output-styles.md](output-styles.md) | 出力スタイルの定義方法 |

## 用語集

| 用語 | 説明 |
|------|------|
| kebab-case | 単語をハイフンで繋ぐ命名規則。例: `my-plugin-name` |
| フロントマター | Markdownファイル冒頭の`---`で囲まれたYAMLメタデータ領域 |
| MCP | Model Context Protocol。Claude Codeが外部サービスと通信するためのプロトコル |
| SSE | Server-Sent Events。サーバーからクライアントへの一方向ストリーミング通信 |
| LSP | Language Server Protocol。エディタと言語サーバー間の標準プロトコル |

## 環境変数リファレンス

プラグイン内で使用可能な環境変数:

| 変数 | 説明 | 使用箇所 |
|------|------|----------|
| `${CLAUDE_PLUGIN_ROOT}` | プラグインルートへの絶対パス | hooks, mcp-servers, lsp-servers |
| `${CLAUDE_PROJECT_DIR}` | プロジェクトルートへの絶対パス | hooks |
| `$ARGUMENTS` | フック入力JSON / コマンド引数 | hooks, slash-commands |
| `$1`, `$2`, `$3`... | 位置指定引数 | slash-commands |
| `${VAR}` | 任意の環境変数を展開 | mcp-servers, lsp-servers |
| `${VAR:-default}` | デフォルト値付き環境変数 | mcp-servers, lsp-servers |
