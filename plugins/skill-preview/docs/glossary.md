# 用語集

skill-preview の README・判断の記録（`docs/adr/`）・コードで使う言葉。

| 用語 | 意味 |
|---|---|
| 右ペイン | skill-preview が開く「スキル」ペイン。スキルの説明と `SKILL.md` を表示する |
| 入力中のプレビュー | 入力欄が `/` で始まっている間に、打った文字列で引いたスキルを右ペインに出す表示。入力欄を空にするか送信すると閉じる |
| 実行中・直前に実行 | スキルが実行されたときの右ペインの表示（「▶ 実行中」）と、そのターンが終わったあとの表示（「✓ 直前に実行」） |
| 候補リスト | 入力欄に `/` を打ったときに Claude Code（Desktop・ターミナル）が出すコマンドとスキルの一覧。ツールチップはその1行の説明 |
| 訳の対象 | 日本語訳を出すコマンドとスキル。組み込みと、Anthropic 提供のプラグインのもの |
| 組み込み | Claude Code 本体のコマンドとスキル。`$.command.list()` の `source` が `builtin`、`command.describe` の提供元が `engine` のもの |
| Anthropic 提供のプラグイン | `plugin.json` の作者が Anthropic のプラグイン。`hooks/lib.ts` の `ANTHROPIC_PLUGINS` に名前を並べる（`anthropic-skills`、`code-review`、`commit-commands`、`cowork-plugin-management`） |
| 原文 | 訳の元にした英語の説明。自前訳の各項目は `en` に原文を持ち、実行時の説明が原文と一致したときだけ訳を出す |
| 公式訳 | Claude Desktop アプリが一部の組み込みコマンド（42 件）に持つ日本語訳。リポジトリには同梱せず、実行時にアプリの内部ファイルから読む |
| 自前訳 | この mod に同梱した日本語訳（`hooks/ja-descriptions.ts`）。開発時に訳したもの。README の「訳文の文体」に従う |
| 未訳 | 訳の対象なのに訳が使えず、英語のまま表示しているもの（公式訳が無く、自前訳も無いか原文が一致しない）。右ペインに件数を出し、`/skill-preview-untranslated` で一覧にする |
