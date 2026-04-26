# claude-code-workflow

## 概要

Claude Code を使う際の個人的な作業スタイル（編成パターン、文体ガイド、判断ルール等）をスキルとして集約するプラグインです。

複数の小さなプラグインに分けず、1 つのプラグインに自分の Claude Code 流儀を内包する方針。デバイスを跨いで Claude Code を使う際、このプラグインを 1 つ入れるだけで一貫した作業スタイルが適用されます。

## 前提条件

- **Claude Code v2.1.64 以降**: `writing-style` スキルが補助ファイル（`style-guide.md` 等）を参照する `${CLAUDE_SKILL_DIR}` 環境変数が v2.1.64 で追加されたため
- **エージェントチーム機能**（任意）: `multi-agent-orchestration` スキルの一部機能（`TeamCreate` や `SendMessage` によるエージェントチーム間通信）を使う場合は以下を設定:

  ```bash
  export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
  ```

  この環境変数が未設定の場合、サブエージェント並列実行にフォールバックして動作します。`writing-style` スキルはこの環境変数に依存しません。

## インストール

```bash
# マーケットプレイスを追加（初回のみ）
claude plugin marketplace add rfdnxbro/claude-code-marketplace

# プラグインをユーザースコープでインストール
claude plugin install claude-code-workflow@custom-marketplace
```

## 使い方

インストール後、各スキルが対象シチュエーションで自動的に発火候補に並びます。

明示的に呼び出す場合:

```text
/multi-agent-orchestration
/writing-style
```

## 収録スキル

| スキル | 内容 |
|---|---|
| [skills/multi-agent-orchestration/SKILL.md](skills/multi-agent-orchestration/SKILL.md) | Agent tool で並列実行・エージェントチーム組成する際の編成パターン（サブエージェント vs エージェントチーム判定 / レビュアー Teammate の組み込み / 役割別モデル選択） |
| [skills/writing-style/SKILL.md](skills/writing-style/SKILL.md) | ユーザー本人の声で日本語の長文（Qiita/Zenn 記事、note、Slack、PR コメント等）を書く際の文体ガイド適用（基本トーン・句読点ルール・禁止表現・シチュエーション別温度感） |

## カスタマイズ

`writing-style` スキルは作者個人の文体・禁止表現・用語統一を定義しています。そのままインストールすると作者の文体ガイドが適用されるため、自分のスタイルに合わせる場合は以下のファイルを編集して fork して使うのを推奨します:

- `skills/writing-style/style-guide.md` — 基本トーン・タイトル型・記事構成・シチュエーション別温度感などの方針
- `skills/writing-style/glossary.md` — 表記揺れ辞書・禁止表現の対応表
- `skills/writing-style/editing-process.md` — ドキュメント編集プロセスの原則

`multi-agent-orchestration` スキルは個人の判断ルール色が強いものの、エージェントチーム編成のパターン自体は汎用的に使えます。

## 設計方針

- **1 プラグインに集約**: スキルが増えても分離せず、ここに追加する。デバイス跨ぎでのインストール手間を削減
- **発火条件は保守的に**: 取りこぼしより誤発火を避ける。明示的なシグナル（並列起動、チーム組成）でのみ発火
- **判断軸を残す**: 「このルールはなぜ存在するか」を SKILL.md 内に残し、改訂時に判断できるようにする

## ライセンス

MIT
