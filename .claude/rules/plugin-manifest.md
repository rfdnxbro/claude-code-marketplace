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
| `$schema` | string | JSONスキーマ参照URL（v2.1.120以降、`claude plugin validate` で受け入れ可能）。公式リファレンス（[plugins-reference](https://code.claude.com/docs/en/plugins-reference)）では `https://json.schemastore.org/claude-code-plugin-manifest.json` の指定が推奨されている。Claude Code 本体はロード時にこのフィールドを無視するため、純粋にエディタの補完・バリデーション用途。 |
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
| `monitors` | string/array | バックグラウンドモニター設定。セッション開始時またはこのプラグイン内のスキル起動時に自動で有効化（v2.1.105以降、→ [monitors.md](monitors.md)）。**v2.1.129以降は `experimental` ブロック配下に宣言を推奨**（トップレベル宣言も動作するが `claude plugin validate` が警告を出す） | `monitors/monitors.json` |
| `channels` | array | チャンネル（Telegram/Discord等のMCPイベント注入）宣言。`server`（必須、`mcpServers` のキーと一致）と per-channel `userConfig` を持つ（v2.1.80以降、→ [channels.md](channels.md)） | なし |
| `themes` | string/array | カスタムテーマ定義ファイル/ディレクトリ（v2.1.118以降）。**v2.1.129以降は `experimental` ブロック配下に宣言を推奨**（トップレベル宣言も動作するが `claude plugin validate` が警告を出す） | `themes/` |
| `userConfig` | object | プラグイン有効化時にユーザー入力を要求する設定項目。**インライン定義のみ**（外部ファイル参照は不可）（v2.1.83以降、→「ユーザー設定オプション」節） | なし |

**注意**: プラグイン同梱の `settings.json`（v2.1.49以降）はプラグインルート直下に配置すれば自動検出されます。`plugin.json` のコンポーネント参照フィールドとしては**公式に定義されていない**ため、上記の表には含まれません。詳細は本ドキュメント下部の「デフォルト設定ファイル（settings.json）」節を参照してください。

**デフォルトディレクトリの動作**:

- デフォルトディレクトリ（`commands/`, `agents/`, `skills/`等）が存在すれば自動的に読み込まれる
- plugin.jsonでの明示的な指定は不要
- カスタムパスを指定した場合、デフォルトディレクトリと**両方が読み込まれる**（置き換えではなく補足）
- **デフォルトパスと同じパスの明示指定は禁止**: 冗長な指定を避けるため、デフォルトパスと一致するコンポーネント参照は記述しないこと（例: `"hooks": "./hooks/hooks.json"` はデフォルトと同一のため不要）

**`bin/` ディレクトリ（v2.1.91以降）**:

プラグインルート直下に `bin/` ディレクトリを作成し、実行可能ファイルを配置することで、Bash ツールからフルパスなしのベアコマンドとして呼び出せます。

```text
my-plugin/
├── .claude-plugin/
│   └── plugin.json
├── bin/
│   ├── my-tool        # フルパス不要で実行可能
│   └── helper-script  # フルパス不要で実行可能
└── commands/
    └── use-tool.md
```

`bin/` ディレクトリは plugin.json での指定不要で自動的に PATH に追加されます。

## `experimental` ブロック（v2.1.129以降）

v2.1.129以降、`themes` と `monitors` は `"experimental"` ブロック配下に宣言することが推奨されます。トップレベル宣言も引き続き動作しますが、`claude plugin validate` が警告を出します。

```json
{
  "name": "my-plugin",
  "experimental": {
    "themes": "./themes/",
    "monitors": "./monitors/monitors.json"
  }
}
```

インライン配列形式でモニターを指定する場合:

```json
{
  "name": "my-plugin",
  "experimental": {
    "monitors": [
      { "name": "deploy-status", "command": "...", "description": "..." }
    ]
  }
}
```

## 完全な例

```json
{
  "$schema": "https://json.schemastore.org/claude-code-plugin-manifest.json",
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

上記の例では `commands/`, `agents/`, `skills/`, `hooks/hooks.json`, `.mcp.json` はデフォルトパスに配置されているため、明示的な指定は不要です。プラグインルート直下の `settings.json` も自動検出されます。

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

## 依存関係（dependencies）（v2.1.110以降）

プラグインが依存する他のプラグインを配列で宣言できます。`/plugin install` 実行時に依存プラグインが自動的にインストールされ、インストールされた依存関係が一覧表示されます。

```json
{
  "name": "my-plugin",
  "dependencies": ["base-plugin", "shared-tools"]
}
```

| フィールド | 型 | 説明 |
|-----------|---|------|
| `dependencies` | array | 依存プラグインのリスト（プラグイン名を配列で指定） |

**動作:**

- `dependencies` に記載したプラグインは、このプラグインのインストール時に自動でインストールされます
- マーケットプレイスエントリ側に `dependencies` が記載されていない場合でも、`plugin.json` の `dependencies` フィールドが有効になります
- プラグイン名は kebab-case で指定します

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

プラグインに `settings.json` を同梱することで、プラグイン有効時のデフォルト設定を提供できます。

### デフォルト位置

プラグインルート直下の `settings.json` が自動検出されます。`plugin.json` 側で独自パスを指定するフィールドは**公式スキーマに存在しません**。

### サポートされるキー

公式ドキュメント（plugins-reference の File locations reference 表）では以下のように明記されています:

> Default configuration applied when the plugin is enabled. Only the `agent` and `subagentStatusLine` keys are currently supported

つまり、プラグイン同梱 `settings.json` で**サポートされるのは `agent` と `subagentStatusLine` の2つのキーのみ**です。`env` や `permissions` などその他のキーは公式にサポートされていません。

| キー | 説明 | 詳細 |
|------|------|------|
| `subagentStatusLine` | サブエージェントのステータスライン設定 | 公式 [`/en/statusline#subagent-status-lines`](https://code.claude.com/docs/en/statusline#subagent-status-lines) を参照 |
| `agent` | エージェント関連のデフォルト設定 | [agents.md](agents.md) および公式 [`/en/sub-agents`](https://code.claude.com/docs/en/sub-agents) を参照 |

### settings.json のフォーマット例

```json
{
  "subagentStatusLine": {
    "type": "command",
    "command": "~/.claude/subagent-statusline.sh"
  }
}
```

### 注意事項

- 機密情報（APIキー等）は `settings.json` に含めないでください。機密値はユーザーごとに入力を求める「ユーザー設定オプション（userConfig）」を使用し、`sensitive: true` を指定してください
- `env` / `permissions` / `hooks` / `model` などのキーはプラグイン同梱 `settings.json` で**サポートされません**。これらを設定したい場合は、プラグイン利用者側の `.claude/settings.json`（プロジェクト設定またはユーザー設定）に記述する前提で設計してください

## ユーザー設定オプション（userConfig）（v2.1.83以降）

プラグインが有効化される際にユーザーへ設定値を入力してもらうための設定を定義できます。`sensitive: true` を指定した値は macOS キーチェーンまたは保護された認証情報ファイル（その他のプラットフォーム）に安全に保存されます。

```json
{
  "name": "my-plugin",
  "userConfig": {
    "apiKey": {
      "type": "string",
      "title": "API キー",
      "description": "サービスへのリクエストで使用する認証キー",
      "sensitive": true
    },
    "serverUrl": {
      "type": "string",
      "title": "サーバーURL",
      "description": "API リクエストの送信先となるベース URL",
      "default": "https://api.example.com"
    }
  }
}
```

### userConfig のフィールド仕様

`userConfig` はキーと設定オブジェクトのマッピングです。各設定オブジェクトには以下のフィールドを指定できます:

| フィールド | 型 | 必須 | 説明 |
|-----------|---|------|------|
| `type` | string | Yes | 設定項目の型。許可値: `string` / `number` / `boolean` / `directory` / `file` |
| `title` | string | Yes | 設定項目の表示名（UI に表示される短いラベル） |
| `description` | string | Yes | 設定項目の説明（ユーザーへの入力プロンプトに表示） |
| `sensitive` | boolean | No | `true` の場合、入力値を安全なストレージ（macOS: キーチェーン、その他: 保護された認証情報ファイル）に保存 |
| `default` | type に対応 | No | 未入力時のデフォルト値。`type` と一致する型で指定する（例: `type: "number"` なら数値リテラル、`type: "boolean"` なら真偽値リテラル） |

> **注意**: `userConfig` の詳細スキーマ（追加フィールドなど）は公式ドキュメントを参照してください。

## エンタープライズ管理設定との優先順位（v2.1.51以降）

v2.1.51以降、macOS plistまたはWindows Registryを通じてManaged Settings（管理設定）を使用できるようになりました。

### 公式の Settings precedence

公式 settings ドキュメントに記載されている優先順位は以下の通りです（高い順）:

1. Managed settings（macOS plist / Windows Registry）
2. Command line arguments
3. Local project settings（`.claude/settings.local.json`）
4. Shared project settings（`.claude/settings.json`）
5. User settings（`~/.claude/settings.json`）

**注意**: プラグイン同梱 `settings.json`（デフォルト設定）は、この優先順位リストに**明示的には列挙されていません**。公式 plugins-reference では「Default configuration applied when the plugin is enabled」と記されるのみです。実用上は「ユーザー/プロジェクト設定で上書きされるデフォルト」として扱うのが安全です。

エンタープライズ環境では、組織の管理者が managed settings を通じてプラグインの挙動を制限できます。プラグインの動作がエンタープライズポリシーによって制約される可能性を前提に設計してください。

### allowedChannelPlugins（v2.1.84以降）

チーム/エンタープライズ管理者がチャンネルプラグインの許可リストを定義するための managed setting です。詳細は [channels.md](channels.md) を参照してください。

チャンネル機能全体は v2.1.80 以降、permission relay は v2.1.81 以降、`allowedChannelPlugins` managed setting は v2.1.84 以降で利用できます。

以下は managed setting として設定する際の**キー構造の概念表現**です。実際は macOS plist または Windows Registry 形式で、以下のキー名・値構造に相当する形式で記述します（プラットフォーム固有の書式例は公式未掲載 — 後述の注意参照）。

```json
{
  "channelsEnabled": true,
  "allowedChannelPlugins": [
    { "marketplace": "claude-plugins-official", "plugin": "telegram" }
  ]
}
```

**動作:**

- `channelsEnabled: true` が前提（未設定または `false` の場合、`--channels` 指定に関わらずチャンネル配信はブロック）
- `allowedChannelPlugins` 未定義 = Anthropic デフォルト allowlist が適用
- `[]`（空配列）= 全チャンネルプラグインをブロック（ただし `--dangerously-load-development-channels` は bypass 可）
- 各エントリは `{ marketplace: string, plugin: string }` の形式

**注意**: macOS plist キー名・Windows Registry パスなどの**プラットフォーム固有の書式例は公式ドキュメントに明示されていません**。一般的な managed settings 機構（[`/en/settings#settings-files`](https://code.claude.com/docs/en/settings#settings-files)）に従って設定してください。

**ユースケース:**

- 組織承認済みプラグインのみを許可するセキュリティポリシーの適用
- 未検証のプラグインによるリスクの軽減
- エンタープライズ環境でのプラグイン管理の一元化
