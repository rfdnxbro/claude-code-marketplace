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
| [channels.md](channels.md) | チャンネル（MCPサーバーからのイベント注入）の設定方法 |
| [lsp-servers.md](lsp-servers.md) | LSPサーバーの設定方法 |
| [monitors.md](monitors.md) | バックグラウンドモニターの定義方法 |
| [skill-authoring.md](skill-authoring.md) | スキル作成のベストプラクティス |
| [slash-commands.md](slash-commands.md) | スラッシュコマンドの定義方法 |
| [plugin-readme.md](plugin-readme.md) | プラグインREADMEの作成ガイドライン |
| [output-styles.md](output-styles.md) | 出力スタイルの定義方法 |
| [statusline.md](statusline.md) | ステータスラインのカスタマイズ方法 |
| [contribution-guide.md](contribution-guide.md) | ドキュメント変更ガイドライン・追跡方針 |

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
| `${CLAUDE_PLUGIN_ROOT}` | プラグインルートへの絶対パス | hooks, mcp-servers, lsp-servers, monitors, allowed-tools |
| `${CLAUDE_PROJECT_DIR}` | プロジェクトルートへの絶対パス | hooks, mcp-servers（v2.1.139以降） |
| `${CLAUDE_SESSION_ID}` | 現在のセッションID | skills, slash-commands |
| `${CLAUDE_SKILL_DIR}` | スキル自身のディレクトリへの絶対パス（v2.1.64以降） | skills |
| `$ARGUMENTS` | フック入力JSON / コマンド引数（全体） | hooks, slash-commands |
| `$ARGUMENTS[0]`, `$ARGUMENTS[1]`... | インデックス指定引数（ブラケット記法） | slash-commands |
| `$0` | コマンド名自体（v2.1.19以降） | slash-commands |
| `$1`, `$2`, `$3`... | 位置指定引数のショートハンド（v2.1.19以降） | slash-commands |
| `${VAR}` | 任意の環境変数を展開 | mcp-servers, lsp-servers |
| `${VAR:-default}` | デフォルト値付き環境変数 | mcp-servers, lsp-servers |
| `CLAUDE_CODE_PLUGIN_GIT_TIMEOUT_MS` | Gitクローンのタイムアウト（ミリ秒）。デフォルト120000（120秒）（v2.1.51以降） | marketplace |
| `CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS` | `SessionEnd` フックのタイムアウト（ミリ秒）。デフォルトは `hook.timeout` の設定値（v2.1.74以降） | hooks |
| `${CLAUDE_PLUGIN_DATA}` | プラグインの永続データディレクトリへの絶対パス。アップデートを超えて永続化される（v2.1.78以降） | hooks, monitors |
| `CLAUDE_CODE_PLUGIN_SEED_DIR` | プラグインのシードディレクトリ。v2.1.79以降は複数ディレクトリをパス区切り文字（Unix: `:`, Windows: `;`）で区切って指定可能 | marketplace |
| `CLAUDE_CODE_MCP_SERVER_NAME` | `headersHelper` スクリプト内で利用可能。呼び出し元の MCP サーバー名（v2.1.85以降） | mcp-servers |
| `CLAUDE_CODE_MCP_SERVER_URL` | `headersHelper` スクリプト内で利用可能。呼び出し元の MCP サーバー URL（v2.1.85以降） | mcp-servers |
| `CLAUDE_CODE_PLUGIN_KEEP_MARKETPLACE_ON_FAILURE` | `git pull` 失敗時に既存マーケットプレイスキャッシュを保持（v2.1.90以降） | marketplace |
| `CLAUDE_CODE_PLUGIN_PREFER_HTTPS` | GitHubプラグインソースをSSHの代わりにHTTPSでクローンする。SSH鍵がない環境（CI・企業ネットワーク等）向け（v2.1.141以降） | marketplace |
| `${CLAUDE_EFFORT}` | 現在のエフォートレベル。値: `low` / `medium` / `high` / `xhigh`（Opus 4.7のみ、他モデルは `high` にフォールバック） / `max`（v2.1.120以降） | skills, hooks（v2.1.133以降） |

## Frontmatterリファレンス

### paths: フィールドのフォーマット（v2.1.84以降）

`.claude/rules/*.md` や CLAUDE.md などのルールファイルの frontmatter で使用する `paths:` フィールドは、カンマ区切り文字列またはYAMLリスト形式で指定できます。`paths:` はルールファイルをスコープ指定するためのフィールドであり、スキルやエージェント等の定義ファイルのfrontmatterとは異なります。

**カンマ区切り形式（従来）:**

```yaml
---
paths: src/**/*.ts, lib/**/*.js
---
```

**YAMLリスト形式（v2.1.84以降）:**

```yaml
---
paths:
  - src/**/*.ts
  - lib/**/*.js
---
```

どちらの形式でも同じ動作をします。YAMLリスト形式はパスが多い場合に可読性が高くなります。

**注意:** 現時点では `paths:` フィールドのバリデーターは `scripts/validators/` に実装されていません。将来的にフロントマターのバリデーションを追加する際は、YAMLリスト形式にも対応が必要です。
