# claude-code-workflow

## 概要

Claude Code を使う際の個人的な作業スタイル（編成パターン、判断ルール等）をスキルとして集約するプラグインです。

複数の小さなプラグインに分けず、1 つのプラグインに自分の Claude Code 流儀を内包する方針。デバイスを跨いで Claude Code を使う際、このプラグインを 1 つ入れるだけで一貫した作業スタイルが適用されます。

## インストール

```bash
# マーケットプレイスを追加（初回のみ）
claude plugin marketplace add rfdnxbro/claude-code-marketplace

# プラグインをユーザースコープでインストール
claude plugin install claude-code-workflow@custom-marketplace
```

## 使い方

インストール後、Agent tool で複数のサブエージェントを並列起動する／エージェントチームを組成する場面で `multi-agent-orchestration` スキルが自動で発火候補に並びます。

明示的に呼び出す場合:

```text
/multi-agent-orchestration
```

## 収録スキル

| スキル | 内容 |
|---|---|
| [skills/multi-agent-orchestration/SKILL.md](skills/multi-agent-orchestration/SKILL.md) | Agent tool で並列実行・エージェントチーム組成する際の編成パターン（サブエージェント vs エージェントチーム判定 / レビュアー Teammate の組み込み / 役割別モデル選択） |

## 設計方針

- **1 プラグインに集約**: スキルが増えても分離せず、ここに追加する。デバイス跨ぎでのインストール手間を削減
- **発火条件は保守的に**: 取りこぼしより誤発火を避ける。明示的なシグナル（並列起動、チーム組成）でのみ発火
- **判断軸を残す**: 「このルールはなぜ存在するか」を SKILL.md 内に残し、改訂時に判断できるようにする

## ライセンス

MIT
