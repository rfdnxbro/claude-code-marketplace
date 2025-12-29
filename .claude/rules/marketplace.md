---
paths: .claude-plugin/marketplace.json
---

# マーケットプレイス設定（marketplace.json）

`.claude-plugin/marketplace.json` はマーケットプレイス全体の設定ファイルです。

個別プラグインの定義には `plugin.json` を使用します。

## 必須フィールド

| フィールド | 型 | 説明 |
|-----------|---|------|
| `name` | string | マーケットプレイス識別子（kebab-case） |
| `owner` | object | 管理者情報（`name`必須） |
| `plugins` | array | プラグイン定義リスト |

## 形式

```json
{
  "name": "my-marketplace",
  "owner": {
    "name": "Team Name",
    "email": "team@example.com"
  },
  "metadata": {
    "description": "マーケットプレイスの説明",
    "version": "1.0.0",
    "pluginRoot": "./plugins"
  },
  "plugins": [
    {
      "name": "plugin-name",
      "source": "./plugins/plugin-name",
      "description": "プラグインの説明",
      "version": "1.0.0"
    }
  ]
}
```

## プラグインエントリ

### 必須フィールド

| フィールド | 型 | 説明 |
|-----------|---|------|
| `name` | string | プラグイン識別子（kebab-case） |
| `source` | string/object | プラグイン取得元 |

### オプションフィールド

| フィールド | 型 | 説明 |
|-----------|---|------|
| `description` | string | プラグイン説明 |
| `version` | string | バージョン |
| `author` | object | 作成者情報 |
| `homepage` | string | ドキュメントURL |
| `repository` | string | ソースコードURL |
| `license` | string | SPDXライセンス識別子 |
| `keywords` | array | 検索用タグ |
| `category` | string | カテゴリ |
| `strict` | boolean | `plugin.json`必須（デフォルト: true） |

## ソース指定

### 相対パス

```json
{
  "name": "local-plugin",
  "source": "./plugins/my-plugin"
}
```

### GitHub

```json
{
  "name": "github-plugin",
  "source": {
    "source": "github",
    "repo": "owner/plugin-repo"
  }
}
```

### Git URL

```json
{
  "name": "git-plugin",
  "source": {
    "source": "url",
    "url": "https://gitlab.com/team/plugin.git"
  }
}
```

## 予約済み名前（使用不可）

- `claude-code-marketplace`
- `claude-code-plugins`
- `claude-plugins-official`
- `anthropic-marketplace`
- `anthropic-plugins`
- `agent-skills`
- `life-sciences`

## 検証

```bash
claude plugin validate .
```
