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

| コード | 意味 | 処理 |
|--------|------|------|
| `0` | 成功 | stdout処理、JSON解析 |
| `2` | ブロック | ツール実行を中止 |
| `1, 3+` | 警告 | stderrを表示、継続 |

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

## パーミッション優先順位（v2.1.27以降）

content-level（具体的パターン）の`ask`設定は、tool-level（ツール全体）の`allow`設定より優先されます。

```json
{
  "allow": ["Bash"],
  "ask": ["Bash(rm *)"]
}
```

上記の設定では:

- `Bash`ツール全体は許可（`allow`）されていますが
- `rm`コマンドは確認プロンプトが表示されます（`ask`が優先）

この仕組みにより、ツール全体を許可しつつ、危険な操作のみ個別に制限できます。フックの`PermissionRequest`イベントでは、この優先順位が適用された後の権限リクエストがトリガーされます。

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
