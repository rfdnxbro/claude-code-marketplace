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

```
@server-name:protocol://resource/path
```

例: `@github:issue://123`

## 出力制限

デフォルト: 25,000トークン

環境変数で変更可能：
```bash
export MAX_MCP_OUTPUT_TOKENS=50000
```

## セキュリティ注意事項

機密情報（APIキー、トークン等）は環境変数経由で渡し、直接記述しないこと。

```json
// 良い例
"env": { "API_KEY": "${API_KEY}" }

// 悪い例（機密情報を直接記述）
"env": { "API_KEY": "sk-xxxx..." }
```

プラグイン配布時は `.mcp.json` に機密情報が含まれていないことを確認する。
