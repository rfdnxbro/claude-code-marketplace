---
paths: plugins/*/.claude-plugin/plugin.json, .claude-plugin/plugin.json
---

# チャンネル（channels）

チャンネルは、MCPサーバーが稼働中のClaude Codeセッションにイベント（メッセージ、アラート、Webhook）を**プッシュ注入**するための仕組みです。Telegram / Discord / iMessage / fakechat などが research preview として提供されています。

## 概要

- 基本は**一方向**: MCPサーバーが `notifications/claude/channel` でイベント（メッセージ/アラート/Webhook）を送信し、Claude のコンテキストに注入される
- **双方向として拡張可能**: チャットブリッジのように使いたい場合、MCPサーバー側で reply ツールを追加公開することで Claude から返信を返せるようになる（詳細は後述の「MCPサーバー側の実装要件」参照）
- 実装は MCP サーバーとして行い、Claude Code が stdio で subprocess として spawn する

## 最低バージョンと前提条件

- Claude Code **v2.1.80 以降** が必須
- **permission relay** 機能は v2.1.81 以降
- **claude.ai ログインが必須**（Console / API key 認証では動作しない）
- Team / Enterprise では管理者による明示的な有効化が必要（デフォルトは off）

## 3つの構成要素

チャンネル機能を動かすには、**3箇所の設定**が整合している必要があります:

1. **プラグイン側**: `plugin.json` の `channels` フィールド + 対応する `mcpServers` エントリ
2. **セッション起動時**: `claude --channels plugin:<name>@<marketplace>` フラグ（必須）
3. **組織ポリシー**: Managed Settings（`channelsEnabled`, `allowedChannelPlugins`）

どれか1つでも欠けるとチャンネル配信は動作しません。

## plugin.json の channels フィールド

| フィールド | 型 | 必須 | 説明 |
|-----------|---|-----|------|
| `server` | string | Yes | プラグインの `mcpServers` 内のキーと**完全一致**する必要がある |
| `userConfig` | object | No | チャンネル単位でのユーザー設定（スキーマはトップレベル `userConfig` と同一） |

### 完全なJSON例（Telegram）

```json
{
  "name": "telegram-channel",
  "mcpServers": {
    "telegram": {
      "command": "node",
      "args": ["${CLAUDE_PLUGIN_ROOT}/server.js"]
    }
  },
  "channels": [
    {
      "server": "telegram",
      "userConfig": {
        "bot_token": {
          "description": "Telegram bot token",
          "sensitive": true
        },
        "owner_id": {
          "description": "Your Telegram user ID",
          "sensitive": false
        }
      }
    }
  ]
}
```

per-channel の `userConfig` とトップレベルの `userConfig` はスキーマが同じですが、宣言場所が異なります。チャンネル単位で別々の認証情報を持たせたい場合に使用します。

## ユーザー体験（セッション起動フロー）

```bash
# 1. インストール
/plugin install telegram-channel@my-marketplace

# 2. 起動時にチャンネルを明示的に有効化（複数指定はスペース区切り）
claude --channels plugin:telegram-channel@my-marketplace

# 3. 開発中の未承認チャンネルを読み込む場合
claude --dangerously-load-development-channels plugin:telegram-channel@my-marketplace
# あるいはサーバー名指定
claude --dangerously-load-development-channels server:telegram
```

**重要**: `.mcp.json` への登録だけではチャンネルからのプッシュは有効化されません。必ず `--channels` での明示指定が必要です。

## MCPサーバー側の実装要件

プラグインが提供する MCP サーバーがチャンネルとして振る舞うには、以下を実装します:

### 必須: capability 宣言

```javascript
server.setCapabilities({
  experimental: {
    "claude/channel": {}
  }
});
```

この宣言がチャンネル側リスナー登録のトリガーになります。

### イベント送信

- 通知メソッド: `notifications/claude/channel`
- パラメータ:
  - `content` (string): Claude コンテキストに注入されるメッセージ本文
  - `meta` (Record<string, string>): ソース属性など。**キーは `[a-zA-Z0-9_]` のみ**有効。ハイフンを含むキーは **silent drop** される
- Claude コンテキストへの注入形式:

```text
<channel source="..." attr="...">body</channel>
```

### 双方向（reply 対応）

以下を追加で実装:

- `capabilities.tools = {}` を宣言
- `ListToolsRequestSchema` / `CallToolRequestSchema` のハンドラを追加し、reply ツールを公開

### permission relay（v2.1.81以降、オプトイン）

Claude 側の tool 実行承認プロンプトをチャンネル経由で中継する場合:

- `capabilities.experimental["claude/channel/permission"] = {}` を宣言
- `notifications/claude/channel/permission_request` を受信するハンドラを実装
- `request_id`（5文字、`l` を除く小文字）をエコーしつつ `notifications/claude/channel/permission` で `{ behavior: "allow" | "deny" }` を返信

## Managed Settings（組織管理）

### channelsEnabled（Managed only）

チャンネル配信のマスタースイッチ。**Managed settings 経由でのみ設定可能**。

- `true`: チャンネル配信を許可
- 未設定 / `false`: `--channels` 指定があってもチャンネル配信をブロック
- Team / Enterprise プランのデフォルトは未設定

### allowedChannelPlugins（Managed only）

組織が許可するチャンネルプラグインの allowlist。Anthropic デフォルトの allowlist を**置換**します。

- `channelsEnabled: true` が前提
- 未定義 = Anthropic デフォルト allowlist が適用
- `[]`（空配列）= すべてのチャンネルプラグインをブロック
  - ただし `--dangerously-load-development-channels` は bypass できる
- 各エントリ: `{ marketplace: string, plugin: string }`

**注意**: `allowedChannelPlugins` の**導入バージョンは公式ドキュメントに明示されていません**（チャンネル機能自体は v2.1.80 以降）。

### JSON例

```json
{
  "channelsEnabled": true,
  "allowedChannelPlugins": [
    { "marketplace": "claude-plugins-official", "plugin": "telegram" },
    { "marketplace": "claude-plugins-official", "plugin": "discord" },
    { "marketplace": "acme-corp-plugins", "plugin": "internal-alerts" }
  ]
}
```

**注意**: macOS plist キー名・Windows Registry のパス/値名などの**プラットフォーム固有の書式例は公式ドキュメントに明示されていません**。一般的な managed settings 機構（[`/en/settings#settings-files`](https://code.claude.com/docs/en/settings#settings-files)）に従って設定してください。

## セキュリティ考慮事項

- **sender allowlist が必須**。Pairing（Telegram/Discord）または handle 登録（iMessage）で送信元を追加する設計にすること
- **ゲートは sender ID（`message.from.id`）で行う**。room / chat ID ではグループチャット内の他人が注入可能になるため危険
- `.mcp.json` 単独登録ではチャンネル push は有効化されない（`--channels` 明示指定が必須）
- permission relay を宣言するチャンネルは**認証が必須**。allowlist に載っている人物は tool 実行の承認権限を持つ点に注意
- bot token 等の機密値は `userConfig` の `sensitive: true` 経由で保存し、コマンドラインや平文ファイルに書かない

## プラン別扱い

| プラン | デフォルト | 有効化方法 |
|--------|----------|-----------|
| Pro / Max（個人） | 利用可能 | `--channels` フラグでオプトイン |
| Team / Enterprise | off | claude.ai Admin console または managed `channelsEnabled: true` で有効化 |

## 公式ドキュメントで明示されていない項目

以下は本ドキュメント作成時点の公式ドキュメントに記載が見当たらず、本ドキュメントでも保証しません:

- `allowedChannelPlugins` の導入バージョン
- macOS plist / Windows Registry における具体的なキー名・パス・値フォーマット
- `plugin.json` の `channels` と `--channels` / `allowedChannelPlugins` の整合性チェック（不整合時の挙動、エラー表示）の詳細

## 出典

- [Channels overview](https://code.claude.com/docs/en/channels)
- [Channels reference](https://code.claude.com/docs/en/channels-reference)
- [Plugins reference: Channels](https://code.claude.com/docs/en/plugins-reference#channels)
- [Settings: channelsEnabled / allowedChannelPlugins](https://code.claude.com/docs/en/settings)
- [MCP: Push messages with channels](https://code.claude.com/docs/en/mcp)
