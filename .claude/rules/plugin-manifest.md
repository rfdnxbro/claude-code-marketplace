---
paths: plugins/*/.claude-plugin/plugin.json, .claude-plugin/plugin.json
---

# プラグインマニフェスト（plugin.json）

`.claude-plugin/plugin.json` は個別プラグインの定義ファイルです。

マーケットプレイス全体の管理には `marketplace.json` を使用します。

## 必須フィールド

| フィールド | 型 | 説明 |
|-----------|---|------|
| `name` | string | プラグイン識別子（kebab-case、スペース禁止） |

## メタデータフィールド（オプション）

| フィールド | 型 | 説明 |
|-----------|---|------|
| `version` | string | セマンティックバージョン（例: `2.1.0`） |
| `description` | string | プラグインの説明 |
| `author` | object | `{name, email?, url?}` |
| `homepage` | string | ドキュメントURL |
| `repository` | string | ソースコードURL |
| `license` | string | SPDXライセンス識別子（`MIT`, `Apache-2.0`等） |
| `keywords` | array | 検索用タグ |

## コンポーネント参照

| フィールド | 型 | 説明 |
|-----------|---|------|
| `commands` | string/array | コマンドファイル/ディレクトリ |
| `agents` | string/array | エージェントファイル/ディレクトリ |
| `skills` | string/array | スキルディレクトリ |
| `hooks` | string/object | フック設定パスまたはインライン |
| `mcpServers` | string/object | MCP設定パスまたはインライン |
| `lspServers` | string/object | LSP設定パスまたはインライン |
| `outputStyles` | string/array | 出力スタイルファイル/ディレクトリ |

## 完全な例

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "プラグインの説明",
  "author": {
    "name": "Author Name",
    "email": "author@example.com"
  },
  "homepage": "https://docs.example.com",
  "repository": "https://github.com/author/plugin",
  "license": "MIT",
  "keywords": ["keyword1", "keyword2"],
  "commands": "./commands/",
  "agents": "./agents/",
  "skills": "./skills/",
  "hooks": "./hooks/hooks.json",
  "mcpServers": "./.mcp.json"
}
```

## パスの重要なルール

- すべてのパスはプラグインルートからの相対パス（`./`で開始）
- カスタムパスはデフォルトディレクトリを**置き換えない、補足する**
- 複数パスは配列で指定可能
- `commands/`, `agents/`, `skills/` は `.claude-plugin/` 内ではなく、プラグインルート直下に配置
