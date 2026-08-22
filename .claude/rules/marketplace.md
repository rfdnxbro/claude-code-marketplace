---
paths: .claude-plugin/marketplace.json
---

# マーケットプレイス設定（marketplace.json）

`.claude-plugin/marketplace.json` はマーケットプレイス全体の設定ファイルです。

個別プラグインの定義には `plugin.json` を使用します。

## `.claude/skills` への自動ロード

`.claude/skills` ディレクトリに配置されたプラグインはマーケットプレイスの設定なしに自動的にロードされます。

```text
.claude/
└── skills/
    └── my-plugin/        # プラグインを配置
        ├── .claude-plugin/
        │   └── plugin.json
        └── commands/
            └── my-command.md
```

**配置方法:**

- プロジェクトの `.claude/skills/<plugin-name>/` にプラグインを配置するだけで自動ロード
- `claude plugin init <name>` コマンドで `.claude/skills` 内に雛形を生成可能（→ [plugin-manifest.md](plugin-manifest.md) の「プラグインの初期化」節を参照）
- マーケットプレイスへの登録・設定が不要なため、個人利用やプロジェクト内専用プラグインに適している

## 必須フィールド

| フィールド | 型 | 説明 |
|-----------|---|------|
| `name` | string | マーケットプレイス識別子（kebab-case） |
| `owner` | object | 管理者情報（`name`必須） |
| `plugins` | array | プラグイン定義リスト |

## トップレベルのオプションフィールド

以下のフィールドが `marketplace.json` のトップレベルで有効です:

| フィールド | 型 | 説明 |
|-----------|---|------|
| `$schema` | string | JSONスキーマ参照URL（任意。Anthropic公式の `marketplace.json` JSON Schemaは現時点で公開されていないため、利用するエディタ等で独自に提供されているスキーマURLを指定する用途を想定） |
| `version` | string | マーケットプレイスのバージョン |
| `description` | string | マーケットプレイスの説明 |
| `renames` | object | プラグイン名変更マッピング（旧名 → 新名）。自動適用される |

## プラグイン自動リネーム

`renames` フィールドを使用すると、プラグイン名を変更した際にユーザーの設定を自動的に更新できます。マーケットプレイスの `renames` マップが自動的に適用され、古いプラグイン名を使用しているユーザーの設定が新しい名前に更新されます。

```json
{
  "name": "my-marketplace",
  "owner": { "name": "Team Name" },
  "renames": {
    "old-plugin-name": "new-plugin-name",
    "another-old-name": "another-new-name"
  },
  "plugins": [
    {
      "name": "new-plugin-name",
      "source": "./plugins/new-plugin-name"
    }
  ]
}
```

| フィールド | 型 | 説明 |
|-----------|---|------|
| キー | string | 旧プラグイン名（kebab-case） |
| 値 | string | 新プラグイン名（kebab-case） |

## 形式

```json
{
  "$schema": "https://example.com/marketplace-schema.json",
  "version": "1.0.0",
  "description": "マーケットプレイスの説明",
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
| `defaultEnabled` | boolean | `false` を指定するとマーケットプレイスからインストール時にデフォルト無効になる。`/plugin` または `claude plugin enable` で有効化できる。有効化済みプラグインの依存として指定された場合は自動的に有効化される |

## ソース指定

### `metadata.pluginRoot`による裸のソース名解決

`metadata.pluginRoot` を設定すると、`./`や`../`で始まらない裸のプラグインソース名（例: `"source": "my-plugin"`）が、そのディレクトリ配下で解決されます。

```json
{
  "metadata": {
    "pluginRoot": "./plugins"
  },
  "plugins": [
    {
      "name": "my-plugin",
      "source": "my-plugin"
    }
  ]
}
```

上記の例では `source: "my-plugin"` は `./plugins/my-plugin` として解決されます。`./plugins/my-plugin` のような相対パス指定や、GitHub/Git URL/npm等のオブジェクト形式のsourceには影響しません。

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

| フィールド | 型 | 必須 | 説明 |
|-----------|---|:---:|------|
| `source` | string | ✓ | `"github"` を指定 |
| `repo` | string | ✓ | `"owner/repo"` 形式（fragment構文でbranch/tag/commit指定可） |
| `skipLfs` | boolean | | `true` に設定すると Git LFS のダウンロードをスキップ |

#### branch/tag/commit SHA指定

GitHub sourceでは、fragment構文を使ってbranch、tag、またはcommit SHAを指定できます。

```json
{
  "name": "github-plugin-branch",
  "source": {
    "source": "github",
    "repo": "owner/plugin-repo#develop"
  }
}
```

```json
{
  "name": "github-plugin-tag",
  "source": {
    "source": "github",
    "repo": "owner/plugin-repo#v1.2.3"
  }
}
```

```json
{
  "name": "github-plugin-commit",
  "source": {
    "source": "github",
    "repo": "owner/plugin-repo#abc123def456789"
  }
}
```

> **注意**: branch/tagを指定したプラグイン（ref-tracked plugins）は、**毎回ロード時に再クローン**されて最新版に更新されます。特定のバージョンに固定したい場合はcommit SHAを指定してください。
>
> - 安定性重視 → commit SHA指定（例: `owner/plugin-repo#abc123def456789`）
> - 常に最新を使用 → branch/tag指定（例: `owner/plugin-repo#main`）

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

**`.git` サフィックスは省略可能**: Azure DevOps や AWS CodeCommit など、`.git` サフィックスなしの URL も正式サポートされています。

```json
{
  "name": "azure-devops-plugin",
  "source": {
    "source": "url",
    "url": "https://dev.azure.com/myorg/myproject/_git/my-plugin"
  }
}
```

```json
{
  "name": "codecommit-plugin",
  "source": {
    "source": "url",
    "url": "https://git-codecommit.ap-northeast-1.amazonaws.com/v1/repos/my-plugin"
  }
}
```

| フィールド | 型 | 必須 | 説明 |
|-----------|---|:---:|------|
| `source` | string | ✓ | `"url"` を指定 |
| `url` | string | ✓ | gitリポジトリのURL（fragment構文でbranch/tag/commit指定可） |
| `skipLfs` | boolean | | `true` に設定すると Git LFS のダウンロードをスキップ |
| `headersHelper` | string | | HTTPヘッダーを動的生成するコマンド。詳細は[headersHelper（カタログエントリ）](#headershelperカタログエントリ)を参照 |

#### branch/tag/commit SHA指定

Git URL sourceでも、URL末尾にfragment構文を使ってbranch、tag、またはcommit SHAを指定できます。`.git` サフィックスの有無にかかわらず、fragment構文を使用できます。

```json
{
  "name": "git-plugin-branch",
  "source": {
    "source": "url",
    "url": "https://gitlab.com/team/plugin.git#develop"
  }
}
```

```json
{
  "name": "git-plugin-tag",
  "source": {
    "source": "url",
    "url": "https://gitlab.com/team/plugin.git#v1.2.3"
  }
}
```

```json
{
  "name": "git-plugin-commit",
  "source": {
    "source": "url",
    "url": "https://gitlab.com/team/plugin.git#abc123def456789"
  }
}
```

> **注意**: branch/tagを指定したプラグイン（ref-tracked plugins）は、**毎回ロード時に再クローン**されて最新版に更新されます。特定のバージョンに固定したい場合はcommit SHAを指定してください。
>
> - 安定性重視 → commit SHA指定（例: `https://gitlab.com/team/plugin.git#abc123def456789`）
> - 常に最新を使用 → branch/tag指定（例: `https://gitlab.com/team/plugin.git#main`）

#### headersHelper（カタログエントリ）

`url` ソースのプラグインエントリ（カタログエントリ）には `headersHelper` を設定できます。そのプラグインをインストール・更新する際にコマンドを実行し、生成したHTTPヘッダー（短命トークンなど）をカタログ取得・同一オリジンのアーカイブ取得に使用します。

```json
{
  "name": "private-plugin",
  "source": {
    "source": "url",
    "url": "https://plugins.example.com/private-plugin.git",
    "headersHelper": "./scripts/get-auth-headers.sh"
  }
}
```

- `headersHelper` はそのプラグインをインストール／更新する時にのみ実行される
- 実行前にコマンド内容が表示され、`claude plugin install`/`update` で `[y/N]` の確認を要求（`-y` で省略可）
- ヘルパースクリプトはJSON形式でヘッダーを出力する。書式は `.mcp.json` の `headersHelper` と同様（[mcp-servers.md](mcp-servers.md#headershelper)を参照）

TODO: 要確認 — 以下は現時点で未確認。

- `github` ソース（`source: "github"`）のカタログエントリでも `headersHelper` が利用できるか
- `headersHelper` の配置。CHANGELOGは「url マーケットプレイスまたはカタログエントリの `headersHelper`」とのみ述べており、`source` オブジェクトの中か、`source` と同階層かを特定できていない。ここでは `source` の中として記載している

### npm

npmレジストリからプラグインをインストール:

```json
{
  "name": "npm-plugin",
  "source": {
    "source": "npm",
    "package": "my-claude-plugin"
  }
}
```

#### 特定バージョンのピン留め

```json
{
  "name": "npm-plugin-pinned",
  "source": {
    "source": "npm",
    "package": "my-claude-plugin",
    "version": "1.2.3"
  }
}
```

#### カスタムnpmレジストリの指定

プライベートレジストリや社内レジストリを使用する場合:

```json
{
  "name": "private-npm-plugin",
  "source": {
    "source": "npm",
    "package": "@company/my-claude-plugin",
    "registry": "https://registry.company.internal"
  }
}
```

| フィールド | 型 | 必須 | 説明 |
|-----------|---|:---:|------|
| `source` | string | ✓ | `"npm"` を指定 |
| `package` | string | ✓ | npmパッケージ名（スコープ付きも可: `@scope/package`） |
| `version` | string | | バージョン指定（省略時は最新版） |
| `registry` | string | | カスタムレジストリURL（省略時はデフォルトのnpmレジストリ） |

### settings

`settings.json` 内にインラインでプラグインエントリを宣言できるソース種別です。マーケットプレイスファイルを別途用意せずに、Claude Code の設定ファイルに直接プラグインを埋め込む場合に使用します:

```json
{
  "name": "settings-plugin",
  "source": {
    "source": "settings"
  }
}
```

### git-subdir

gitリポジトリ内の特定サブディレクトリをプラグインソースとして指定:

```json
{
  "name": "subdir-plugin",
  "source": {
    "source": "git-subdir",
    "url": "https://github.com/owner/monorepo.git",
    "path": "packages/my-plugin"
  }
}
```

#### branch/tag/commit SHA指定

`git-subdir` でも、URL末尾にfragment構文を使ってbranch、tag、またはcommit SHAを指定できます:

```json
{
  "name": "subdir-plugin-branch",
  "source": {
    "source": "git-subdir",
    "url": "https://github.com/owner/monorepo.git#develop",
    "path": "packages/my-plugin"
  }
}
```

> **注意**: branch/tagを指定したプラグイン（ref-tracked plugins）は、**毎回ロード時に再クローン**されて最新版に更新されます。特定のバージョンに固定したい場合はcommit SHAを指定してください。
>
> - 安定性重視 → commit SHA指定（例: `https://github.com/owner/monorepo.git#abc123def456789`）
> - 常に最新を使用 → branch/tag指定（例: `https://github.com/owner/monorepo.git#main`）

| フィールド | 型 | 必須 | 説明 |
|-----------|---|:---:|------|
| `source` | string | ✓ | `"git-subdir"` を指定 |
| `url` | string | ✓ | gitリポジトリのURL（fragment構文でbranch/tag/commit指定可） |
| `path` | string | ✓ | リポジトリ内のサブディレクトリパス |

### archive

zipアーカイブをHTTPS経由でダウンロードしてインストールするソース種別です。ユーザー側にgit/npmが不要です:

```json
{
  "name": "my-plugin",
  "source": {
    "source": "archive",
    "url": "https://artifacts.example.com/claude-plugins/my-plugin-2.1.0.zip"
  }
}
```

zipは配下に`.claude-plugin/`を直接含む構成、または単一のトップレベルフォルダの中に`.claude-plugin/`を含む構成のどちらでもインストール可能です。それより深い階層にネストされたプラグインはインストールできません。アーカイブサイズの上限は256MiBです。

> この節の制約（zipの構成・サイズ上限・URLの制約・`sha256`の形式）は公式ドキュメント [plugin-marketplaces](https://code.claude.com/docs/en/plugin-marketplaces) の Zip archives 節に基づきます。CHANGELOG本文だけでは裏付けられないため、出典を明記します。

#### SHA-256ピン留め

`sha256`フィールドでアーカイブのダイジェストを指定すると、ダウンロード時に検証され、不一致の場合はインストールが拒否されます:

```json
{
  "name": "my-plugin",
  "source": {
    "source": "archive",
    "url": "https://artifacts.example.com/claude-plugins/my-plugin-2.1.0.zip",
    "sha256": "65b29a9fd3ff6a671e185d4deaeb5c42afb57ec1dd86f334b92f2e374f4344b5"
  }
}
```

| フィールド | 型 | 必須 | 説明 |
|-----------|---|:---:|------|
| `source` | string | ✓ | `"archive"` を指定 |
| `url` | string | ✓ | zipアーカイブのHTTPS URL。`http://`は非対応。loopback/link-local/クラウドメタデータホストへのURLは拒否される。リダイレクトも同じ条件を満たす必要がある |
| `sha256` | string | | アーカイブのSHA-256ダイジェスト（16進数64文字、大文字小文字問わず） |

## 予約済み名前（使用不可）

- `claude-code-marketplace`
- `claude-code-plugins`
- `claude-plugins-official`
- `anthropic-marketplace`
- `anthropic-plugins`
- `agent-skills`
- `life-sciences`

## シードディレクトリの複数指定

`CLAUDE_CODE_PLUGIN_SEED_DIR` 環境変数を使用してプラグインのシードディレクトリを指定できます。複数のディレクトリをプラットフォームのパス区切り文字で区切って指定できます。

| プラットフォーム | パス区切り文字 | 例 |
|----------------|:---:|---|
| Unix / macOS | `:` | `/path/to/dir1:/path/to/dir2` |
| Windows | `;` | `C:\path\dir1;C:\path\dir2` |

```bash
# Unix/macOSの場合: 複数のシードディレクトリを指定
export CLAUDE_CODE_PLUGIN_SEED_DIR="/opt/company/plugins:/home/user/my-plugins"

# Windowsの場合
# set CLAUDE_CODE_PLUGIN_SEED_DIR=C:\company\plugins;C:\Users\user\my-plugins
```

複数のプラグインソースを管理する場合はこの機能を活用してください。

## HTTPS経由でのプラグイン取得

`CLAUDE_CODE_PLUGIN_PREFER_HTTPS` 環境変数を設定すると、GitHubプラグインソースをSSHの代わりにHTTPSでクローン・更新します（`claude plugin add` および `claude plugin update` 操作を含む）。

```bash
export CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1
```

SSH鍵が設定されていないCI環境や企業ネットワーク環境など、SSHでのGitHub接続が難しい場合に有用です。`claude plugin add` および `claude plugin update` 操作にも適用されます。

## オフライン環境でのマーケットプレイス

`CLAUDE_CODE_PLUGIN_KEEP_MARKETPLACE_ON_FAILURE` 環境変数を設定すると、`git pull` が失敗した場合でも既存のマーケットプレイスキャッシュを保持します。

```bash
export CLAUDE_CODE_PLUGIN_KEEP_MARKETPLACE_ON_FAILURE=1
```

ネットワーク接続が不安定な環境や、オフラインでの使用時に有用です。未設定の場合、`git pull` 失敗時はマーケットプレイスが利用できなくなります。

## Gitタイムアウト設定

プラグインのGitクローン時のデフォルトタイムアウトは **120秒** です。

### カスタムタイムアウトの設定

`CLAUDE_CODE_PLUGIN_GIT_TIMEOUT_MS` 環境変数を設定することで、タイムアウトをミリ秒単位でカスタマイズできます:

```bash
# タイムアウトを300秒（5分）に設定
export CLAUDE_CODE_PLUGIN_GIT_TIMEOUT_MS=300000
```

大規模なプラグインリポジトリや低速なネットワーク環境で使用する場合は、この値を増やすことを推奨します。

## `--add-dir`での設定読み込み

`--add-dir`で追加したディレクトリから以下の設定が読み込まれます:

- `enabledPlugins`: 有効化するプラグインのリスト
- `extraKnownMarketplaces`: 追加のマーケットプレイス定義

これにより、プロジェクト固有の設定を`--add-dir`ディレクトリ内で管理できます。設定はプロジェクトルートの`.claude.json`と同様の形式で記述できます。
`extraKnownMarketplaces`が他のtierと同名エントリを定義している場合のマージ挙動は次節を参照。

## extraKnownMarketplacesの複数tier間マージ挙動

`extraKnownMarketplaces`はmanaged settings（enterprise）・ユーザー設定・プロジェクト設定・`--add-dir`など複数のsettingsで定義できます（tierの優先順位は[plugin-manifest.md](plugin-manifest.md)の「エンタープライズ管理設定との優先順位」を参照）。

同名のマーケットプレイスエントリが複数tierで定義されている場合、最も優先度の高いtierのエントリが**フィールド単位ではなくエントリ全体単位で**下位tierのエントリを上書きします。

エントリには、マーケットプレイスソースの取得時に送信するカスタムリクエストヘッダー（認証トークン等）を指定する`headers`フィールドを含められます:

```json
{
  "extraKnownMarketplaces": {
    "my-marketplace": {
      "source": { "source": "github", "repo": "org/repo" },
      "headers": {
        "Authorization": "Bearer ${TOKEN}"
      }
    }
  }
}
```

上位tierで同名エントリを再定義すると、下位tierで設定した`headers`は引き継がれず、上位tierのエントリで指定したフィールドのみが有効になります。カスタム`headers`を維持したい場合は、上位tierのエントリ内で`headers`を含めて完全な形でエントリを再定義する必要があります。

## urlマーケットプレイスのheadersHelper

`extraKnownMarketplaces` や `claude plugin marketplace add` でマーケットプレイス自体を `url` ソースとして登録する場合も、`headersHelper` を設定してカタログ（`marketplace.json`本体）取得時のHTTPヘッダーを動的生成できます。

```json
{
  "extraKnownMarketplaces": {
    "internal-catalog": {
      "source": {
        "source": "url",
        "url": "https://plugins.example.com/marketplace.json",
        "headersHelper": "/path/to/mint-headers.sh"
      }
    }
  }
}
```

- 生成されたヘッダーは、カタログ（`marketplace.json`本体）の取得と、同一オリジン（スキーム・ホスト・ポートが一致）のアーカイブ取得に使用される
- ヘルパースクリプトはJSON形式でヘッダーを出力する。書式は `.mcp.json` の `headersHelper` と同様（[mcp-servers.md](mcp-servers.md#headershelper)を参照）

TODO: 要確認 — 以下は現時点で未確認。

- 異なるオリジンへのアーカイブ取得や、オリジンを離れるリダイレクトでヘッダーが送信されるか。CHANGELOGは「カタログおよび同一オリジンのアーカイブ取得に使用される」とのみ述べており、それ以外の場合の挙動には触れていない。送信されないことを前提に設計しないこと
- カタログエントリ（`claude plugin install`/`update`）と同様に、`claude plugin marketplace add` 実行時にもコマンド内容の表示・`[y/N]` 確認が行われるか
- `headersHelper` の配置。上記の例では `source` オブジェクトの中として記載しているが、`source` と同階層の可能性もある（[headersHelper（カタログエントリ）](#headershelperカタログエントリ)の同じ注記を参照）

## strictKnownMarketplacesのpathPattern

エンタープライズ管理設定の `strictKnownMarketplaces` の `pathPattern` フィールドにより、ファイル/ディレクトリマーケットプレイスソースの正規表現マッチングが可能です。

`hostPattern` による制限に加えて、ローカルパスのパターンマッチングでマーケットプレイスソースを制限できます:

```json
{
  "strictKnownMarketplaces": [
    {
      "hostPattern": "github.com",
      "pathPattern": "^/myorg/.*-plugins$"
    },
    {
      "pathPattern": "^/opt/company/plugins/.*"
    }
  ]
}
```

| フィールド | 型 | 説明 |
|-----------|---|------|
| `hostPattern` | string | ホスト名のパターン（gitソースに使用） |
| `pathPattern` | string | ファイル/ディレクトリパスの正規表現パターン |

## strictKnownMarketplaces / blockedMarketplacesのownerワイルドカード

エンタープライズ管理設定の `strictKnownMarketplaces`（許可リスト）および `blockedMarketplaces`（プラグインマーケットプレイスソースをブロックするブロックリスト。`strictKnownMarketplaces`と対になる設定）では、GitHub sourceのエントリで `"owner/*"` のようなownerワイルドカードを指定できます。これにより、特定のGitHub org配下の全マーケットプレイスリポジトリを一括で許可・ブロックできます。

`strictKnownMarketplaces` でorg配下のリポジトリのみを許可する例:

```json
{
  "strictKnownMarketplaces": [
    {
      "source": "github",
      "repo": "acme-corp/*"
    }
  ]
}
```

`blockedMarketplaces` でorg配下のリポジトリを一括ブロックする例:

```json
{
  "blockedMarketplaces": [
    {
      "source": "github",
      "repo": "untrusted-org/*"
    }
  ]
}
```

| フィールド | 型 | 説明 |
|-----------|---|------|
| `source` | string | `"github"` を指定するとGitHub repoベースのマッチングになる |
| `repo` | string | `"owner/repo"`（単一リポジトリ）または `"owner/*"`（owner配下の全リポジトリを対象とするownerワイルドカード）形式 |

単一リポジトリを指定する既存のエントリはそのまま併用できます:

```json
{
  "strictKnownMarketplaces": [
    {
      "source": "github",
      "repo": "acme-corp/approved-plugins"
    }
  ]
}
```

TODO: 要確認 — ownerワイルドカードのマッチング挙動（大文字小文字を区別するか、ネストしたパスにマッチするかなど）は未調査。

## pluginTrustMessageマネージド設定

エンタープライズ管理設定の `pluginTrustMessage` フィールドにより、プラグインインストール前に表示される信頼警告に組織固有のコンテキストを追記できます。

macOS plistまたはWindows Registryで設定します:

```json
{
  "pluginTrustMessage": "このプラグインは組織のセキュリティチームによって審査されています。詳細はhttps://internal.example.com/plugins を参照してください。"
}
```

このメッセージはプラグインのデフォルト信頼警告に追記されて表示されます。組織固有のポリシー案内やサポート連絡先の追加に活用できます。

## `--plugin-dir` での `.zip` アーカイブ指定

`--plugin-dir` はディレクトリだけでなく `.zip` アーカイブも受け入れます。

```bash
# ディレクトリを指定
claude --plugin-dir ./my-plugin

# .zip アーカイブを指定
claude --plugin-dir ./my-plugin.zip
```

## `--plugin-dir` のローカル開発優先

`--plugin-dir` で指定したローカル開発コピーは、同名のインストール済みマーケットプレイスプラグインより優先されます。

```bash
# ローカル開発コピーでプラグインを起動（インストール済みの同名プラグインより優先）
claude --plugin-dir ./my-plugin
```

**優先順位（高い順）:**

1. `--plugin-dir` で指定したローカル開発コピー
2. インストール済みマーケットプレイスプラグイン（同名の場合）

**例外**: 管理設定（managed settings）によって `force-enabled` に設定されているプラグインは、`--plugin-dir` のローカルコピーより優先されます。

これにより、プラグイン開発中にインストール済みの同名プラグインを一時的にアンインストールすることなく、ローカルの変更をテストできます。

## 検証

```bash
claude plugin validate .
```
