---
paths: plugins/*/.claude-plugin/plugin.json
---

# プラグインマニフェスト（plugin.json）

`.claude-plugin/plugin.json` はプラグインの必須ファイルです。

## 必須フィールド

- `name`: プラグイン識別子（kebab-case）

## 形式

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "プラグインの説明",
  "author": {
    "name": "Author Name",
    "email": "author@example.com",
    "url": "https://github.com/author"
  },
  "homepage": "https://docs.example.com",
  "repository": "https://github.com/author/plugin",
  "license": "MIT",
  "keywords": ["tag1", "tag2"],
  "commands": "./commands/",
  "agents": "./agents/",
  "hooks": "./hooks/hooks.json",
  "mcpServers": "./.mcp.json"
}
```

## コンポーネント参照

| フィールド | 型 | 説明 |
|-----------|---|------|
| `commands` | string/array | コマンドファイル/ディレクトリ |
| `agents` | string/array | エージェントファイル/ディレクトリ |
| `hooks` | string/object | フック設定パスまたはインライン |
| `mcpServers` | string/object | MCP設定パスまたはインライン |
