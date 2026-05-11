---
paths: plugins/*/monitors/monitors.json, monitors/monitors.json
---

# バックグラウンドモニター（monitors/monitors.json）

プラグインモニターは、セッション中に常駐するシェルコマンドを自動起動し、その stdout の各行を Claude への通知として届ける仕組みです。Claude が自発的に watch を張らなくても、プラグイン側で監視対象を宣言できます。

## Monitor tool との関係

プラグインモニターは組み込みの Monitor tool と**同じメカニズム**で動作し、同じ可用性制約を共有します。プラグインモニター固有の差分は、**Claude に指示しなくても自動起動できる**点です。Monitor tool 本体の仕様については公式 [`/en/tools-reference#monitor-tool`](https://code.claude.com/docs/en/tools-reference#monitor-tool) を参照してください。

## 最低バージョン

- プラグインモニター: **Claude Code v2.1.105 以降** が必須
- Monitor tool 本体: v2.1.98 以降（プラグインモニターを使わない場合はこちらが下限）

## デフォルトファイル位置とフォーマット

| 項目 | 値 |
|------|----|
| デフォルトパス | `monitors/monitors.json` |
| トップレベル型 | JSON 配列（monitor エントリのリスト） |

## plugin.json での指定方法

プラグインルート直下に `monitors/monitors.json` を配置すれば自動検出されます（`plugin.json` での指定は不要）。明示的に指定する場合は、v2.1.129以降は `experimental` ブロック配下に宣言することが推奨されます（トップレベル宣言も引き続き動作するが `claude plugin validate` が警告を出す）:

```json
{
  "name": "my-plugin",
  "experimental": {
    "monitors": "./config/monitors.json"
  }
}
```

`monitors` はインライン配列としても指定できます:

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

**パス動作ルール**: `monitors` に独自パス文字列を指定した場合、デフォルトの `monitors/monitors.json` は読み込まれません（他のコンポーネント参照と同じ挙動）。

## 必須フィールド

| フィールド | 型 | 説明 |
|-----------|---|------|
| `name` | string | プラグイン内でユニークな識別子。プラグイン reload やスキル再起動時の重複プロセスを防ぐために使用される |
| `command` | string | セッションの作業ディレクトリで永続バックグラウンドプロセスとして実行されるシェルコマンド |
| `description` | string | 監視対象の短い要約。タスクパネルと通知サマリに表示される |

## オプションフィールド

| フィールド | 型 | 説明 |
|-----------|---|------|
| `when` | string | モニター起動タイミング。`"always"`（デフォルト、セッション開始時とプラグイン reload 時に起動）、`"on-skill-invoke:<skill-name>"`（指定したプラグイン内スキルが初めて起動されたときに起動）のいずれか。**これ以外の値は公式ドキュメントで明示されていません** |

## 変数展開

`command` 内では MCP/LSP と同じ変数展開が利用できます:

| 変数 | 用途 |
|------|------|
| `${CLAUDE_PLUGIN_ROOT}` | プラグインのインストールディレクトリへの絶対パス（プラグイン更新で変化する） |
| `${CLAUDE_PLUGIN_DATA}` | 更新をまたいで永続する状態ディレクトリ（`~/.claude/plugins/data/{id}/`） |
| `${user_config.<key>}` | `userConfig` で宣言した値 |
| `${ENV_VAR}` | 任意の環境変数 |

プラグインディレクトリで実行したい場合は、コマンド先頭に `cd "${CLAUDE_PLUGIN_ROOT}" &&` を付けて（末尾のスペース忘れに注意）コマンドを連結するパターンが推奨されています。

## ライフサイクル

- `when: "always"`（デフォルト）のモニターは**セッション開始時**および**プラグイン reload 時**に起動
- `when: "on-skill-invoke:<skill>"` のモニターは該当スキルの初回 dispatch 時に起動
- コマンドの **stdout の各行が notification として Claude に届く**
- モニターは**セッション終了時に停止**
- **セッション中にプラグインを無効化しても、既に実行中のモニタープロセスは停止しません**（再起動防止のため、`name` でユニーク性を担保する必要がある）

## 制約・実行環境

- **インタラクティブ CLI セッション限定**。非対話モードでは起動しません
- **非サンドボックス実行**。フックと同じ信頼レベルで動作（プラグインをインストール/有効化する行為は、これらのコマンドを信頼することと等価）
- Monitor tool が利用不可な環境ではスキップされます。具体的には以下のケース:
  - Amazon Bedrock
  - Google Vertex AI
  - Microsoft Foundry
  - 環境変数 `DISABLE_TELEMETRY` または `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` が設定されている場合
- `on-skill-invoke:<skill-name>` の `<skill-name>` はプラグイン内のスキル名と一致していること。**バリデーターはスキル名の実在チェック（クロスファイル検証）を行わない**ため、タイプミスがあると該当モニターが起動しない状態となる

## セキュリティ考慮事項

- モニターは非サンドボックスで実行されるため、コマンド内容はフックと同等の責任で扱うこと
- `${user_config.<key>}` を参照する場合、sensitive な値はキーチェーンから展開されます。コマンドログに値が漏れないよう注意してください
- すべてのパスはプラグインルートからの相対表現（`./` 開始）にとどめ、path traversal は使用しないこと

## 実例

公式 plugins-reference に掲載されている例（日本語コメント付き）:

```json
[
  {
    "name": "deploy-status",
    "command": "${CLAUDE_PLUGIN_ROOT}/scripts/poll-deploy.sh ${user_config.api_endpoint}",
    "description": "Deployment status changes"
  },
  {
    "name": "error-log",
    "command": "tail -F ./logs/error.log",
    "description": "Application error log",
    "when": "on-skill-invoke:debug"
  }
]
```

- 1つ目: デプロイ状況の変化を監視するスクリプト。セッション開始時に自動起動し、`${user_config.api_endpoint}` がキーチェーン/設定から注入される
- 2つ目: `debug` スキルが呼ばれた初回のみ `tail -F` でエラーログを監視開始

## 公式ドキュメントで明示されていない項目

以下の点は plugins-reference / tools-reference に明示されておらず、本ドキュメントでも保証しません:

- `stderr` / 終了コードの扱い（通知として届くのは stdout のみと記載）
- プロセスが異常終了した場合の自動再起動挙動（LSP の `restartOnCrash` に相当する仕組みの有無）
- 並列起動可能な monitor 数の上限
- 出力レート制限や通知のバッチング有無

## 出典

- [Plugins reference: Monitors](https://code.claude.com/docs/en/plugins-reference#monitors)
- [Plugins reference: File locations reference](https://code.claude.com/docs/en/plugins-reference#file-locations-reference)
- [Plugins reference: Environment variables](https://code.claude.com/docs/en/plugins-reference#environment-variables)
- [Plugins reference: Path behavior rules](https://code.claude.com/docs/en/plugins-reference#path-behavior-rules)
- [Tools reference: Monitor tool](https://code.claude.com/docs/en/tools-reference#monitor-tool)
