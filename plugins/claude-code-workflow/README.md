# claude-code-workflow

## 概要

Claude Code を使う際の個人的な作業スタイル（編成パターン、文体ガイド、判断ルール等）をスキルとして集約するプラグインです。

複数の小さなプラグインに分けず、1 つのプラグインに自分の Claude Code 流儀を内包する方針。デバイスを跨いで Claude Code を使う際、このプラグインを 1 つ入れるだけで一貫した作業スタイルが適用されます。

## 前提条件

`multi-agent-orchestration` スキルの一部機能（`TeamCreate` や `SendMessage` によるエージェントチーム間通信）は、実験的なエージェントチーム機能を必要とします:

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

## 設計方針

- **1 プラグインに集約**: スキルが増えても分離せず、ここに追加する。デバイス跨ぎでのインストール手間を削減
- **発火条件は保守的に**: 取りこぼしより誤発火を避ける。明示的なシグナル（並列起動、チーム組成）でのみ発火
- **判断軸を残す**: 「このルールはなぜ存在するか」を SKILL.md 内に残し、改訂時に判断できるようにする

## ライセンス

MIT
