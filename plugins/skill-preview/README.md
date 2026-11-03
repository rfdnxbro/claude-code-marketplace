# skill-preview

## 概要

入力欄に `/スキル名` を打っている間や、スキルが実行されたときに、そのスキルの `SKILL.md`（frontmatter と本文）を右ペインに表示する mod です。

- **入力中のプレビュー**: 入力欄が `/` で始まると、先頭のトークン（`/` の後ろから空白まで）でスキルを引きます。完全一致を優先し、なければ前方一致で探します。`plugin:skill` 形式のスキルはコロンの後ろの名前でも一致します。候補が複数あるときは上位 6 件をボタンで並べ、押すとそのスキルに切り替わります
- **実行時の表示**: `/name`、Skill ツール、サブエージェントへのプリロードでスキルが実行されると、そのスキルを「▶ 実行中」として表示します。ターンが終わると「✓ 直前に実行」に変わります
- **表示内容**: スキル名、出どころ（`user` / `project` / `plugin: <名前>` / `builtin` など）、ファイルパス、frontmatter の各フィールド（`description`、`allowed-tools`、`model` など）、本文（Markdown）
- 入力欄が `/` で始まらなくなっても、直前の表示を残します
- ファイルが見つからないスキル（組み込みコマンドなど）は、コマンド一覧の説明文だけを表示します

mod は Claude Code のプロセス内で動く関数フックのプラグインです。仕組みは公式ドキュメント [Mods overview](https://code.claude.com/docs/en/plugins/mods/overview) を参照してください。

## 前提条件

- **Claude Code v2.1.309 以降**（mod の API は早期アクセスのため、バージョンによって動かない場合があります）
- ターミナル、Claude Desktop の Code タブ、VS Code 拡張で表示されます。`claude -p` や Desktop の WSL セッションでは表示されません
- 組み込みガードが読み込まれるセッション（managed settings がある端末、Team / Enterprise のログイン）では、ユーザーの mod の `skill.prompt` フックが動かないため、実行時の表示は出ません

## インストール

```bash
# マーケットプレイスを追加（初回のみ）
claude plugin marketplace add rfdnxbro/claude-code-marketplace

# プラグインをユーザースコープでインストール
claude plugin install skill-preview@custom-marketplace
```

開いているセッションには `/reload-plugins` で読み込みます。

## 使い方

入力欄に `/` に続けてスキル名を打つと、最初に一致したときに「スキル」ペインが開き、一致したスキルの `SKILL.md` が表示されます。

```text
/gri
```

ペインを閉じたあとで開き直すときや、特定のスキルを表示したいときはコマンドを使います。

```text
/skill-preview
/skill-preview grilling
```

ターミナルでは、mod が自分で開くペインは幅 144 列以上のときだけ表示されます。狭いときは `/skill-preview` で開いてください。

## スキルの探し方

セッション開始時に、次の場所からスキル名と `SKILL.md` のパスの対応表を作ります（ファイルの中身は表示するときに読みます）。

| 出どころ | 場所 | 名前 |
|---|---|---|
| project | `<作業ディレクトリ>/.claude/skills/<name>/SKILL.md`、`<作業ディレクトリ>/.claude/commands/**/*.md` | `<name>`（サブディレクトリは `dir:name`） |
| user | `~/.claude/skills/<name>/SKILL.md`、`~/.claude/commands/**/*.md` | 同上 |
| plugin | `~/.claude/plugins/installed_plugins.json` の各プラグインの `installPath` 配下の `skills/*/SKILL.md` と `commands/*.md` | `<plugin>:<name>` |
| synced | `~/.claude/skills/synced/*/<name>/SKILL.md`（アカウントから同期されたスキル） | コロンの後ろの名前で引く |

`CLAUDE_CONFIG_DIR` が設定されていれば `~/.claude` の代わりにそこを見ます。

この表に無いスキル（`--plugin-dir` で読み込んだプラグインのものなど）も、一度実行されれば `skill.prompt` で分かったパスを覚え（`$.store` に保存）、次回以降の入力中プレビューに使います。

## 制限

- typeahead（スラッシュコマンドの候補一覧）の上下キーでの選択移動を検知するイベントが無いため、プレビューは入力した文字列だけで決まります
- プラグインの `plugin.json` でスキルの置き場所を変えている場合や、frontmatter の `name` でスキル名を変えている場合は、一度実行するまでファイルを見つけられません
- frontmatter は表示用に簡易に読んでいるため、入れ子の深い YAML は 1 行にまとめて表示します

## 開発

```bash
# 静的解析（Mod を動かす環境と同じバージョンの claude で実行する）
claude plugin validate plugins/skill-preview

# テスト（hooks/register.test.tsx）
claude plugin test plugins/skill-preview
```

## ライセンス

MIT
