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

| フィールド | 型 | 説明 | デフォルトディレクトリ |
|-----------|---|------|----------------------|
| `commands` | string/array | コマンドファイル/ディレクトリ | `commands/` |
| `agents` | string/array | エージェントファイル/ディレクトリ | `agents/` |
| `skills` | string/array | スキルディレクトリ | `skills/` |
| `hooks` | string/object | フック設定パスまたはインライン | `hooks/hooks.json` |
| `mcpServers` | string/object | MCP設定パスまたはインライン（→ [mcp-servers.md](mcp-servers.md)） | `.mcp.json` |
| `lspServers` | string/object | LSP設定パスまたはインライン（→ [lsp-servers.md](lsp-servers.md)） | `.lsp.json` |
| `outputStyles` | string/array | 出力スタイルファイル/ディレクトリ（→ [output-styles.md](output-styles.md)） | なし |
| `settings` | string | デフォルト設定ファイルへのパス（v2.1.49以降） | `settings.json` |

**デフォルトディレクトリの動作**:

- デフォルトディレクトリ（`commands/`, `agents/`, `skills/`等）が存在すれば自動的に読み込まれる
- plugin.jsonでの明示的な指定は不要
- カスタムパスを指定した場合、デフォルトディレクトリと**両方が読み込まれる**（置き換えではなく補足）
- **デフォルトパスと同じパスの明示指定は禁止**: 冗長な指定を避けるため、デフォルトパスと一致するコンポーネント参照は記述しないこと（例: `"hooks": "./hooks/hooks.json"` や `"settings": "./settings.json"` はデフォルトと同一のため不要）

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
  "keywords": ["keyword1", "keyword2"]
}
```

上記の例では `commands/`, `agents/`, `skills/`, `hooks/hooks.json`, `.mcp.json`, `settings.json` はデフォルトパスに配置されているため、明示的な指定は不要です。

**カスタムパスを使用する場合のみ指定**:

```json
{
  "name": "my-plugin",
  "hooks": "./custom-hooks/config.json",
  "mcpServers": "./config/mcp.json"
}
```

## パスの重要なルール

- すべてのパスはプラグインルートからの相対パス（`./`で開始）
- カスタムパスはデフォルトディレクトリを**置き換えない、補足する**
- 複数パスは配列で指定可能
- `commands/`, `agents/`, `skills/` は `.claude-plugin/` 内ではなく、プラグインルート直下に配置

## パーミッション設定（v2.1.27以降）

プラグインでは、ツールの実行権限を `allow` と `ask` フィールドで制御できます。これらはスキル、エージェント、スラッシュコマンドのfrontmatterで指定します。

### 優先順位

content-level（具体的なパターン指定）の `ask` は、tool-level（ツール全体）の `allow` より**優先されます**。

```yaml
---
name: my-command
allow: ["Bash"]
ask: ["Bash(rm *)", "Bash(dd *)"]
---
```

上記の設定では:

- `Bash` ツール全体は許可されています（`allow`）
- しかし `rm` や `dd` コマンドは確認プロンプトが表示されます（`ask` が優先）

### ユースケース

この仕組みにより、以下のような柔軟な権限制御が可能です:

```yaml
---
# 例1: ファイル編集は許可、削除のみ確認
allow: ["Edit", "Write"]
ask: ["Bash(rm *)"]

# 例2: Bashは基本許可、危険なコマンドのみ確認
allow: ["Bash"]
ask: ["Bash(rm *)", "Bash(dd *)", "Bash(sudo *)"]
---
```

### 注意事項

- content-levelパターンはツール名と引数パターンで指定（例: `Bash(rm *)`）
- パターンマッチングはワイルドカード（`*`）をサポート
- 複数のパターンを配列で指定可能
- この優先順位は v2.1.27 で導入されました

詳細は [hooks.md](hooks.md) の「パーミッション優先順位」セクションを参照してください。

## プラグインの即時利用可能化（v2.1.45以降）

v2.1.45以降、プラグインインストール後に**再起動なしで即座に利用可能**になります。

以前のバージョンではプラグインインストール後にClaude Codeの再起動が必要でしたが、現在は以下のコンポーネントがすぐに利用できます:

- スラッシュコマンド
- サブエージェント
- フック
- MCPサーバー
- LSPサーバー
- 出力スタイル

これにより、プラグイン開発のイテレーションが高速化され、ユーザー体験が向上します。

## `/reload-plugins` コマンド（v2.1.69以降）

v2.1.69以降、Claude Codeを再起動せずにプラグインの変更を即座に反映できる `/reload-plugins` コマンドが追加されました。

```text
/reload-plugins
```

プラグインのファイルを編集した後、このコマンドを実行することでセッションを継続しながら最新の変更を反映できます。

**ユースケース:**

- プラグイン開発中のイテレーション高速化
- スラッシュコマンド・エージェント・フックの変更をすぐに確認
- デバッグ時の素早い変更反映

## デフォルト設定ファイル（settings.json）（v2.1.49以降）

プラグインに `settings.json` を同梱することで、ユーザーにデフォルト設定を提供できます。

### plugin.json での設定

プラグインルート直下に `settings.json` を配置すれば自動的に読み込まれるため、通常は `plugin.json` での指定は不要です。

カスタムパスに配置する場合のみ指定:

```json
{
  "name": "my-plugin",
  "settings": "./config/settings.json"
}
```

### settings.json のフォーマット例

```json
{
  "env": {
    "MY_PLUGIN_API_URL": "https://api.example.com",
    "MY_PLUGIN_TIMEOUT": "30"
  },
  "permissions": {
    "allow": ["Bash(git:*)"],
    "ask": ["Bash(rm *)"]
  }
}
```

### ユースケース

- プラグインのデフォルト環境変数の設定
- デフォルトのパーミッション設定の提供
- ユーザーが上書き可能な初期設定の定義

### 注意事項

- ユーザーの設定はプラグインのデフォルト設定より優先されます
- 機密情報（APIキー等）はデフォルト設定に含めないでください
- パスはプラグインルートからの相対パス（`./`で開始）で指定してください

## ユーザー設定オプション（userConfig）（v2.1.83以降）

プラグインが有効化される際にユーザーへ設定値を入力してもらうための設定を定義できます。`sensitive: true` を指定した値は macOS キーチェーンまたは保護された認証情報ファイル（その他のプラットフォーム）に安全に保存されます。

```json
{
  "name": "my-plugin",
  "userConfig": {
    "apiKey": {
      "description": "API認証キー",
      "sensitive": true
    },
    "serverUrl": {
      "description": "サーバーのURL",
      "default": "https://api.example.com"
    }
  }
}
```

### userConfig のフィールド仕様

`userConfig` はキーと設定オブジェクトのマッピングです。各設定オブジェクトには以下のフィールドを指定できます:

| フィールド | 型 | 説明 |
|-----------|---|------|
| `description` | string | 設定項目の説明（ユーザーへの入力プロンプトに表示） |
| `sensitive` | boolean | `true` の場合、入力値を安全なストレージ（macOS: キーチェーン、その他: 保護された認証情報ファイル）に保存 |
| `default` | string | 未入力時のデフォルト値 |

> **注意**: `userConfig` の詳細スキーマ（必須フィールドなど）は公式ドキュメントを参照してください。<!-- TODO: 要確認 -->

### エンタープライズ管理設定との優先順位（v2.1.51以降）

v2.1.51以降、macOS plistまたはWindows Registryを通じてManaged Settings（管理設定）を設定できるようになりました。優先順位は以下の通りです（高い順）:

1. エンタープライズ管理設定（macOS plist / Windows Registry）
2. ユーザー設定（`~/.claude.json` 等）
3. プラグインの `settings.json`（デフォルト設定）

エンタープライズ環境では、組織の管理者がプラグインのデフォルト設定を上書きできます。プラグインの動作がエンタープライズポリシーによって制限される場合があることを念頭に置いて設計してください。
