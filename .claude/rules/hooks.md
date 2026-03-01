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
| `UserPromptSubmit` | ユーザープロンプト送信時 | × |
| `Notification` | 通知発行時 | ✓ |
| `Stop` | Claude終了時 | × |
| `SubagentStart` | サブエージェント起動時 | ✓ |
| `SubagentStop` | サブエージェント終了時 | ✓ |
| `PreCompact` | コンパクト前 | ✓ |
| `SessionStart` | セッション開始時 | ✓ |
| `SessionEnd` | セッション終了時 | × |
| `Setup` | セットアップ・メンテナンス時 | × |
| `TeammateIdle` | チームメイトエージェントがアイドル状態時 | × |
| `TaskCompleted` | タスク完了時 | × |
| `ConfigChange` | セッション中に設定ファイルが変更された時 | ✓ |
| `WorktreeCreate` | エージェントworktree分離でworktreeが作成された時 | × |
| `WorktreeRemove` | エージェントworktree分離でworktreeが削除された時 | × |

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

### agent（エージェント起動）

特定のエージェントを起動:

```json
{
  "type": "agent",
  "agent": "code-reviewer",
  "timeout": 120
}
```

`timeout`は秒単位で指定。省略時のデフォルトは60秒。

### http（HTTPリクエスト）【v2.1.63以降】

<!-- validator-disable dangerous-operation -->

HTTPエンドポイントにJSONをPOSTし、サーバーからのJSONレスポンスを受信・処理するフックタイプ（v2.1.63以降）:

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

> **セキュリティ変更（v2.1.63・破壊的変更）**: ヘッダー値での環境変数展開（`${VAR}` 形式）には、`allowedEnvVars` フィールドへの明示的なホワイトリスト登録が必須となりました。これはHTTPフックが任意の環境変数をヘッダーに展開できたセキュリティ問題への対応です。

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
    "permissionDecision": "allow|deny|ask",
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

#### HTTPフックの制限事項（v2.1.63以降）

- **`SessionStart` および `Setup` イベントでは使用不可**: HTTPフックはこれらのイベントに対応していません
- **サンドボックスモード時のプロキシ経由ルーティング**: サンドボックスモードが有効な場合、HTTPフックはサンドボックスネットワークプロキシ経由でルーティングされ、ドメイン許可リストが適用されます

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
    "permissionDecision": "allow|deny|ask",
    "updatedInput": { "field": "new_value" },
    "additionalContext": "モデルに提供する追加コンテキスト（PreToolUseのみ）"
  }
}
```

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

## 環境変数

- `${CLAUDE_PLUGIN_ROOT}` - プラグインルートへの絶対パス
- `${CLAUDE_PROJECT_DIR}` - プロジェクトルートへの絶対パス
- `$ARGUMENTS` - フック入力JSON（prompt型で使用）

## フック入力JSON

フック実行時、stdinにJSON形式で入力が渡されます:

```json
{
  "session_id": "セッションID",
  "transcript_path": "/path/to/transcript.json",
  "cwd": "/current/working/directory",
  "permission_mode": "default",
  "hook_event_name": "PreToolUse",
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

**ユースケース:**

- タスク完了の通知・ログ記録
- 次のタスクへの自動トリガー
- 成果物の検証・レビュー
- プロジェクト進捗の追跡

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

**ユースケース:**

- worktree作成時の依存パッケージインストール
- worktree固有の設定ファイル生成
- カスタムVCSセットアップ処理
- worktree作成通知・ログ記録

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
