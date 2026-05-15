---
paths: plugins/*/hooks/hooks.json
---

# フック

フックは以下の2つの方法で定義できます:

1. **hooks.json** - プラグイン全体のフック（`hooks/hooks.json`）
2. **Frontmatter** - エージェント/スキル/スラッシュコマンド内のフック（YAML形式）

## hooks.json形式

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash|Edit|Write",
        "once": false,
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/validate.sh",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

## Frontmatter形式

エージェント、スキル、スラッシュコマンドのfrontmatter内でフックを定義できます:

```yaml
---
name: my-agent
hooks:
  PreToolUse:
    - matcher: "Bash"
      once: false
      hooks:
        - type: command
          command: "${CLAUDE_PLUGIN_ROOT}/scripts/check.sh"
  Stop:
    - hooks:
        - type: prompt
          prompt: "処理完了を確認"
---
```

## 対応イベント

| イベント | 説明 | マッチャー |
|---------|------|:---:|
| `PreToolUse` | ツール呼び出し前 | ✓ |
| `PostToolUse` | ツール呼び出し成功後 | ✓ |
| `PostToolUseFailure` | ツール呼び出し失敗後 | ✓ |
| `PermissionRequest` | 権限ダイアログ表示時 | ✓ |
| `PermissionDenied` | autoモードクラシファイアーによる拒否後（v2.1.88以降） | ✓ |
| `UserPromptSubmit` | ユーザープロンプト送信時 | × |
| `Notification` | 通知発行時 | ✓ |
| `Stop` | Claude終了時 | × |
| `StopFailure` | APIエラー（レート制限・認証失敗など）でターンが終了した時（v2.1.78以降） | × |
| `SubagentStart` | サブエージェント起動時 | ✓ |
| `SubagentStop` | サブエージェント終了時 | ✓ |
| `PreCompact` | コンパクト前（exit code 2または`{"decision":"block"}`でブロック可能・v2.1.105以降） | ✓ |
| `PostCompact` | コンパクション完了後（v2.1.76以降） | ✓ |
| `SessionStart` | セッション開始時 | ✓ |
| `SessionEnd` | セッション終了時 | × |
| `Setup` | セットアップ・メンテナンス時 | × |
| `TeammateIdle` | チームメイトエージェントがアイドル状態時 | × |
| `TaskCompleted` | タスク完了時 | × |
| `TaskCreated` | `TaskCreate` でタスクが作成された時（v2.1.84以降） | × |
| `ConfigChange` | セッション中に設定ファイルが変更された時 | ✓ |
| `CwdChanged` | カレントディレクトリが変更された時（direnvなどのリアクティブ環境管理用）（v2.1.83以降） | ✓ |
| `FileChanged` | ファイルが変更された時（direnvなどのリアクティブ環境管理用）（v2.1.83以降） | ✓ |
| `WorktreeCreate` | エージェントworktree分離でworktreeが作成された時 | × |
| `WorktreeRemove` | エージェントworktree分離でworktreeが削除された時 | × |
| `InstructionsLoaded` | CLAUDE.mdまたは`.claude/rules/*.md`がコンテキストに読み込まれた時（v2.1.64以降） | × |
| `Elicitation` | MCPエリシテーションのレスポンス送信前（v2.1.76以降） | ✓ |
| `ElicitationResult` | MCPエリシテーションのレスポンス結果（v2.1.76以降） | ✓ |

> **v2.1.75 フックソース表示**: パーミッションプロンプトでフックの確認が必要な場合、フックのソース（`settings` / `plugin` / `skill`）が表示されるようになりました。

## フックタイプ

### 共通オプション

全フックタイプで以下のオプションが使用可能:

| フィールド | 型 | 説明 |
|-----------|---|------|
| `statusMessage` | string | フック実行中にスピナーに表示するカスタムメッセージ |

### command（Bashコマンド）

Bashコマンドを実行:

```json
{
  "type": "command",
  "command": "${CLAUDE_PLUGIN_ROOT}/scripts/check.sh",
  "timeout": 30
}
```

`timeout`は秒単位で指定。省略時のデフォルトは600秒（10分）。

`async`（オプション）: `true`を指定するとフックを非同期で実行し、結果を待たずにツール実行を続行します。

**async フックの stdin（v2.1.72で修正）**: v2.1.72以降、`async: true` で実行されるフックでも `bash read -r` 等を使用して stdin を正常に受け取れるようになりました。それ以前のバージョンでは async フックが stdin を受け取れないバグがありました。

### prompt（LLM評価）

LLMを使用してプロンプトを評価:

```json
{
  "type": "prompt",
  "prompt": "タスク完了を評価: $ARGUMENTS",
  "timeout": 30
}
```

`timeout`は秒単位で指定。省略時のデフォルトは30秒。

**注**: プラグインからは`prompt`と`agent`タイプもサポートされます（v2.1.0以降）。

#### prompt型フックの出力と継続制御

`prompt` 型フックはLLMが評価した結果を `{ok: boolean, reason: string}` のJSON形式で出力します。非Stopイベント（`PreToolUse` など）で `ok: false` が返された場合、ツール実行や処理の継続がブロックされます（v2.1.92でセマンティクス回復）。`reason` フィールドの内容がユーザーへのブロック理由として表示されます。

```json
{
  "ok": false,
  "reason": "処理を中断した理由"
}
```

| フィールド | 型 | 説明 |
|-----------|---|------|
| `ok` | boolean | 条件が満たされたかどうか。`false` の場合、非Stopイベントではツール実行等の継続がブロックされる |
| `reason` | string | 判定理由。`ok: false` 時にユーザーへブロック理由として表示される |

**注意（v2.1.92）**: 非Stopイベントの `prompt` 型フックに対する `ok: false` による継続ブロックのセマンティクスが回復されました。

### agent（エージェント起動）

特定のエージェントを起動:

```json
{
  "type": "agent",
  "agent": "code-reviewer",
  "prompt": "コードの品質・セキュリティ・保守性をレビューしてください: $ARGUMENTS",
  "timeout": 120
}
```

| フィールド | 型 | 必須 | 説明 |
|-----------|---|:---:|------|
| `type` | string | ✓ | `"agent"` を指定 |
| `agent` | string | ✓ | 起動するエージェント名 |
| `prompt` | string | ✓ | エージェントに渡すタスク記述 |
| `timeout` | number | | タイムアウト（秒単位、省略時: 60秒） |

### mcp_tool（MCPツール呼び出し）【v2.1.118以降】

MCPツールをフック内から直接呼び出す:

```json
{
  "type": "mcp_tool",
  "server": "my-mcp-server",
  "tool": "tool-name"
}
```

| フィールド | 型 | 必須 | 説明 |
|-----------|---|:---:|------|
| `type` | string | ✓ | `"mcp_tool"` を指定 |
| `server` | string | ✓ | 呼び出すMCPサーバー名（`mcpServers` で定義したキー名） |
| `tool` | string | ✓ | 呼び出すツール名 |

### http（HTTPリクエスト）【v2.1.51以降】

<!-- validator-disable dangerous-operation -->

HTTPエンドポイントにJSONをPOSTし、サーバーからのJSONレスポンスを受信・処理するフックタイプ（v2.1.51以降、JSONレスポンス処理はv2.1.63以降）:

```json
{
  "type": "http",
  "url": "https://api.example.com/webhook",
  "method": "POST",
  "headers": {
    "Authorization": "Bearer ${API_TOKEN}",
    "Content-Type": "application/json"
  },
  "allowedEnvVars": ["API_TOKEN"],
  "timeout": 30
}
```

> **セキュリティ変更（v2.1.51・破壊的変更）**: ヘッダー値での環境変数展開（`${VAR}` 形式）には、`allowedEnvVars` フィールドへの明示的なホワイトリスト登録が必須となりました。これはHTTPフックが任意の環境変数をヘッダーに展開できたセキュリティ問題への対応です。

#### フィールド説明

| フィールド | 型 | 必須 | 説明 |
|-----------|---|:---:|------|
| `type` | string | ✓ | `"http"` を指定 |
| `url` | string | ✓ | リクエスト送信先URL |
| `method` | string | | HTTPメソッド（省略時: `POST`） |
| `headers` | object | | リクエストヘッダー |
| `allowedEnvVars` | array | ✓* | ヘッダー値で展開を許可する環境変数名のリスト（*ヘッダーで環境変数を使用する場合は必須） |
| `timeout` | number | | タイムアウト（秒単位、省略時: 600秒） |

#### `allowedEnvVars` の使い方

ヘッダー値で環境変数を使用する場合は、使用する変数名を `allowedEnvVars` に列挙する必要があります:

```json
{
  "type": "http",
  "url": "https://api.example.com/hook",
  "headers": {
    "X-Auth-Token": "${MY_SECRET_TOKEN}",
    "X-Team-ID": "${TEAM_ID}"
  },
  "allowedEnvVars": ["MY_SECRET_TOKEN", "TEAM_ID"]
}
```

`allowedEnvVars` に含まれていない環境変数は展開されず、リテラル文字列として扱われます。

#### HTTPフックのJSONレスポンス処理

HTTPフックはサーバーからのJSONレスポンスを受信・処理できます。レスポンスのJSONスキーマは `command` フックの stdout JSON と同様です（[JSON出力スキーマ](#json出力スキーマ)を参照）:

```json
{
  "continue": true,
  "stopReason": "停止メッセージ",
  "systemMessage": "警告メッセージ",
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow|deny|ask|defer",
    "updatedInput": { "field": "new_value" }
  }
}
```

**サーバー側の実装例（Node.js）:**

```javascript
// Expressサーバーの例
app.post('/webhook', (req, res) => {
  const hookData = req.body;
  // フックデータを処理...
  res.json({
    continue: true,
    systemMessage: "監査ログを記録しました"
  });
});
```

HTTPフックのレスポンスでJSONを返さない場合（200以外のステータスコードや空のボディ）、フックは警告として扱われ処理が継続されます。

#### HTTPフックの制限事項（v2.1.51以降）

- **`SessionStart` および `Setup` イベントでは使用不可**: HTTPフックはこれらのイベントに対応していません
- **サンドボックスモード時のプロキシ経由ルーティング**: サンドボックスモードが有効な場合、HTTPフックはサンドボックスネットワークプロキシ経由でルーティングされ、ドメイン許可リストが適用されます

## フックタイプ制限（v2.1.142以降）

`SessionStart`・`Setup`・`SubagentStart` イベントでは、`prompt` 型および `agent` 型のフックは使用できません。これらのイベントには `command` 型のみ有効です。誤った設定時は「use a command-type hook instead」というエラーが表示されます。

| イベント | command | prompt | agent | http | mcp_tool |
|---------|:-------:|:------:|:-----:|:----:|:--------:|
| `SessionStart` | ✓ | ✗ | ✗ | ✗ | ✓ |
| `Setup` | ✓ | ✗ | ✗ | ✗ | ✓ |
| `SubagentStart` | ✓ | ✗ | ✗ | ✓ | ✓ |
| `PostCompact` | ✓ | ✗ | ✗ | ✗ | ✗ |
| その他のイベント | ✓ | ✓ | ✓ | ✓ | ✓ |

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "http",
            "url": "https://audit.example.com/log",
            "method": "POST",
            "allowedEnvVars": []
          }
        ]
      }
    ]
  }
}
```

## matcher の仕様

| パターン | 例 | マッチ対象 |
|---------|-----|----------|
| 完全一致 | `Bash` | Bashのみ |
| 複数（OR） | `Edit\|Write` | EditまたはWrite |
| 正規表現 | `Notebook.*` | Notebookで始まるすべて |
| MCPツール | `mcp__github__.*` | githubサーバーのすべて |

**注意**: 大文字小文字を区別

## once フィールド

フックを一度だけ実行する場合は `once: true` を指定:

**hooks.json形式:**

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "once": true,
        "hooks": [
          {
            "type": "command",
            "command": "echo '初回のみ実行'"
          }
        ]
      }
    ]
  }
}
```

**Frontmatter形式:**

```yaml
hooks:
  PreToolUse:
    - matcher: "Bash"
      once: true
      hooks:
        - type: command
          command: "echo '初回のみ実行'"
```

- `true`: フックは最初のマッチ時のみ実行
- `false`（デフォルト）: マッチするたびに実行

## if フィールド（v2.1.85以降）

フックエントリにパーミッションルール構文（例: `Bash(git *)`）で条件を指定し、条件が一致する場合のみフックを実行します。プロセス生成のオーバーヘッドを削減するために使用します。

**hooks.json形式:**

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "if": "Bash(git *)",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/git-check.sh"
          }
        ]
      }
    ]
  }
}
```

**Frontmatter形式:**

```yaml
hooks:
  PreToolUse:
    - matcher: "Bash"
      if: "Bash(git *)"
      hooks:
        - type: command
          command: "${CLAUDE_PLUGIN_ROOT}/scripts/git-check.sh"
```

- `if` フィールドはパーミッションルール構文（`ToolName(pattern)`）を使用
- 条件が一致する場合のみフックが実行される
- `matcher` との違い: `matcher` はフックを紐付けるツールを指定し、`if` は実際に実行する条件を絞り込む

## Exit Code

フックスクリプトの終了コードによって、Claude Codeの動作が変わります:

| コード | 意味 | 処理 |
|--------|------|------|
| `0` | 成功 | stdout処理、JSON解析を実行し、ツールを続行 |
| `2` | ブロック | ツール実行を中止、stderrをユーザーに表示（v2.1.39以降） |
| `1, 3+` | 警告 | stderrを表示し、処理を継続 |

**v2.1.39での変更**: exit code 2でブロックされた場合、stderrの内容がユーザーに表示されるようになりました。これにより、フックがツール実行をブロックした理由をユーザーに伝えることができます。

**使用例**:

```bash
#!/bin/bash
# 本番環境での危険な操作をブロック

if [[ "$ENVIRONMENT" == "production" ]]; then
  echo "Error: 本番環境での操作は禁止されています" >&2
  exit 2
fi

exit 0
```

### ブロック時のメッセージ（v2.1.39以降）

exit code 2でツール実行をブロックする場合、stderrに出力された内容がユーザーに表示されます。
ユーザーがブロックの理由を理解できるよう、明確なメッセージを出力することを推奨します。

**良い例:**

```bash
#!/bin/bash
# ファイル削除をブロックする例

echo "エラー: 本番環境でのファイル削除は禁止されています。" >&2
echo "詳細: https://example.com/docs/production-safety" >&2
exit 2
```

**悪い例:**

```bash
#!/bin/bash
# メッセージなしでブロック
exit 2  # ユーザーには理由が伝わらない
```

## JSON出力スキーマ

```json
{
  "continue": true,
  "stopReason": "停止メッセージ",
  "systemMessage": "警告メッセージ",
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow|deny|ask|defer",
    "updatedInput": { "field": "new_value" },
    "additionalContext": "モデルに提供する追加コンテキスト（PreToolUseのみ）"
  }
}
```

### PostToolUse フックでのツール出力置き換え（v2.1.121以降）

`PostToolUse` フックは `hookSpecificOutput.updatedToolOutput` を返すことで、ツールの出力を置き換えることができます。v2.1.121以降、MCPツールだけでなく Bash、Edit、Write などすべてのツールに対応しました。

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "updatedToolOutput": "置き換えるツール出力内容"
  }
}
```

| フィールド | 型 | 説明 |
|-----------|---|------|
| `updatedToolOutput` | string | ツールの出力を置き換える文字列。すべてのツール（Bash、Edit、Write、MCPツール等）に対応（v2.1.121以降） |

> **注意（v2.1.89以降）**: フックスクリプトが **50K文字を超える出力** を返した場合、コンテキストに直接注入される代わりに **ディスクに保存** され、ファイルパスとプレビューのみが提供されます。大量の出力を返すフックの動作に注意してください。
>
> **注意（v2.1.101以降）**: `permissionDecision: "ask"` を返しても、`permissions.deny` ルールが設定されている場合は **deny が優先** されます。
>
> **注意（v2.1.110以降）**: `PermissionRequest` フックが `updatedInput` を返した場合も、`permissions.deny` ルールによる再チェックが行われ、deny が優先されます。

### setMode フィールド（v2.1.110以降）

`PermissionRequest` フックの出力 JSON で `setMode: "bypassPermissions"` を返すと、パーミッションモードを切り替えることができます。

```json
{
  "continue": true,
  "setMode": "bypassPermissions"
}
```

**制約:**

- `disableBypassPermissionsMode` が設定されている場合、`setMode: "bypassPermissions"` は無効になります（v2.1.110以降）

### PreToolUseフックの追加コンテキスト

`PreToolUse`フックは、`additionalContext`フィールドを使用してモデルに追加のコンテキストを提供できます（v2.1.9以降）。

**使用例:**

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/context.sh"
          }
        ]
      }
    ]
  }
}
```

**scripts/context.sh:**

```bash
#!/bin/bash
# ツール実行前にコンテキスト情報を提供

cat <<EOF
{
  "continue": true,
  "hookSpecificOutput": {
    "additionalContext": "注意: 本番環境での実行です。慎重に操作してください。"
  }
}
EOF
```

**ユースケース:**

- 環境固有の警告や注意事項を提供
- 実行前のチェック結果をモデルに伝達
- 動的に変化するコンテキスト情報の追加
- コンプライアンス要件の通知

### PreToolUseフックの "defer" パーミッション決定値（v2.1.89以降）

`PreToolUse` フックで `permissionDecision: "defer"` を返すと、ヘッドレスセッションでツール呼び出しを一時停止できます。その後 `-p --resume` で再開すると、フックが再評価されます。

```json
{
  "continue": true,
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "defer"
  }
}
```

**ユースケース:**

- ヘッドレスパイプラインで人間のレビューが必要な操作を一時停止する
- 外部承認フローが完了するまでツール実行を保留する

### AskUserQuestion の回答をフックで提供（v2.1.85以降）

ヘッドレス統合において、`PreToolUse` フックが `updatedInput` を `permissionDecision: "allow"` と組み合わせて返すことで、`AskUserQuestion` ツールの回答をフックが代わりに提供できます:

```json
{
  "continue": true,
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow",
    "updatedInput": {
      "answer": "yes"
    }
  }
}
```

**ユースケース:**

- CI/CD パイプラインなどのヘッドレス環境で `AskUserQuestion` の確認を自動化
- ユーザーの代わりにフックが回答を事前に決定して提供

## 環境変数

- `${CLAUDE_PLUGIN_ROOT}` - プラグインルートへの絶対パス
- `${CLAUDE_PROJECT_DIR}` - プロジェクトルートへの絶対パス
- `${CLAUDE_PLUGIN_DATA}` - プラグインの永続データディレクトリへの絶対パス。プラグインのアップデートを超えて永続化される（v2.1.78以降）。`/plugin uninstall` 実行時は削除前に確認プロンプトが表示される
- `$ARGUMENTS` - フック入力JSON（prompt型で使用）
- `$CLAUDE_EFFORT` - 現在のエフォートレベル（`low` / `medium` / `high` / `xhigh` / `max`）（v2.1.133以降）

## フック入力JSON

フック実行時、stdinにJSON形式で入力が渡されます:

```json
{
  "session_id": "セッションID",
  "transcript_path": "/path/to/transcript.json",
  "cwd": "/current/working/directory",
  "permission_mode": "default",
  "hook_event_name": "PreToolUse",
  "effort": {
    "level": "high"
  },
  "tool_name": "Edit",
  "tool_input": { "file_path": "/path/to/file", "old_string": "...", "new_string": "..." },
  "tool_use_id": "toolu_abc123"
}
```

| フィールド | 説明 |
|-----------|------|
| `session_id` | セッションID |
| `transcript_path` | トランスクリプトファイルのパス |
| `cwd` | 現在の作業ディレクトリ |
| `permission_mode` | 現在のパーミッションモード（`default`, `plan`, `acceptEdits`, `dontAsk`, `bypassPermissions`） |
| `hook_event_name` | フックイベント名 |
| `tool_name` | 実行されるツール名 |
| `tool_input` | ツールへの入力パラメータ |
| `tool_use_id` | ツール呼び出しの一意識別子（トラッキング用） |
| `effort.level` | 現在のエフォートレベル（`low` / `medium` / `high` / `xhigh` / `max`）（v2.1.133以降） |
| `agent_id` | サブエージェントから実行された場合のエージェントID（v2.1.64以降） |
| `agent_type` | `--agent`フラグで起動された場合のエージェントタイプ（v2.1.64以降） |

### Stop / SubagentStop イベントの入力（v2.1.47以降）

`Stop` および `SubagentStop` フックには、追加フィールド `last_assistant_message` が渡されます（v2.1.47以降）:

```json
{
  "last_assistant_message": "タスクが完了しました。変更内容を確認してください。"
}
```

| フィールド | 説明 |
|-----------|------|
| `last_assistant_message` | 最後のアシスタント応答テキスト |

これにより、フックスクリプトがトランスクリプトファイルをパースすることなく、最後のアシスタント応答にアクセスできます。

**使用例:**

```bash
#!/bin/bash
# 最後のアシスタントメッセージを取得してログに記録
input=$(cat)
last_message=$(echo "$input" | jq -r '.last_assistant_message // ""')

if [ -n "$last_message" ]; then
  echo "完了メッセージ: $last_message" >> /tmp/session-log.txt
fi
```

### PostToolUse / PostToolUseFailure イベントの追加フィールド（v2.1.119以降）

`PostToolUse` および `PostToolUseFailure` フックには、追加フィールド `duration_ms` が渡されます（v2.1.119以降）:

```json
{
  "duration_ms": 1234
}
```

| フィールド | 型 | 説明 |
|-----------|---|------|
| `duration_ms` | number | ツール実行時間（ミリ秒）。パーミッションプロンプトと PreToolUse フックの実行時間を除く |

## イベント詳細

### SessionStart

セッション開始時に実行されるフック。

**注意（v2.1.47以降）**: `SessionStart` フックの実行は、起動パフォーマンス改善のため、セッション開始後に約500ms遅延して実行されます。フックが起動直後に即座に実行されることを前提としたロジックがある場合は注意が必要です。

**使用例:**

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/session-init.sh",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

**`agent_type`入力**: `--agent`フラグでセッションを開始した場合、SessionStartフックのJSON入力に`agent_type`フィールドが含まれます。

**`CLAUDE_ENV_FILE`**: SessionStartフックでは`CLAUDE_ENV_FILE`環境変数にファイルパスが設定されます。このファイルに`export KEY=VALUE`形式で環境変数を書き込むと、セッション全体で利用可能になります。

**ユースケース:**

- セッション開始時の初期化処理
- ウェルカムメッセージの表示
- 環境チェック（遅延実行を考慮した設計が必要）

### SessionEnd

セッション終了時に実行されるフック。

**タイムアウト設定（v2.1.74で修正・追加）:**

v2.1.74より前のバージョンでは、`SessionEnd` フックは `hook.timeout` の設定に関わらず終了時に1.5秒でkillされていましたが、このバグが修正されました。また、環境変数 `CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS` を設定することで、セッション終了フックのタイムアウト時間をミリ秒単位でカスタマイズできます。

```bash
# セッション終了フックのタイムアウトを5秒に設定
export CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS=5000
```

**使用例:**

```json
{
  "hooks": {
    "SessionEnd": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/session-cleanup.sh",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

**ユースケース:**

- セッション終了時のクリーンアップ処理
- セッションサマリーの記録
- 一時ファイルの削除
- 通知の送信

### Setup

リポジトリのセットアップとメンテナンス操作時に実行されるフック。以下のCLIフラグでトリガーされます:

- `--init`: 初期セットアップ実行後にフックをトリガー
- `--init-only`: セットアップのみ実行（会話を開始しない）
- `--maintenance`: メンテナンス操作実行

**使用例:**

```json
{
  "hooks": {
    "Setup": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/setup.sh",
            "timeout": 60
          }
        ]
      }
    ]
  }
}
```

**ユースケース:**

- 依存パッケージのインストール
- 設定ファイルの生成
- 開発環境の初期化
- キャッシュのクリア
- スキルファイルの生成（サンドボックス制限の回避策として）

**サンドボックスモードとSetupフック（v2.1.38以降）:**

サンドボックスモードでは`.claude/skills`ディレクトリへの実行時の書き込みがブロックされます。スキルを動的に生成する必要がある場合は、`Setup`フックを使用してセットアップ時（`--init`または`--init-only`フラグ）に生成することを推奨します。

```json
{
  "hooks": {
    "Setup": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/generate-skills.sh",
            "timeout": 60
          }
        ]
      }
    ]
  }
}
```

この方法により、サンドボックス制限を受けることなく、初期セットアップ時にスキルを生成できます。

### TeammateIdle

マルチエージェントワークフロー環境で、チームメイトエージェントがアイドル状態（待機中）になったときに実行されるフック（v2.1.33以降）。

**使用例:**

```json
{
  "hooks": {
    "TeammateIdle": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/notify-idle.sh",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

**停止サポート（v2.1.64以降）:**

`TeammateIdle` フックで `{"continue": false, "stopReason": "..."}` を返すことで、チームメイトエージェントを停止できます（`Stop` フックと同様の動作）:

```bash
#!/bin/bash
echo '{"continue": false, "stopReason": "タスクは完了しました。これ以上の処理は不要です。"}'
```

**ユースケース:**

- アイドル状態のエージェントへのタスク割り当て
- リソース効率化のためのエージェント管理
- ワークフロー調整・最適化
- チーム協調の可視化

### TaskCompleted

マルチエージェントワークフロー環境で、タスクが完了したときに実行されるフック（v2.1.33以降）。

**使用例:**

```json
{
  "hooks": {
    "TaskCompleted": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/task-notification.sh",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

**停止サポート（v2.1.64以降）:**

`TaskCompleted` フックで `{"continue": false, "stopReason": "..."}` を返すことで、チームメイトエージェントを停止できます（`Stop` フックと同様の動作）:

```bash
#!/bin/bash
echo '{"continue": false, "stopReason": "タスクが完了しました。後続処理は不要です。"}'
```

**ユースケース:**

- タスク完了の通知・ログ記録
- 次のタスクへの自動トリガー
- 成果物の検証・レビュー
- プロジェクト進捗の追跡

### TaskCreated

`TaskCreate` でタスクが作成された時に実行されるフック（v2.1.84以降）。

**使用例:**

```json
{
  "hooks": {
    "TaskCreated": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/on-task-created.sh",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

**入力JSON（固有フィールド）:**

| フィールド | 型 | 説明 |
|-----------|---|------|
| `task_id` | string | 作成されるタスクのID |
| `task_subject` | string | タスクのタイトル |
| `task_description` | string | タスクの詳細説明（省略される場合あり） |
| `teammate_name` | string | タスクを作成するチームメイト名（省略される場合あり） |
| `team_name` | string | チーム名（省略される場合あり） |

共通フィールド（`session_id`, `transcript_path`, `cwd`, `permission_mode`, `hook_event_name`）も含まれます。`TaskCompleted` と同一の構造で、`hook_event_name` のみ異なります。

**終了コードによる制御:**

| 終了コード | 動作 |
|-----------|------|
| 0 | 成功（タスク作成を続行） |
| 2 | stderrの内容がモデルにフィードバックされ、タスク作成がブロックされる |
| その他 | stderrはユーザーにのみ表示（タスク作成はブロックしない） |

**ユースケース:**

- タスク作成のログ記録
- タスク作成の通知
- タスク作成時のバリデーション（終了コード2でブロック可能）
- タスク作成時の初期化処理

### ConfigChange

セッション中に設定ファイルが変更されたときに実行されるフック（v2.1.49以降）。エンタープライズのセキュリティ監査や設定変更のブロックに使用できます。

**使用例:**

```json
{
  "hooks": {
    "ConfigChange": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/audit-config.sh",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

**ユースケース:**

- 設定変更のセキュリティ監査ログ記録
- 未承認の設定変更をブロック（exit code 2を返すことで）
- 設定変更の通知・アラート
- エンタープライズポリシーの強制適用

**セキュリティ監査の例:**

```bash
#!/bin/bash
# 設定変更を監査ログに記録

input=$(cat)
timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
echo "$timestamp ConfigChange detected: $input" >> /var/log/claude-audit.log

exit 0
```

**設定変更ブロックの例:**

```bash
#!/bin/bash
# 特定の設定変更をブロック

input=$(cat)
# 危険な設定変更を検出した場合はブロック
echo "エラー: この設定変更はポリシーにより禁止されています。" >&2
exit 2
```

### WorktreeCreate

エージェントのworktree分離（`isolation: worktree`）で、新しいgit worktreeが作成されたときに実行されるフック（v2.1.50以降）。

**使用例:**

```json
{
  "hooks": {
    "WorktreeCreate": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/worktree-setup.sh",
            "timeout": 60
          }
        ]
      }
    ]
  }
}
```

**HTTPタイプのサポート（v2.1.84以降）:**

`WorktreeCreate` フックは `type: "command"` に加えて `type: "http"` もサポートしています。HTTPフックのレスポンスJSONで `hookSpecificOutput.worktreePath` を返すことで、作成するworktreeのパスをカスタマイズできます:

```json
{
  "type": "http",
  "url": "https://api.example.com/worktree-setup",
  "timeout": 30
}
```

**HTTPレスポンスの例（worktreePathを指定する場合）:**

```json
{
  "hookSpecificOutput": {
    "worktreePath": "/custom/path/to/worktree"
  }
}
```

**注意:** `worktreePath` は絶対パスで指定する必要があります。`hookSpecificOutput.worktreePath` を省略した場合やフックが失敗した場合、デフォルトパスへのフォールバックは行われず、worktree作成自体が失敗します。

**ユースケース:**

- worktree作成時の依存パッケージインストール
- worktree固有の設定ファイル生成
- カスタムVCSセットアップ処理
- worktree作成通知・ログ記録
- 外部サービスとの連携によるworktreeパスのカスタマイズ

### WorktreeRemove

エージェントのworktree分離（`isolation: worktree`）で、git worktreeが削除されたときに実行されるフック（v2.1.50以降）。

**使用例:**

```json
{
  "hooks": {
    "WorktreeRemove": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/worktree-cleanup.sh",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

**ユースケース:**

- worktree削除時のクリーンアップ処理
- 一時ファイルの削除
- worktree削除通知・ログ記録
- リソースの解放

### InstructionsLoaded

CLAUDE.mdまたは`.claude/rules/*.md`ファイルがコンテキストに読み込まれたときに実行されるフック（v2.1.64以降）。

**使用例:**

```json
{
  "hooks": {
    "InstructionsLoaded": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/on-instructions-loaded.sh",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

**ユースケース:**

- 指示ファイルの読み込みをログに記録
- 読み込まれた指示の検証
- 追加コンテキストのセットアップ

### PreCompact

コンパクション実行前に発火するフック。exit code 2または`{"decision":"block"}`を返すことでコンパクションをブロックできます（v2.1.105以降）。

**マッチャー**: `trigger`フィールドでマッチ（`manual` = `/compact`コマンド実行時、`auto` = コンテキストウィンドウ超過時の自動コンパクト時）

**使用例:**

```json
{
  "hooks": {
    "PreCompact": [
      {
        "matcher": "auto",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/pre-compact.sh",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

**入力JSON（固有フィールド）:**

| フィールド | 型 | 説明 |
|-----------|---|------|
| `trigger` | string | `"manual"`（`/compact`コマンド実行時）または `"auto"`（自動コンパクト時） |

**コンパクションのブロック（v2.1.105以降）:**

以下のいずれかの方法でコンパクションをブロックできます:

1. exit code `2` で終了（stderrの内容がユーザーに表示される）
2. 以下のJSONをstdoutに出力:

```json
{"decision":"block"}
```

**使用例（コンパクションブロック）:**

```bash
#!/bin/bash
# 自動コンパクションをブロックする例

input=$(cat)
trigger=$(echo "$input" | jq -r '.trigger')

if [[ "$trigger" == "auto" ]]; then
  echo "自動コンパクションをブロックしました" >&2
  exit 2
fi

exit 0
```

**ユースケース:**

- コンパクション実行前のログ記録・通知
- 特定の条件下でのコンパクションのブロック
- コンパクションのタイミング制御

### PostCompact

コンパクション完了後に実行されるフック（v2.1.76以降）。コンパクション結果のブロックや変更はできません（ログ・通知用途）。

**マッチャー**: `trigger`フィールドでマッチ（`manual` = `/compact`コマンド実行後、`auto` = コンテキストウィンドウ超過時の自動コンパクト後）

**対応フックタイプ**: `command` のみ

**使用例:**

```json
{
  "hooks": {
    "PostCompact": [
      {
        "matcher": "auto",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/post-compact.sh",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

**入力JSON（固有フィールド）:**

| フィールド | 型 | 説明 |
|-----------|---|------|
| `trigger` | string | `"manual"`（`/compact`コマンド実行時）または `"auto"`（自動コンパクト時） |
| `compact_summary` | string | コンパクト操作で生成された会話サマリー |

**出力JSON:**

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PostCompact",
    "additionalContext": "Claudeへ追加コンテキスト"
  }
}
```

**ユースケース:**

- コンパクション後の状態確認・ログ記録
- コンパクション完了通知の送信
- コンパクション後のクリーンアップ処理

### Elicitation

MCPサーバーが構造化入力（フォームフィールドまたはブラウザURL）をリクエストした際、レスポンス送信前に実行されるフック（v2.1.76以降）。
MCPエリシテーション機能のレスポンスをインターセプト・オーバーライドできます。

**マッチャー**: `mcp_server_name`（MCPサーバー名）でマッチ

**使用例:**

```json
{
  "hooks": {
    "Elicitation": [
      {
        "matcher": "my-auth-server",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/handle-elicitation.sh",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

**入力JSON（固有フィールド）:**

| フィールド | 型 | 説明 |
|-----------|---|------|
| `mcp_server_name` | string | 入力を要求しているMCPサーバー名（matcher対象） |
| `message` | string | ユーザーに表示されるメッセージ |
| `mode` | string | `"form"`（フォーム入力）または `"url"`（ブラウザ認証） |
| `requested_schema` | object | フォームモード時のフィールドのJSONスキーマ（optional） |
| `url` | string | URLモード時の認証URL（optional） |
| `elicitation_id` | string | エリシテーションの一意識別子（optional） |

**出力JSON:**

```json
{
  "hookSpecificOutput": {
    "hookEventName": "Elicitation",
    "action": "accept|decline|cancel",
    "content": { "username": "alice" }
  }
}
```

- `action`: `accept`（承認しフォーム値を送信）、`decline`（拒否）、`cancel`（キャンセル）
- `content`: `action`が`accept`の場合のみ有効。フォームフィールドの値
- exit code 2でエリシテーションを拒否可能

**ユースケース:**

- MCPエリシテーションリクエストのログ記録
- エリシテーションレスポンスの自動入力・オーバーライド
- セキュリティポリシーに基づくエリシテーションのブロック

### ElicitationResult

MCPエリシテーションのレスポンス結果を受け取るフック（v2.1.76以降）。
ユーザーがMCPエリシテーションに応答した後、応答をサーバーに返す前に発火します。応答の観察・修正・ブロックが可能です。

**マッチャー**: `mcp_server_name`（MCPサーバー名）でマッチ

**使用例:**

```json
{
  "hooks": {
    "ElicitationResult": [
      {
        "matcher": "my-auth-server",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/elicitation-result.sh",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

**入力JSON（固有フィールド）:**

| フィールド | 型 | 説明 |
|-----------|---|------|
| `mcp_server_name` | string | MCPサーバー名（matcher対象） |
| `action` | string | ユーザーのアクション: `"accept"` / `"decline"` / `"cancel"` |
| `mode` | string | `"form"` または `"url"` |
| `content` | object | ユーザーが送信したフォーム値（`action`が`accept`の場合のみ、optional） |
| `elicitation_id` | string | 対応するElicitationイベントのID（optional） |

**出力JSON:**

```json
{
  "hookSpecificOutput": {
    "hookEventName": "ElicitationResult",
    "action": "accept|decline|cancel",
    "content": { "username": "modified_value" }
  }
}
```

- `action`/`content`でユーザーの応答をオーバーライド可能
- exit code 2で応答をブロック（actionが`decline`に変更される）

**ユースケース:**

- エリシテーション結果の監査ログ記録
- エリシテーション結果に基づく後続処理のトリガー
- セキュリティポリシーに基づく応答のブロック・修正

### PermissionDenied

autoモード（自動モード）のクラシファイアーがツール実行を拒否した後に発火するフック（v2.1.88以降）。
フックから `{retry: true}` を返すと、モデルにリトライを促すことができます。

**使用例:**

```json
{
  "hooks": {
    "PermissionDenied": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/handle-denied.sh",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

**返却値:**

| フィールド | 型 | 説明 |
|-----------|---|------|
| `retry` | boolean | `retry: true` を返すとモデルにリトライを促す |

**ユースケース:**

- 拒否されたコマンドの監査ログ記録
- 条件によってリトライを許可する（例: 特定のパターンのみ）

### UserPromptSubmit

ユーザーがプロンプトを送信したときに実行されるフック。

**使用例:**

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/on-prompt-submit.sh",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

**出力JSON（v2.1.94以降）:**

`UserPromptSubmit` フックは `hookSpecificOutput.sessionTitle` フィールドをサポートしています。これを使用すると、セッションのタイトルをカスタマイズできます。

```json
{
  "continue": true,
  "hookSpecificOutput": {
    "sessionTitle": "カスタムセッションタイトル"
  }
}
```

| フィールド | 型 | 説明 |
|-----------|---|------|
| `hookSpecificOutput.sessionTitle` | string | セッションのタイトルを設定する（v2.1.94以降） |

**ユースケース:**

- プロンプト送信のログ記録・監査
- プロンプト内容に基づくセッションタイトルの自動設定
- プロンプト送信時の前処理・バリデーション

## パーミッション優先順位（v2.1.27以降）

Claude Codeのパーミッションシステムでは、より具体的な制限が優先されます。

### 基本ルール

content-level（具体的パターン）の `ask` 設定は、tool-level（ツール全体）の `allow` 設定より**優先されます**。

**YAML形式（エージェント/スキル/スラッシュコマンド）:**

```yaml
---
allow: ["Bash"]
ask: ["Bash(rm *)"]
---
```

**JSON形式（hooks.jsonなど）:**

```json
{
  "allow": ["Bash"],
  "ask": ["Bash(rm *)"]
}
```

### 動作説明

上記の設定では:

1. `Bash` ツール全体は許可（`allow`）されています
2. しかし `rm` コマンドのみ確認プロンプトが表示されます（`ask` が優先）
3. `rm` 以外のBashコマンド（`ls`, `cd` など）は確認なしで実行できます

### 実用例

```yaml
---
# 危険なコマンドのみ制限
allow: ["Bash"]
ask: [
  "Bash(rm *)",      # ファイル削除
  "Bash(dd *)",      # ディスク操作
  "Bash(sudo *)",    # 管理者権限
  "Bash(chmod *)"    # 権限変更
]
---
```

### フックとの関係

フックの `PermissionRequest` イベントは、この優先順位が適用された**後**の権限リクエストでトリガーされます。つまり:

- `allow` で許可されたツールは `PermissionRequest` イベントをトリガーしません
- `ask` で確認が必要なツールのみ `PermissionRequest` イベントが発火します
- content-levelの `ask` が tool-levelの `allow` より優先されるため、危険な操作のみフックで処理できます

### `PreToolUse` フックの `permissionDecision` と `deny` ルールの優先順位

`PreToolUse` フックが `permissionDecision: "allow"` を返しても、設定の `deny` ルールが常に優先されます。

- `deny` ルールはフックの `allow` 判断より常に優先される
- エンタープライズのマネージド設定による制限はフックによって回避できない

### 関連ドキュメント

パーミッション設定の詳細は [plugin-manifest.md](plugin-manifest.md) を参照してください。

## セッション再開とフックコンテキスト（v2.1.29以降）

Claude Codeはセッション再開時にフックコンテキストを保存・復元する機能を提供しています。ただし、`saved_hook_context`の使用には以下の注意が必要です。

### パフォーマンス上の考慮事項

- セッション再開時、保存されたフックコンテキストが復元されます
- 大量のコンテキストデータを保存すると、セッション再開時のパフォーマンスに影響する可能性があります
- v2.1.29でパフォーマンス改善が行われましたが、コンテキストサイズには注意が必要です

### 推奨される使用方法

- フックコンテキストには必要最小限の情報のみを保存する
- 大量のログやデバッグ情報を保存しない
- 状態管理が必要な場合は、外部ファイルへの保存を検討する

## セキュリティ注意事項

フックは自動実行されるため、悪意あるコードはシステムに損害を与える可能性があります。

```bash
# 変数は必ずクォート
"$VAR"      # 良い
$VAR        # 危険

# パストラバーサル防止
if [[ "$path" == *".."* ]]; then
  exit 2
fi
```

### ワークスペーストラスト要件（v2.1.51以降）

`statusLine` および `fileSuggestion` フックは、インタラクティブモードでワークスペーストラストが受け入れられていない場合は実行されません。

- **`statusLine` フック**: ワークスペーストラスト受け入れ後にのみ実行
- **`fileSuggestion` フック**: ワークスペーストラスト受け入れ後にのみ実行

これはインタラクティブモードでの不正なコード実行を防ぐためのセキュリティ要件です。ワークスペーストラストが未受け入れの状態では、これらのフックはスキップされます。

### サンドボックスモードでの制限（v2.1.38以降）

サンドボックスモードで実行されるフックは、`.claude/skills`ディレクトリへの書き込みがブロックされます。

**制限される操作:**

- `.claude/skills`ディレクトリ内のファイル作成
- 既存のスキルファイルの変更
- `.claude/skills`ディレクトリ内のファイル削除

**推奨される回避策:**

- スキルの動的生成が必要な場合は、`Setup`フック（`--init`または`--init-only`フラグ）を使用して初期セットアップ時に生成する
- 実行時の設定変更は、`.claude/skills`外のディレクトリ（例: `/tmp`、プロジェクトルート等）に保存する
- スキルの内容を変更する代わりに、フック内で動的にコンテキストを提供する（`PreToolUse`フックの`additionalContext`を活用）

詳細は[skill-authoring.md](skill-authoring.md)のセキュリティ注意事項を参照してください。
