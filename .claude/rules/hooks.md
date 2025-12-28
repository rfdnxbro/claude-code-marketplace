---
paths: plugins/*/hooks/hooks.json
---

# フック

JSON形式で記述します。配置場所は `hooks/hooks.json`。

## 形式

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash|Edit|Write",
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

## フックタイプ

### command（Bashコマンド）

```json
{
  "type": "command",
  "command": "${CLAUDE_PLUGIN_ROOT}/scripts/check.sh",
  "timeout": 60
}
```

### prompt（LLM評価）

```json
{
  "type": "prompt",
  "prompt": "タスク完了を評価: $ARGUMENTS",
  "timeout": 30
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
    "updatedInput": { "field": "new_value" }
  }
}
```

## 環境変数

- `${CLAUDE_PLUGIN_ROOT}` - プラグインルートへの絶対パス
- `${CLAUDE_PROJECT_DIR}` - プロジェクトルートへの絶対パス
- `$ARGUMENTS` - フック入力JSON（prompt型で使用）

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
