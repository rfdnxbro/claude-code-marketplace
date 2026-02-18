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

**デフォルトディレクトリの動作**:

- デフォルトディレクトリ（`commands/`, `agents/`, `skills/`等）が存在すれば自動的に読み込まれる
- plugin.jsonでの明示的な指定は不要
- カスタムパスを指定した場合、デフォルトディレクトリと**両方が読み込まれる**（置き換えではなく補足）

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
