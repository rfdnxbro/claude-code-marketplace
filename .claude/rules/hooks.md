---
paths: plugins/*/hooks/hooks.json, .claude/hooks/hooks.json
---

# フック

JSON形式で記述します。配置場所は `hooks/hooks.json`。

## 形式

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/validate.sh"
          }
        ]
      }
    ]
  }
}
```

## 対応イベント

| イベント | 説明 |
|---------|------|
| `PreToolUse` | ツール呼び出し前 |
| `PostToolUse` | ツール呼び出し成功後 |
| `UserPromptSubmit` | ユーザープロンプト送信時 |
| `Notification` | 通知発行時 |
| `Stop` | セッション終了時 |
| `SubagentStop` | サブエージェント終了時 |

## 環境変数

- `${CLAUDE_PLUGIN_ROOT}` - プラグインルートへの絶対パス
