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

## 環境変数

- `${VAR}` - 環境変数を展開
- `${VAR:-default}` - デフォルト値付き
- `${CLAUDE_PLUGIN_ROOT}` - プラグインルートへの絶対パス
