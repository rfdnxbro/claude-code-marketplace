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
| `PermissionRequest` | 権限ダイアログ表示時 | ✓ |
| `UserPromptSubmit` | ユーザープロンプト送信時 | × |
| `Notification` | 通知発行時 | ✓ |
| `Stop` | Claude終了時 | × |
| `SubagentStop` | サブエージェント終了時 | × |
| `PreCompact` | コンパクト前 | ✓ |
| `SessionStart` | セッション開始時 | ✓ |
| `SessionEnd` | セッション終了時 | × |
| `Setup` | セットアップ・メンテナンス時 | × |
| `TeammateIdle` | チームメイトエージェントがアイドル状態時 | × |
| `TaskCompleted` | タスク完了時 | × |

## フックタイプ

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

### prompt（LLM評価）

LLMを使用してプロンプトを評価:

```json
{
  "type": "prompt",
  "prompt": "タスク完了を評価: $ARGUMENTS",
  "timeout": 30
}
```

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
| `2` | ブロック | ツール実行を中止、stderrをユーザーに表示（v2.1.41以降） |
| `1, 3+` | 警告 | stderrを表示し、処理を継続 |

**v2.1.41での変更**: exit code 2でブロックされた場合、stderrの内容がユーザーに表示されるようになりました。これにより、フックがツール実行をブロックした理由をユーザーに伝えることができます。

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

### ブロック時のメッセージ（v2.1.41以降）

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
  "tool_name": "Edit",
  "tool_input": { "file_path": "/path/to/file", "old_string": "...", "new_string": "..." },
  "tool_use_id": "toolu_abc123"
}
```

| フィールド | 説明 |
|-----------|------|
| `tool_name` | 実行されるツール名 |
| `tool_input` | ツールへの入力パラメータ |
| `tool_use_id` | ツール呼び出しの一意識別子（トラッキング用） |

## イベント詳細

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
