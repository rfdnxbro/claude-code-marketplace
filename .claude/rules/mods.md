---
paths:
  - plugins/*/hooks/**/*.ts
  - plugins/*/hooks/**/*.tsx
  - plugins/*/hooks/**/*.js
  - plugins/*/hooks/**/*.jsx
  - plugins/*/types/index.d.ts
---

# Mods（関数フックのプラグイン）

Mod は、JavaScript / TypeScript のイベントハンドラーで Claude Code の見た目や振る舞いを変えるプラグイン。Claude Code のプロセス内で動くため、ペインや入力欄上の帯を描く、既存 UI（ツール行・スピナー・質問ダイアログ）を差し替える、`/command` を追加する、ツール呼び出しを止める・書き換えるといったことができる。settings hook・スキル・MCP サーバーとの違いは「UI に描画できる」点。

`hooks.json` の `modules` キーとバリデーターの扱いは [hooks.md](hooks.md) の「Mods（hooks モジュール）」節を参照。このドキュメントは、hooks モジュールの書き方・API・制約をまとめる。

> API は早期アクセスで、リリースごとに変わる。**実行中のビルドの型定義（`.claude-plugin/types/claude-code/index.d.ts`）が一次情報**で、公式ドキュメントと食い違う場合は型定義を信頼する。

## ファイル構成

```text
my-mod/
├── .claude-plugin/
│   ├── plugin.json        # 通常のマニフェスト。Mod 固有の必須フィールドはない
│   └── types/             # Claude Code が自動生成（コミットしない。.gitignore も自動生成）
├── hooks/
│   ├── hooks.json         # {"modules": ["./register.tsx"]}
│   └── register.tsx       # hooks モジュール
├── types/
│   └── index.d.ts         # $.state を使う場合の型契約（plugin.json の "types" で指定）
└── tsconfig.json          # .claude-plugin/types/tsconfig.json を extends（自動追加）
```

| ファイル | 必須 | 内容 |
|---------|------|------|
| `.claude-plugin/plugin.json` | ○ | `name` / `version` / `description`。`$.state` を使うなら `"types": "./types/index.d.ts"` |
| `hooks/hooks.json` | ○ | `modules` にパスを1つ。同じファイルの `hooks` に settings hook も併記できる |
| `hooks/register.tsx` | ○ | `export const register: Register = (on, options) => { ... }`。`options` は `userConfig` の値 |
| `types/index.d.ts` | △ | `declare module 'claude-code' { interface PluginState { '<mod名>': { ... } } }` |

- ビルド不要。Node.js もバンドラーも要らず、`.js` / `.ts` / `.tsx` をそのまま読み込む
- hooks モジュールは ES module。プラグイン内のファイルは相対パスの静的 `import` で読める。動的 `import()` を含むモジュールは読み込まれない
- 型は `import type { Register } from 'claude-code'` で取る（実行時は空）。`atom` / `read` / `update` / `derive` / `memberOf` は `claude-code` から値として import する
- プラグイン名が `claude-` で始まるなど Anthropic の名前に似ていると `claude plugin validate` が失敗する

## 実行環境

hooks モジュールは独自の実行環境で動き、**DOM も Node.js API も `setTimeout` もない**（`URL` / `TextEncoder` / `AbortController` / `crypto.subtle` は使える）。外部へのアクセスはすべて `$`（Mods API）経由で行う。

| 環境 | hook の実行 | 描画 |
|------|------------|------|
| ターミナル（エディタ内ターミナル、JetBrains 含む） | ○ | ○ |
| Desktop アプリの Code タブ（WSL 以外） | ○ | ○（ターミナル専用要素を除く） |
| Desktop アプリの WSL セッション | × | × |
| VS Code 拡張のチャットパネル | ○ | ○ |
| `claude -p` / Agent SDK | ○ | × |
| Remote Control（claude.ai / モバイル） | ○（手元のセッションで実行） | 手元のターミナルのみ |

Desktop アプリで使われる Claude Code のバージョンは、Code タブのローカルセッションで `/status` の「Claude Code」行で確認できる。

## hook の基本形

```tsx
import type { Register } from 'claude-code'

export const register: Register = on => {
  on('tool.call', { tool: 'Bash' }, async ($, e, next) => {
    const ran = await next(e)   // 下位のプラグインと Claude Code 本体の処理を実行
    $.ui.status(ran.isError ? `failed: ${e.command.slice(0, 40)}` : undefined)
    return ran
  })
}
```

- `on(event, matcher?, hook)` で登録する。matcher はイベントのフィールドに対するフィルター（例: `{ component: 'Pane', requestId: 'my-pane' }`）
- hook は `($, e, next)`。`e` は deep-frozen な入力値。`next(e)` を呼ばずに返すと自分で応答し、`next({ ...e, x })` で後続に渡す値を書き換える
- 拒否系の hook（`tool.call` / `prompt.submit` / `command.run` など）は、throw やタイムアウトでスキップされると素通りになる。fail closed にするには `.catch(($, e, next) => next.called ? next(e) : { deny: '...' })` を付ける
- ストリームするイベント（`turn.step` / `process.spawn`）の hook は async generator で書く

### 静的解析の規則

Claude Code は hooks モジュールのソースを実行前に静的解析し、満たさないと読み込まない。

- `$` は `$.namespace.method(...)` の形で書く。`const ui = $.ui` のような代入・分割代入・計算プロパティは不可
- `$` をメソッド、hook 内で定義した関数、他ファイルの関数に渡さない（同じファイルのトップレベル関数には渡せる）
- `on` のイベント名は文字列リテラル。`register` の中で `on` を再宣言しない
- `$.state` のキーは `{ plugin: '<mod名>', key: '<キー>' } as const` のリテラルで書き、`types/index.d.ts` に宣言する

## 主なイベント

全イベントの入力・結果は型定義の `'tool.call'` などで grep すると引ける。

| 分類 | イベント | 用途 |
|------|---------|------|
| セッション | `session.start` | 起動時に1回。コマンド登録・タイマー開始・ペインを開く。`/clear` `/resume` `/branch` では再発火しない（`classic.SessionStart` で拾う） |
| | `session.measure` | 各ターン後、およびレート制限の使用率が1ポイント動いたとき。`$.session.usage()` と同じ値がプッシュされる |
| | `session.end` | 終了時（短い時間予算内） |
| ターン | `turn.start` / `turn.step` / `turn.complete` | ターンの開始・各モデルリクエスト・完了（`e.usage`, `e.durationMs`） |
| ツール | `tool.call` / `tool.check` / `tool.describe` | ツール呼び出しの観察・拒否・書き換え、権限判定、説明文の書き換え |
| プロンプト | `prompt.submit` | 送信時。`e.command`（`{ name, args }`）があればスラッシュコマンドの送信 |
| | `prompt.edit` | 入力欄の編集（キー入力・ペースト）ごと。hook の時間上限は 50 ms |
| | `prompt.change` | 編集以外の入力欄の変化（履歴呼び出し・クリア・プラグインの fill）。観察のみ |
| | `prompt.autocomplete` | カーソル位置の単語に対して、typeahead に候補行を追加 |
| | `prompt.compose` / `prompt.section` / `prompt.context` | システムプロンプトや初回コンテキストの組み立て |
| スキル | `skill.prompt` | スキル本文をモデル向けに展開するとき（`/name`、Skill ツール、プリロード）。`e.skill` / `e.path`（SKILL.md の絶対パス）/ `e.frontmatter` / `e.text` / `e.source` |
| コマンド | `command.run` / `command.describe` | スラッシュコマンドの実行（自前登録したコマンドへの応答）、一覧での説明 |
| 描画 | `ui.render` | 描画サイトへのツリー供給（下記） |
| | `ui.press` / `ui.input` / `ui.select` | Button / Input / Select の操作 |

> typeahead（スラッシュコマンド候補）の上下キーでの選択移動を検知するイベントはない。

## 描画（ui.render）

`on('ui.render', { component: '<サイト>' }, hook)` でツリーを返すと描画し、`next(e)` を返すと何も描かない（または本体の描画を残す）。要素は `const { Box, Text, Button } = $.ui.resolve(e)` で取り、グローバルの `h` を JSX ファクトリとして使う。

### 主な描画サイト

| サイト | 描画されるサーフェス | 説明 |
|-------|-------------------|------|
| `Pane` | Terminal / Desktop / VS Code | `$.ui.open({ id, title })` で開くペイン。`requestId` が id。ターミナルは全画面かつ十分な幅でトランスクリプト横に dock、それ以外は入力欄の上に inline |
| `AbovePrompt` | Terminal / Desktop | 入力欄のすぐ上の帯。インスタンスは1つで全 Mod 共有。`e.props.hasSurvey` が true の間はアンケートに譲る |
| `UserMessage` / `AssistantMessage` / `ToolUse` / `ToolResult` / `ToolGroup` / `AskUserQuestion` / `Spinner` | Terminal / Desktop / VS Code | 既存 UI の差し替え |
| `CommandOutput` / `SessionMode` / `PromptHint` | Terminal / Desktop | コマンド出力行、モード表示、入力欄下のヒント行 |
| `ToolProgress` / `TurnDuration` / `InfoNotice` | Terminal のみ | |

- `Pane` / `AbovePrompt` は `e.props.bodyColumns`（描ける幅）に合わせてツリーを組む
- ユーザー操作によらず Mod が自分で開いたペインは、ターミナル幅 144 列以上でのみ表示される（ユーザーが一度開いた id は 110 列）。`$.ui.open` は `{ isPlaced, reason }` を返す
- 帯の折りたたみはターミナルの全画面描画のみ（`[-]` / Ctrl+X Ctrl+A）。**Mod は帯が折りたたまれたかを知る手段がない**ため、Mod 独自の開閉が必要なら `$.state` で状態を持ち Button で切り替える

### 要素とサーフェス

| 要素 | Terminal | Desktop | VS Code |
|------|:-:|:-:|:-:|
| `Box` / `Text` / `Button` / `Link` / `Code` / `Markdown` / `Input` / `Select` | ○ | ○ | ○ |
| `Svg` | × | ○ | ○ |
| `Client`（Mod 独自のサーフェスモジュール） | ○ | ○ | × |
| `Raster` / `Image` | ○ | × | × |

- `Box` は `width`（数値または `"40%"` などの割合）と `backgroundColor` を持つため、全サーフェス共通のゲージを Box の入れ子で描ける
- サーフェスに無い要素や受け付けない prop を含むツリーは検証で落ち、その hook だけがスキップされる
- リスト内の Button には固有の `key` を付ける

### 状態と再描画

| 置き場所 | 寿命 | 用途 |
|---------|------|------|
| モジュール変数 | 次のリロードまで（リロードで `register` が再実行され初期化） | 失ってよい値 |
| `$.state` | セッション終了、または `/clear` `/resume` `/branch` まで。リロードを越えて残る | 描画が読む値。`ui.render` 内で `read($, atom)` すると購読され、書き込みで読者だけ自動再描画 |
| `$.store` | セッションをまたいで保持（合計 4 MiB の JSON、マシン上の全セッションで共有） | 次回起動にも持ち越す設定（開閉状態など） |

- `ui.render` 内では書き込まない。書き込みはハンドラー（`onPress`）や他イベントの hook から `update($, atom, fn)` で行う
- 値の形を変えたら `atom(ref, initial, { shape: '<タグ>' })` のタグを変え、古い形の値を初期値扱いにする（キーは型契約で `Shaped<T>` と宣言）
- タイマーで定期再描画するなら `session.start` で `$.clock.every(ms, ...)` を開始する。`$.ui.invalidate('ui.render')` は毎秒10回（ターミナルの表示中ペイン・展開中の帯は30回）に間引かれる

## 使用量の取得

`$.session.usage()`（呼び出しは無料）または `session.measure` イベントで、ステータスラインと同じ値が取れる。

| フィールド | 内容 |
|-----------|------|
| `context.tokens` / `context.window` / `context.percent` | 直近レスポンスの入力トークン、モデルのコンテキストウィンドウ、使用率（0〜100 の整数）。新規セッションやコンパクト直後は `tokens` / `percent` が無い |
| `rateLimits[]` | `{ kind, percentUsed, resetsAt? }`。`kind` は `five_hour` / `seven_day` / ゲートウェイの `spend_limit` などの開いた文字列。サブスクリプション以外や初回レスポンス前は空配列 |
| `cost.usd` | セッションの累計コスト（米ドル） |
| `startedAt` | セッション開始時刻（ミリ秒） |

- `{ breakdown: 'summary' | 'full' }` を渡すと `/context` と同じカテゴリ別内訳が付く（`full` はトークンカウント API を呼ぶ）
- モデル別の週次枠（例: Fable 専用の週次枠）や extra usage / クレジット残高を取る Mods API は、公式ドキュメント・型定義に記載がない。`rateLimits` の `kind` は開いた文字列なので、実行時に追加の `kind` が届く可能性はあるが、Claude Desktop の Code タブでの実機確認では `five_hour` と `seven_day` しか届かなかった

### 公式外の手段: OAuth 使用量エンドポイント

モデル別の週次枠やクレジットが必要な場合は、claude.ai の使用量画面と同じ情報を返す**非公開のエンドポイント**を mod から呼ぶ手段がある（本リポジトリの `plugins/usage-gauge/` がこの方式）。仕様は公開されておらず予告なく変わりうるため、取得に失敗しても公式の値だけで動くように作る。

```tsx
const auth = await $.session.authorize()   // 公式 API。資格情報はホスト側に残り、中身の見えないハンドルだけが返る
if (auth) {                                 // API キー・ゲートウェイ・サードパーティプロバイダーでは null
  const res = await $.http.fetch('https://api.anthropic.com/api/oauth/usage', {
    headers: { 'anthropic-beta': 'oauth-2025-04-20' },
    auth: auth.handle,                      // ファーストパーティのホストにだけ認証ヘッダーが付く
  })
}
```

- `$.session.authorize()` と `$.http.fetch` の `auth` は公式の Mods API。トークン本体は mod に渡らないため、Keychain を読む必要はない
- 実機で確認した応答のキー（非公開のため変わりうる）:
  - モデル別の週次枠: `limits[]` のうち `kind` が `"weekly_scoped"` の要素。モデル名は `scope.model.display_name`（例: `"Fable"`）、使用率は `percent`、リセット時刻は `resets_at`
  - クレジット: `spend.used` / `spend.limit`（`{ amount_minor, currency, exponent }`）、`spend.percent`、`spend.enabled`。`extra_usage` の `is_enabled` / `monthly_limit` / `used_credits` / `utilization` にも同じ系統の値がある
  - 5時間・週次の枠: `five_hour` / `seven_day` の `utilization` と `resets_at`
- 失敗時は `Retry-After` に従って間隔を空ける。呼び出し頻度は分単位にとどめる

## スキル情報の取得

- `skill.prompt`: スキル展開時に `e.path`（SKILL.md の絶対パス。組み込みスキルなどファイルが無い場合は無し）、`e.frontmatter`、`e.text`（展開後の本文）が取れる
- `$.command.list()`: スラッシュコマンド一覧（`name` / `description` / `source` / `plugin`）。ファイルパスは含まない
- 組み込みガード（`cc-plugin-sec-default`）が読み込まれるセッション（managed settings がある端末、または Team / Enterprise の `/login`）では、ユーザーの Mod の `skill.prompt` / `prompt.compose` / `prompt.section` / `prompt.context` / `classic.<Event>` などの hook は動かない

## 開発と読み込み

| 方法 | 説明 |
|------|------|
| `claude --plugin-dir <dir>` | そのセッションだけ読み込む（インストールしない）。対話セッションではフォルダを監視し、保存でホットリロード |
| `CLAUDE_CODE_PLUGIN_DIRS` | フラグを渡せない環境（Desktop アプリ等）向け。環境変数または `~/.claude/settings.json` の `env` に絶対パスをパス区切りで指定 |
| Claude に書かせる | `plugin-authoring` スキルで `~/.claude/dev-mods/<セッションID>/<mod名>/` に書かれ、初回保存時の確認で有効化。そのセッションでのみ読み込まれ、`cleanupPeriodDays` を過ぎると削除される |
| マーケットプレイス | 通常のプラグインと同じく `/plugin install <mod>@<marketplace>`。開いているセッションには `/reload-plugins` |

- ターン中に Claude が保存した変更は、ターン終了時にリロードされる
- hook の失敗やツリーの検証エラーは、ホットリロード中のセッションではトランスクリプトに薄い1行で、それ以外はデバッグログ（`claude --debug`）に出る
- 無効化: 個別は `/plugin` の Installed タブ、全体は `claude --safe-mode` または `"disableAllHooks": true`

## 検証とテスト

```bash
# マニフェストと hooks モジュールを静的解析（hooks: / calls: / state reads: などを一覧）
claude plugin validate plugins/my-mod

# 型チェック（.claude-plugin/types/ が生成された後）
tsc -p plugins/my-mod

# *.test.ts / *.test.tsx を Claude Code のエンジン上で実行（セッション・ネットワーク不要）
claude plugin test plugins/my-mod
```

- Desktop アプリは内蔵の Claude Code で動くため、PATH 上の `claude` とバージョンが違うことがある。古い `claude` で validate すると新しいイベント（例: `prompt.change`）を `is not an event` と誤って弾くので、Mod を動かす環境と同じバージョンの `claude` で検証する
- テストは `claude-code/testing` から `test` / `expect` / `mock` を import する。エンジン役の hook を `on(...)` で差し込み、`$.ui.mount({ plugin, surface, component, props })` で描画を検証する
- 描画テストは `['terminal', 'desktop'] as const` などでサーフェスをループし、特定サーフェスに依存しないことを確かめる

## 主な制限

| 項目 | 上限 |
|------|------|
| hook の実行時間 | 1イベント10秒（`next` と `$` 呼び出し中は数えない）。`prompt.edit` は 50 ms、`.catch` は 1 秒 |
| ツリー | テキスト先頭 100,000 文字、ネスト 32 階層、要素とテキスト子は合計 20,000 |
| `$.fs.read` / `$.fs.write` | 1ファイル 4 MiB（write は atomic ではない） |
| `$.process.run` | 既定 30 秒・最大 10 分 |
| `$.http.fetch` | 本文 4 MiB、1呼び出し 30 秒 |
| `$.store` | 合計 4 MiB |
| トースト | 既定 4 秒 |

- Mod はユーザー権限で動き、サンドボックスの対象外。`$.fs` / `$.process` にはパーミッションルールも PreToolUse hook も適用されない
- 組織は managed settings の `pluginConfigs` で組み込みガードに `allowManagedModsOnly: true` を渡すと、ユーザーの Mod を止められる

> 出典: 公式ドキュメント [Mods overview](https://code.claude.com/docs/en/plugins/mods/overview)、[Create a mod](https://code.claude.com/docs/en/plugins/mods/create)、[Draw in the interface with a mod](https://code.claude.com/docs/en/plugins/mods/interface)、[React to events with a mod](https://code.claude.com/docs/en/plugins/mods/events)、[Use the mods API](https://code.claude.com/docs/en/plugins/mods/api)、[Mods reference](https://code.claude.com/docs/en/plugins/mods/reference)、[Manage mods for your organization](https://code.claude.com/docs/en/plugins/mods/admin)、および Claude Code 同梱の型定義（`claude-code/index.d.ts`）
