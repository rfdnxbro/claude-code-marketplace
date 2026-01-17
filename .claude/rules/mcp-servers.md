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

### SSE（Server-Sent Events）

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

## リソース参照

MCPリソースはプロンプトで参照可能：

```text
@server-name:protocol://resource/path
```

例: `@github:issue://123`

## 出力制限

デフォルト: 25,000トークン

環境変数で変更可能：

```bash
export MAX_MCP_OUTPUT_TOKENS=50000
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

## セキュリティ注意事項

機密情報（APIキー、トークン等）は環境変数経由で渡し、直接記述しないこと。

```json
// 良い例
"env": { "API_KEY": "${API_KEY}" }

// 悪い例（機密情報を直接記述）
"env": { "API_KEY": "sk-xxxx..." }
```

プラグイン配布時は `.mcp.json` に機密情報が含まれていないことを確認する。
