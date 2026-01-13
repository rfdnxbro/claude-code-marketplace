---
paths: .claude/settings.local.json
---

# ステータスライン

ステータスラインはClaude Codeのターミナルに表示される情報バーをカスタマイズする機能です。

## 設定方法

`.claude/settings.local.json` で設定します:

```json
{
  "statusLine": {
    "template": "{{model}} | {{context_window.used}}/{{context_window.max}} ({{context_window.used_percentage}}%)"
  }
}
```

## 利用可能なフィールド

ステータスライン表示用に以下のフィールドが利用可能です:

### モデル情報

| フィールド | 説明 | 例 |
|-----------|------|-----|
| `model` | 現在使用中のモデル名 | `claude-sonnet-4-5` |

### コンテキストウィンドウ情報

| フィールド | 説明 | 例 |
|-----------|------|-----|
| `context_window.used` | 使用中のトークン数 | `15000` |
| `context_window.max` | 最大トークン数 | `200000` |
| `context_window.remaining` | 残りトークン数 | `185000` |
| `context_window.used_percentage` | 使用率（%） | `7.5` |
| `context_window.remaining_percentage` | 残り率（%） | `92.5` |

### バージョン2.1.6で追加されたフィールド

- `context_window.used_percentage`: コンテキストウィンドウの使用率をパーセンテージで表示
- `context_window.remaining_percentage`: コンテキストウィンドウの残り率をパーセンテージで表示

これらのフィールドにより、数値計算なしで直接パーセンテージを表示できます。

## テンプレート構文

テンプレートは `{{field}}` 形式でフィールドを参照します。ネストされたフィールドはドット記法で参照します（例: `{{context_window.used_percentage}}`）。

### 例1: シンプルな使用率表示

```json
{
  "statusLine": {
    "template": "Context: {{context_window.used_percentage}}% used"
  }
}
```

出力例: `Context: 7.5% used`

### 例2: 使用量と残量の両方を表示

```json
{
  "statusLine": {
    "template": "{{model}} | Used: {{context_window.used_percentage}}% | Remaining: {{context_window.remaining_percentage}}%"
  }
}
```

出力例: `claude-sonnet-4-5 | Used: 7.5% | Remaining: 92.5%`

### 例3: 詳細な情報表示

```json
{
  "statusLine": {
    "template": "{{model}} | {{context_window.used}}/{{context_window.max}} tokens ({{context_window.used_percentage}}%)"
  }
}
```

出力例: `claude-sonnet-4-5 | 15000/200000 tokens (7.5%)`

## プラグインでの活用

プラグインでステータスライン設定を提供する場合、ドキュメントやセットアップスクリプトでユーザーに設定例を提示できます。

```markdown
## ステータスライン設定

`.claude/settings.local.json` に以下を追加することで、使いやすいステータスラインを設定できます:

\`\`\`json
{
  "statusLine": {
    "template": "{{model}} | {{context_window.used_percentage}}% used"
  }
}
\`\`\`
```

## 注意事項

- `.claude/settings.local.json` はユーザー固有の設定ファイルです
- プラグインが直接このファイルを変更するのは避け、ユーザーに設定例を提示する形が推奨されます
- フィールド名は大文字小文字を区別します
- 存在しないフィールドを参照した場合、そのまま `{{field}}` として表示されます
