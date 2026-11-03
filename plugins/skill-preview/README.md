# skill-preview

## 概要

入力欄に `/スキル名` を打っている間や、スキルが実行されたときに、そのスキルの `SKILL.md`（frontmatter と本文）を右ペインに表示する mod です。

- **入力中のプレビュー**: 入力欄が `/` で始まると、先頭のトークン（`/` の後ろから空白まで）でスキルを引きます。完全一致を優先し、なければ前方一致で探します。`plugin:skill` 形式のスキルはコロンの後ろの名前でも一致します。候補が複数あるときは上位 6 件をボタンで並べ、押すとそのスキルに切り替わります
- **実行時の表示**: `/name`、Skill ツール、サブエージェントへのプリロードでスキルが実行されると、そのスキルを「▶ 実行中」として表示します。ターンが終わると「✓ 直前に実行」に変わります。実行中・直前に実行の表示中に `/` で別のスキル名を打つと、一致したときだけそちらのプレビューに切り替わり、一致しないときは元の表示を残します
- **表示内容**: スキル名、出どころ（`user` / `project` / `plugin: <名前>` / `builtin` など）、ファイルパス、frontmatter の各フィールド（`description`、`allowed-tools`、`model` など）、本文（Markdown）
- 入力欄を空にする（または `/` で始まらない文に書き換える）と、入力中のプレビューのペインを閉じます。送信した直後にスキルが実行された場合は閉じずに「▶ 実行中」に切り替え、実行中・直前に実行の表示は入力欄が空でも残します。入力中のプレビューを手で閉じたときは、入力欄を空にするまで開き直しません
- ファイルが見つからないスキル（組み込みコマンドなど）は、コマンド一覧の説明文だけを表示します
- **説明の日本語訳**: 組み込み・Anthropic 提供のスキルとコマンドの英語の説明を、同梱の日本語訳に置き換えて表示します（[説明の日本語訳](#説明の日本語訳)）

mod は Claude Code のプロセス内で動く関数フックのプラグインです。仕組みは公式ドキュメント [Mods overview](https://code.claude.com/docs/en/plugins/mods/overview) を参照してください。

## 前提条件

- **Claude Code v2.1.309 以降**（mod の API は早期アクセスのため、バージョンによって動かない場合があります）
- ターミナル、Claude Desktop の Code タブ、VS Code 拡張で表示されます。`claude -p` や Desktop の WSL セッションでは表示されません
- 組み込みガードが読み込まれるセッション（managed settings がある端末、Team / Enterprise のログイン）では、ユーザーの mod の `skill.prompt` フックが動かないため、実行時の表示は出ません

## インストール

> **Note**: このプラグインは `.claude-plugin/marketplace.json` への登録が済むまで、以下の手順ではインストールできません。それまでは「開発」の手順で読み込んでください。

```bash
# マーケットプレイスを追加（初回のみ）
claude plugin marketplace add rfdnxbro/claude-code-marketplace

# プラグインをユーザースコープでインストール
claude plugin install skill-preview@custom-marketplace
```

開いているセッションには `/reload-plugins` で読み込みます。

## 使い方

入力欄に `/` に続けてスキル名を打つと、一致したときに「スキル」ペインが開き、一致したスキルの `SKILL.md` が表示されます。入力欄を空にするとペインは閉じます。

```text
/gri
```

ペインを閉じたあとで開き直すときや、特定のスキルを表示したいときはコマンドを使います。

```text
/skill-preview
/skill-preview grilling
```

組み込み・Anthropic 提供の説明のうち、日本語訳が無く英語のままのものは次のコマンドで一覧できます（[未訳の確認](#未訳の確認)）。

```text
/skill-preview-untranslated
```

ターミナルでは、mod が自分で開くペインは幅 144 列以上のときだけ表示されます。狭いときは `/skill-preview` で開いてください。

## スキルの探し方

セッション開始時に、次の場所からスキル名と `SKILL.md` のパスの対応表を作ります（ファイルの中身は表示するときに読みます）。

| 出どころ | 場所 | 名前 |
|---|---|---|
| project | 作業ディレクトリと、その親をたどった各ディレクトリ（ホームを除く）の `.claude/skills/**/SKILL.md`、`.claude/commands/**/*.md`。作業ディレクトリに近いものが優先 | スキルは `<name>`（ネストしたものは `category:name` でも引く）、コマンドは `<name>`（サブディレクトリは `dir:name`） |
| user | `~/.claude/skills/**/SKILL.md`（`synced` を除く）、`~/.claude/commands/**/*.md` | 同上 |
| plugin | `~/.claude/plugins/installed_plugins.json` の各プラグインの `installPath` 配下の `skills/**/SKILL.md` と `commands/**/*.md` | `<plugin>:<name>` |
| synced | `~/.claude/skills/synced/*/<name>/SKILL.md`（アカウントから同期されたスキル） | コロンの後ろの名前で引く |

`CLAUDE_CONFIG_DIR` が設定されていれば `~/.claude` の代わりにそこを見ます。スキルは `skills/` の下を 3 階層まで探し、`node_modules` には入りません。

この表に無いスキル（`--plugin-dir` で読み込んだプラグインのものなど）も、一度実行されれば `skill.prompt` で分かったパスを作業ディレクトリごとに覚え（`$.store` に保存）、次回以降の入力中プレビューに使います。表で見つかるスキルは、覚えたパスより表を優先します。

## 説明の日本語訳

組み込み・Anthropic 提供のスキルとコマンドの説明（description）を、同梱の日本語訳（`hooks/ja-descriptions.ts`）で表示します。訳は開発時に用意したもので、実行時に翻訳はしません。SKILL.md の本文は訳しません。

| 表示先 | 置き換えるもの |
|---|---|
| 入力欄の候補リスト・`/help` | `command.describe` で返す説明 |
| 右ペイン | コマンド一覧の説明、SKILL.md の frontmatter の `description`、実行時に届く frontmatter の `description` |

### 訳す対象

- **組み込み**: Claude Code 本体のスラッシュコマンドとスキル（`$.command.list()` の `source` が `builtin`、`command.describe` の提供元が `engine` のもの）
- **Anthropic 提供のプラグイン**: プラグインの `plugin.json` の `author` が Anthropic のもの。現在は次の 4 つです

| プラグイン | 配布元 |
|---|---|
| `anthropic-skills` | claude.ai のアカウントから同期されるスキル |
| `code-review`、`commit-commands` | 公式マーケットプレイス `claude-plugins-official` |
| `cowork-plugin-management` | Claude Desktop が配る `knowledge-work-plugins` |

次のものは訳しません。

- ユーザーやプロジェクトが書いたスキル・コマンド（組み込みと同じ名前でも訳しません）
- コミュニティや他社のプラグイン（`eli5`、公式マーケットプレイスや Desktop 経由でも作者が Anthropic でない `1password` など）
- MCP サーバーのコマンド
- もともと日本語の説明（`anthropic-skills` にユーザーがアップロードしたスキルなど）

### 原文が変わったとき

各訳には訳の元にした英語の原文を持たせています。実行時の説明がその原文と一致しないとき（Claude Code やプラグインの更新で説明が変わったとき）は、古い訳を出さずに英語の説明をそのまま表示します。改行や連続する空白の違いは無視して比べます。モデル名のように実行時に変わる部分は、原文と訳の `{}` で表し、原文の該当部分を訳にそのまま入れます（例: `Set the AI model for Claude Code (currently {})`）。

### 未訳の確認

訳の対象なのに訳が使えないもの（同梱の訳が無い、または英語の原文が同梱時と一致しないため英語のまま表示しているもの）を「未訳」として数えます。未訳があるときは、右ペインに「未訳 N 件」と控えめに表示します（0 件なら出しません）。説明が空のものと、もともと日本語のものは数えません。

```text
/skill-preview-untranslated
```

未訳の一覧（`name` / `source` / `plugin` / 現在の英語の `description`）と、訳文ファイルの更新の頼み方を出力し、クリップボードにもコピーします。

### 訳文の更新手順

Claude Code やプラグインの更新で説明が変わったり、コマンドが増えたりして未訳が出たら、次の手順で訳を足して配ります。実行時に自動で翻訳はしません。

1. `/skill-preview-untranslated` を実行し、出力（クリップボードにも入っています）をこのリポジトリで作業する Claude に渡して、`hooks/ja-descriptions.ts` の `JA_DESCRIPTIONS` の更新を頼みます。`en` には出力の `description` をそのまま写します（手で打ち直すと一致しなくなります）。訳のトーンは簡潔な説明文（「〜する。」調）で、固有名詞・コマンド名・ツール名・ファイル名は原文のままにします
2. `claude plugin test plugins/skill-preview` を実行します（原文と訳の `{}` の数がそろっているかもテストします）
3. `.claude-plugin/plugin.json` の `version` を上げて配ります

Anthropic 提供のプラグインが増えたときは、`hooks/lib.ts` の `ANTHROPIC_PLUGINS` に名前を足すと、そのプラグインも未訳として数えるようになります。

## 制限

- typeahead（スラッシュコマンドの候補一覧）の上下キーでの選択移動を検知するイベントが無いため、プレビューは入力した文字列だけで決まります
- プラグインの `plugin.json` でスキルの置き場所を変えている場合や、frontmatter の `name` でスキル名を変えている場合は、一度実行するまでファイルを見つけられません
- frontmatter は表示用に簡易に読んでいるため、入れ子の深い YAML は 1 行にまとめて表示します
- 説明の日本語訳は、訳を用意した時点の Claude Code とプラグインの説明に合わせています。新しく増えたコマンドや説明が変わったコマンドは、訳を更新するまで英語のまま表示します（[未訳の確認](#未訳の確認)）
- `command.describe` で書き換えた説明は、候補リストだけでなく、Claude がスキルを選ぶときに読むスキル一覧の説明にも使われます。この mod を入れると、組み込み・Anthropic 提供のスキルの説明は Claude にも日本語訳で渡ります

## 開発

```bash
# 静的解析（Mod を動かす環境と同じバージョンの claude で実行する）
claude plugin validate plugins/skill-preview

# テスト（hooks/register.test.tsx。説明の日本語訳のテストも含む）
claude plugin test plugins/skill-preview

# 開発中のセッションに読み込む
claude --plugin-dir plugins/skill-preview
```

`.claude-plugin/types/`（`claude-code` の型定義と、この mod の `tsconfig.json` が継承する設定）は、Claude Code がこの mod を読み込んだときに生成します。生成するコマンドは無く、`git` の管理対象外です（`.gitignore` で除外）。一度読み込んだあとは `tsc -p plugins/skill-preview` で型チェックできます。

## ライセンス

MIT
