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

**`.git` サフィックスは省略可能（v2.1.72以降）**: Azure DevOps や AWS CodeCommit など、`.git` サフィックスなしの URL も正式サポートされています。

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

### npm（v2.1.51以降）

npmレジストリからプラグインをインストール（v2.1.51以降）:

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

### git-subdir（v2.1.64以降）

gitリポジトリ内の特定サブディレクトリをプラグインソースとして指定（v2.1.64以降）:

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

| フィールド | 型 | 必須 | 説明 |
|-----------|---|:---:|------|
| `source` | string | ✓ | `"git-subdir"` を指定 |
| `url` | string | ✓ | gitリポジトリのURL（fragment構文でbranch/tag/commit指定可） |
| `path` | string | ✓ | リポジトリ内のサブディレクトリパス |

> **バグ修正（v2.1.77）**: 同じモノレポの異なるサブディレクトリにある `git-subdir` プラグインが、プラグインキャッシュで衝突する問題が修正されました。v2.1.77以降では、`url` が同一でも `path` が異なる場合は別々のキャッシュエントリとして扱われます。

## 予約済み名前（使用不可）

- `claude-code-marketplace`
- `claude-code-plugins`
- `claude-plugins-official`
- `anthropic-marketplace`
- `anthropic-plugins`
- `agent-skills`
- `life-sciences`

## Gitタイムアウト設定（v2.1.51以降）

プラグインのGitクローン時のタイムアウトが変更されました。

| バージョン | デフォルトタイムアウト |
|-----------|-----------------|
| v2.1.50以前 | 30秒 |
| v2.1.51以降 | **120秒** |

### カスタムタイムアウトの設定

`CLAUDE_CODE_PLUGIN_GIT_TIMEOUT_MS` 環境変数を設定することで、タイムアウトをミリ秒単位でカスタマイズできます:

```bash
# タイムアウトを300秒（5分）に設定
export CLAUDE_CODE_PLUGIN_GIT_TIMEOUT_MS=300000
```

大規模なプラグインリポジトリや低速なネットワーク環境で使用する場合は、この値を増やすことを推奨します。

## `--add-dir`での設定読み込み（v2.1.45以降）

v2.1.45以降、`--add-dir`で追加したディレクトリから以下の設定が読み込まれるようになりました:

- `enabledPlugins`: 有効化するプラグインのリスト
- `extraKnownMarketplaces`: 追加のマーケットプレイス定義

これにより、プロジェクト固有の設定を`--add-dir`ディレクトリ内で管理できます。設定はプロジェクトルートの`.claude.json`と同様の形式で記述できます。

## strictKnownMarketplacesのpathPattern（v2.1.64以降）

エンタープライズ管理設定の `strictKnownMarketplaces` に `pathPattern` フィールドが追加され、ファイル/ディレクトリマーケットプレイスソースの正規表現マッチングが可能になりました（v2.1.64以降）。

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
| `pathPattern` | string | ファイル/ディレクトリパスの正規表現パターン（v2.1.64以降） |

## pluginTrustMessageマネージド設定（v2.1.64以降）

エンタープライズ管理設定に `pluginTrustMessage` フィールドが追加され、プラグインインストール前に表示される信頼警告に組織固有のコンテキストを追記できます（v2.1.64以降）。

macOS plistまたはWindows Registryで設定します:

```json
{
  "pluginTrustMessage": "このプラグインは組織のセキュリティチームによって審査されています。詳細はhttps://internal.example.com/plugins を参照してください。"
}
```

このメッセージはプラグインのデフォルト信頼警告に追記されて表示されます。組織固有のポリシー案内やサポート連絡先の追加に活用できます。

## `--plugin-dir` のローカル開発優先（v2.1.74以降）

v2.1.74以降、`--plugin-dir` で指定したローカル開発コピーは、同名のインストール済みマーケットプレイスプラグインより優先されるようになりました。

```bash
# ローカル開発コピーでプラグインを起動（インストール済みの同名プラグインより優先）
claude --plugin-dir ./my-plugin
```

**優先順位（高い順）:**

1. `--plugin-dir` で指定したローカル開発コピー
2. インストール済みマーケットプレイスプラグイン（同名の場合）

**例外**: 管理設定（managed settings）によって `force-enabled` に設定されているプラグインは、`--plugin-dir` のローカルコピーより優先されます。

この変更により、プラグイン開発中にインストール済みの同名プラグインを一時的にアンインストールすることなく、ローカルの変更をテストできます。

## 検証

```bash
claude plugin validate .
```

**v2.1.77以降の検証強化**: `claude plugin validate` は以下を検証するようになりました:

- スキル（skill）のフロントマタースキーマ
- エージェント（agent）のフロントマタースキーマ
- スラッシュコマンド（command）のフロントマタースキーマ
- `hooks/hooks.json` のスキーマ
- YAMLパースエラー
- スキーマ違反
