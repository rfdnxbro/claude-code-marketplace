---
paths: plugins/*/.lsp.json
---

# LSPサーバー

JSON形式で記述します。配置場所はプラグインルートの `.lsp.json`。

## 形式

```json
{
  "server-name": {
    "command": "language-server-binary",
    "args": ["serve"],
    "extensionToLanguage": {
      ".ext": "language-id"
    }
  }
}
```

## フィールド仕様

### 必須フィールド

| フィールド | 型 | 説明 |
|-----------|---|------|
| `command` | string | LSPサーバーの実行コマンド（PATHに存在する必要あり） |
| `extensionToLanguage` | object | ファイル拡張子から言語IDへのマッピング |

### オプションフィールド

| フィールド | 型 | 説明 |
|-----------|---|------|
| `args` | array | コマンドライン引数 |
| `transport` | string | 通信方式（`"stdio"` または `"socket"`、デフォルト: `"stdio"`） |
| `env` | object | 環境変数 |
| `initializationOptions` | object | サーバー初期化オプション |
| `settings` | object | ワークスペース設定 |
| `workspaceFolder` | string | ワークスペースフォルダパス |
| `startupTimeout` | number | サーバー起動タイムアウト（ミリ秒） |
| `shutdownTimeout` | number | シャットダウン待機時間（ミリ秒） |
| `restartOnCrash` | boolean | クラッシュ時の自動再起動 |
| `maxRestarts` | number | 最大再起動回数 |

## サンプル

### Go（gopls）

```json
{
  "go": {
    "command": "gopls",
    "args": ["serve"],
    "extensionToLanguage": {
      ".go": "go"
    }
  }
}
```

### Python（Pyright）

```json
{
  "python": {
    "command": "pyright-langserver",
    "args": ["--stdio"],
    "extensionToLanguage": {
      ".py": "python",
      ".pyi": "python"
    }
  }
}
```

### TypeScript

```json
{
  "typescript": {
    "command": "typescript-language-server",
    "args": ["--stdio"],
    "extensionToLanguage": {
      ".ts": "typescript",
      ".tsx": "typescriptreact",
      ".js": "javascript",
      ".jsx": "javascriptreact"
    }
  }
}
```

### 詳細設定例

```json
{
  "rust": {
    "command": "rust-analyzer",
    "transport": "stdio",
    "extensionToLanguage": {
      ".rs": "rust"
    },
    "initializationOptions": {
      "checkOnSave": {
        "command": "clippy"
      }
    },
    "settings": {
      "rust-analyzer": {
        "cargo": {
          "allFeatures": true
        }
      }
    },
    "startupTimeout": 30000,
    "restartOnCrash": true,
    "maxRestarts": 3
  }
}
```

## 環境変数

- `${VAR}` - 環境変数を展開
- `${VAR:-default}` - デフォルト値付き
- `${CLAUDE_PLUGIN_ROOT}` - プラグインルートへの絶対パス

```json
{
  "custom-server": {
    "command": "${CLAUDE_PLUGIN_ROOT}/bin/my-lsp",
    "env": {
      "CONFIG_PATH": "${CLAUDE_PLUGIN_ROOT}/config.json"
    },
    "extensionToLanguage": {
      ".custom": "custom-lang"
    }
  }
}
```

## 言語ID

言語IDはLSP仕様に準拠します。一般的な例:

| 言語 | 言語ID |
|-----|--------|
| Go | `go` |
| Python | `python` |
| TypeScript | `typescript` |
| JavaScript | `javascript` |
| Rust | `rust` |
| Java | `java` |
| C/C++ | `c` / `cpp` |

完全な一覧は [LSP仕様](https://microsoft.github.io/language-server-protocol/specifications/specification-current/#textDocumentItem) を参照してください。

## セキュリティ注意事項

- LSPサーバーバイナリはプラグインに含まれない。ユーザーが別途インストールする必要がある
- 機密情報（APIキー等）は環境変数経由で渡し、直接記述しない
- `command` にはPATH内の実行可能ファイル、または `${CLAUDE_PLUGIN_ROOT}` を使った絶対パスを指定

良い例:

```json
"env": { "API_KEY": "${API_KEY}" }
```

悪い例（機密情報を直接記述）:

```json
"env": { "API_KEY": "secret-key-xxx" }
```

## トラブルシューティング

### サーバーが起動しない

1. **コマンドの確認**: `command`がPATHに存在するか確認

   ```bash
   which gopls  # コマンドのパスを確認
   ```

2. **手動実行テスト**: ターミナルでサーバーを直接起動

   ```bash
   gopls serve  # サーバーが正常に起動するか確認
   ```

### 診断情報が表示されない

- `extensionToLanguage`のマッピングが正しいか確認
- 言語IDがLSP仕様に準拠しているか確認

### タイムアウトエラー

- `startupTimeout`を増やす（デフォルトは通常十分）
- ネットワーク遅延がある場合は値を調整

### 頻繁な再起動

- `maxRestarts`の値を確認
- サーバーがクラッシュする原因を調査（ログを確認）
