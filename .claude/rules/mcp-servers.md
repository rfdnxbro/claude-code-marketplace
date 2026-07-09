---
paths: plugins/*/.mcp.json
---

# MCPサーバー

JSON形式で記述します。配置場所はプラグインルートの `.mcp.json`。

## 形式

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

## サーバータイプ

### Stdio（ローカル実行）

| フィールド | 必須 | 説明 |
|-----------|:---:|------|
| `type` | ✓ | `"stdio"` |
| `command` | ✓ | 実行コマンド |
| `args` | - | コマンド引数 |
| `env` | - | 環境変数 |

#### Stdio MCPサーバーサブプロセスが受け取る環境変数

Stdio MCPサーバーのサブプロセスは以下の環境変数を自動的に受け取ります:

| 変数 | 値 | 説明 |
|------|---|------|
| `CLAUDE_CODE_SESSION_ID` | セッションID文字列 | 現在のClaude Codeセッションの識別子 |
| `CLAUDECODE` | `1` | Claude Codeから起動されたことを示すフラグ |

```json
{
  "server-name": {
    "type": "stdio",
    "command": "${CLAUDE_PLUGIN_ROOT}/servers/my-server",
    "args": ["--config", "${CLAUDE_PLUGIN_ROOT}/config.json"],
    "env": {
      "DB_URL": "${DB_URL}"
    }
  }
}
```

### HTTP（リモート）

| フィールド | 必須 | 説明 |
|-----------|:---:|------|
| `type` | ✓ | `"http"` |
| `url` | ✓ | サーバーURL |
| `headers` | - | 認証ヘッダー等 |
| `headersHelper` | - | ヘッダー生成コマンド |

```json
{
  "server-name": {
    "type": "http",
    "url": "https://api.example.com/mcp",
    "headers": {
      "Authorization": "Bearer ${API_TOKEN}"
    }
  }
}
```

#### headersHelper

動的にヘッダーを生成する場合は`headersHelper`を使用:

```json
{
  "server-name": {
    "type": "http",
    "url": "https://api.example.com/mcp",
    "headersHelper": "${CLAUDE_PLUGIN_ROOT}/scripts/get-auth-headers.sh"
  }
}
```

ヘルパースクリプトはJSON形式でヘッダーを出力:

```bash
#!/bin/bash
echo '{"Authorization": "Bearer '$(get-token)'"}'
```

#### headersHelper 内で利用可能な環境変数

`headersHelper` スクリプト内では以下の環境変数が利用可能です:

| 変数 | 説明 |
|------|------|
| `CLAUDE_CODE_MCP_SERVER_NAME` | 呼び出し元の MCP サーバー名 |
| `CLAUDE_CODE_MCP_SERVER_URL` | 呼び出し元の MCP サーバー URL |

1つのヘルパースクリプトで複数のサーバーに対応できます:

```bash
#!/bin/bash
# CLAUDE_CODE_MCP_SERVER_NAME を使って認証情報を切り替える
case "$CLAUDE_CODE_MCP_SERVER_NAME" in
  "server-a")
    echo '{"Authorization": "Bearer '$(get-token-a)'"}'
    ;;
  "server-b")
    echo '{"Authorization": "Bearer '$(get-token-b)'"}'
    ;;
esac
```

### WebSocket

| フィールド | 必須 | 説明 |
|-----------|:---:|------|
| `type` | ✓ | `"ws"` |
| `url` | ✓ | WebSocketサーバーURL |

```json
{
  "server-name": {
    "type": "ws",
    "url": "wss://api.example.com/mcp"
  }
}
```

### SSE（Server-Sent Events）【非推奨】

> **注意**: SSEトランスポートは非推奨（deprecated）です。新規実装ではHTTPトランスポートの使用を推奨します。

| フィールド | 必須 | 説明 |
|-----------|:---:|------|
| `type` | ✓ | `"sse"` |
| `url` | ✓ | サーバーURL |

```json
{
  "server-name": {
    "type": "sse",
    "url": "https://api.example.com/sse"
  }
}
```

## 環境変数

- `${VAR}` - 環境変数を展開
- `${VAR:-default}` - デフォルト値付き
- `${CLAUDE_PLUGIN_ROOT}` - プラグインルートへの絶対パス
- `${CLAUDE_PROJECT_DIR}` - プロジェクトルートへの絶対パス（stdioサーバーの `command`・`args`・`env` フィールドで参照可能）

`${CLAUDE_PROJECT_DIR}` の使用例:

```json
{
  "server-name": {
    "type": "stdio",
    "command": "${CLAUDE_PLUGIN_ROOT}/servers/my-server",
    "args": ["--project", "${CLAUDE_PROJECT_DIR}"],
    "env": {
      "PROJECT_DIR": "${CLAUDE_PROJECT_DIR}"
    }
  }
}
```

### POSIXシェルパラメータ展開

MCP設定ではPOSIXシェルパラメータ展開の各形式がサポートされています:

| 形式 | 説明 |
|------|------|
| `${VAR}` | 変数展開 |
| `${VAR:-default}` | 未設定時にデフォルト値を使用 |
| `${VAR%pattern}` | 末尾から最短マッチを削除 |
| `${VAR%%pattern}` | 末尾から最長マッチを削除 |
| `${VAR#pattern}` | 先頭から最短マッチを削除 |
| `${VAR##pattern}` | 先頭から最長マッチを削除 |

```json
{
  "server-name": {
    "type": "stdio",
    "command": "node",
    "args": ["${CLAUDE_PLUGIN_ROOT}/server.js"],
    "env": {
      "BASE_URL": "${API_URL%/}"
    }
  }
}
```

## リソース参照

MCPリソースはプロンプトで参照可能：

```text
@server-name:protocol://resource/path
```

例: `@github:issue://123`

## プロンプト参照

MCPサーバーが提供するプロンプトはスラッシュコマンドとして使用可能:

```text
/mcp__servername__promptname
```

## 出力制限

デフォルト: 25,000トークン

環境変数で変更可能：

```bash
export MAX_MCP_OUTPUT_TOKENS=50000
```

## タイムアウト

| 設定 | 説明 |
|------|------|
| `timeout`（`.mcp.json` のサーバーエントリ） | そのサーバーのツール実行タイムアウト（ミリ秒）。例: `"timeout": 600000`（10分）。そのサーバーに限り `MCP_TOOL_TIMEOUT` を上書きする。ツール呼び出しごとの厳密な wall-clock 上限で、進捗通知では延長されない。1000未満の値は無視され `MCP_TOOL_TIMEOUT`（未設定時は約28時間）にフォールバックする |
| `MCP_TIMEOUT`（環境変数） | MCPサーバーの起動タイムアウト（ミリ秒）。例: `MCP_TIMEOUT=10000 claude` |
| `MCP_TOOL_TIMEOUT`（環境変数） | ツール実行タイムアウトのデフォルト（ミリ秒）。サーバー個別の `timeout` で上書き可能 |

```json
{
  "mcpServers": {
    "slow-server": {
      "type": "http",
      "url": "https://mcp.example.com/mcp",
      "timeout": 600000
    }
  }
}
```

## ツール許可パターン

MCPサーバーのツールは `mcp__サーバー名__ツール名` の形式で参照されます。

### ワイルドカード構文

```yaml
# 特定のツールを許可
allowed-tools: mcp__github__create_issue

# 特定サーバーの全ツールを許可
allowed-tools: mcp__github__*

# 複数パターン
allowed-tools:
  - mcp__github__create_issue
  - mcp__github__list_issues
  - mcp__slack__*
```

## 動的更新通知

MCPサーバーはツールやリソースの変更を通知できます（`list_changed` notifications）:

- ツール一覧の変更をクライアントに通知
- リソース一覧の変更をクライアントに通知
- クライアントは通知を受けて一覧を再取得

これにより、サーバー側でツールを動的に追加・削除できます。

## OAuth認証

MCPサーバーのOAuth認証をサポートしています。

多くのリモートMCPサーバーはOAuth 2.0認証を必要とします。リモートサーバーが `401 Unauthorized` または `403 Forbidden` を返すと、Claude Code はそのサーバーを認証要と判定し `/mcp` で OAuth フローを実行できます。通常は Dynamic Client Registration により自動でセットアップされます。

### 事前設定されたOAuth認証情報を使用する

Dynamic Client Registration をサポートしないサーバー（事前にOAuthアプリを作成してClient ID/Client Secretを取得する必要があるサーバー）では、`claude mcp add` 時に認証情報を渡します。`--client-secret` は**値を引数に取らず、マスク入力でシークレットの入力を求めるフラグ**です（コマンドライン履歴にシークレットが残りません）。HTTP/SSE トランスポートでのみ有効です。

```bash
claude mcp add --transport http \
  --client-id <CLIENT_ID> --client-secret --callback-port 8080 \
  <server-name> https://mcp.example.com/mcp
```

- `--callback-port` は事前登録した `http://localhost:PORT/callback` 形式のリダイレクトURIに合わせる場合に使用します。
- 公開OAuthクライアント（シークレットなし）では `--client-id` のみを指定し `--client-secret` は付けません。
- 入力したシークレットは設定ファイルではなくシステムキーチェーン（macOS）または認証情報ファイルに安全に保存されます。

CI など非対話環境では `MCP_CLIENT_SECRET` 環境変数でプロンプトをスキップできます:

```bash
MCP_CLIENT_SECRET=your-secret claude mcp add --transport http \
  --client-id <CLIENT_ID> --client-secret --callback-port 8080 \
  <server-name> https://mcp.example.com/mcp
```

### OAuthメタデータ探索の上書き

サーバーの標準エンドポイントがエラーになる場合や、社内プロキシ経由で探索したい場合は、`.mcp.json` の各サーバー設定の `oauth` オブジェクトに `authServerMetadataUrl`（`https://` 必須）を指定して探索チェーンをバイパスできます。`oauth.scopes`（スペース区切りの1文字列）で要求スコープを固定することもできます。

```json
{
  "mcpServers": {
    "my-server": {
      "type": "http",
      "url": "https://mcp.example.com/mcp",
      "oauth": {
        "authServerMetadataUrl": "https://auth.example.com/.well-known/openid-configuration"
      }
    }
  }
}
```

### 注意事項

- プラグインの `.mcp.json` には認証情報を直接記述しない（OAuthはキーチェーン/認証情報ファイルに保存される）
- これらのフラグは HTTP/SSE トランスポート専用で、stdio サーバーには効果がありません

## claude.ai MCP コネクター

claude.ai アカウントで Claude Code にログインしていれば、claude.ai 側で追加した MCP サーバー（コネクター）が **Claude Code で自動的に利用可能**になります。専用の追加コマンドはありません。

### 設定方法

1. [claude.ai/customize/connectors](https://claude.ai/customize/connectors) でサーバーを追加する（Team/Enterprise プランでは管理者のみ追加可能）
2. claude.ai 側で必要な認証を完了する
3. Claude Code を claude.ai アカウントでログインして起動すると、`/mcp` の一覧に claude.ai 由来であることを示すインジケーター付きで表示される

### 注意事項

- claude.ai 由来のコネクターを使うには claude.ai アカウントへのログインが必要です
- `ENABLE_CLAUDEAI_MCP_SERVERS=false` 環境変数を設定すると、claude.ai MCPサーバーの利用をオプトアウトできます

## ツール検索（Tool Search）

MCPサーバーのツール数が多い場合、ツール説明がコンテキストウィンドウを圧迫します。ツール検索機能を使用すると、必要なときだけツール説明をロードできます。

### 設定

`ENABLE_TOOL_SEARCH`環境変数で制御:

| 値 | 説明 |
|---|------|
| `auto`（デフォルト） | ツール説明がコンテキストの10%を超える場合に自動有効化 |
| `auto:N` | ツール説明がコンテキストのN%を超える場合に自動有効化 |
| `true` | 常に有効 |
| `false` | 無効 |

### alwaysLoad オプション

サーバー設定に `alwaysLoad: true` を指定すると、ツール検索による遅延ロードをスキップし、そのサーバーのツールが常に利用可能な状態でロードされます。

```json
{
  "mcpServers": {
    "server-name": {
      "type": "stdio",
      "command": "...",
      "alwaysLoad": true
    }
  }
}
```

| フィールド | 型 | 説明 |
|-----------|---|------|
| `alwaysLoad` | boolean | `true` にするとツール検索による遅延ロードを無効化し、常にツールをロードする。省略時は従来通り遅延ロードが適用される |

## 予約済みサーバー名

以下のサーバー名は予約済みです。これらの名前を `.mcp.json` の `mcpServers` キーに使用すると、警告が表示されてスキップされます:

| サーバー名 |
|-----------|
| `workspace` |
| `Claude Browser` |
| `Claude Preview` |

## セキュリティ注意事項

機密情報（APIキー、トークン等）は環境変数経由で渡し、直接記述しないこと。

```json
// 良い例
"env": { "API_KEY": "${API_KEY}" }

// 悪い例（機密情報を直接記述）
"env": { "API_KEY": "sk-xxxx..." }
```

プラグイン配布時は `.mcp.json` に機密情報が含まれていないことを確認する。
