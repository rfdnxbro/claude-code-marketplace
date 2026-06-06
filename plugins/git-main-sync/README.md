# git-main-sync

## 概要

新規セッション開始時(`SessionStart` の `startup` / `resume`)に、git 管理下のリポジトリなら `main` ブランチを自動で最新化する hook プラグイン。

現在ブランチに応じて挙動を切り替える:

- 現在ブランチが既定ブランチ(`origin/HEAD`)と一致 → `git pull --ff-only origin <default>`
- それ以外 → `git fetch origin`(ローカル既定ブランチは触らない)

git 管理下でない / `origin` リモートが無い場合は静かに終了する。pull/fetch に失敗してもセッション開始はブロックしない(`exit 0`)。

## インストール

このマーケットプレイス([rfdnxbro/claude-code-marketplace](https://github.com/rfdnxbro/claude-code-marketplace))を追加した上で:

```bash
/plugin install git-main-sync@custom-marketplace
```

## 使い方

インストール後、Claude Code の新規セッション起動・再開のたびに自動で実行される。手動操作は不要。

結果はステータスメッセージとして 1 行通知される:

```text
[git-main-sync] main を pull で最新化しました
[git-main-sync] main は既に最新です
[git-main-sync] origin を fetch しました (現在ブランチ: feat/foo)
```

### 挙動の詳細

| 状況 | 動作 |
|------|------|
| git 管理下でない | 何もしない |
| `origin` リモートが未設定 | 何もしない |
| 現在ブランチ = 既定ブランチ | `git pull --ff-only origin <default>` |
| 現在ブランチ ≠ 既定ブランチ | `git fetch origin` のみ(ローカル既定ブランチは触らない) |
| pull / fetch がネットワークやコンフリクトで失敗 | 通知して `exit 0` で続行 |

既定ブランチは `git symbolic-ref refs/remotes/origin/HEAD` から検出する。取得できない場合は `main` にフォールバック。

### タイムアウト

hook 全体のタイムアウトは 30 秒。低速なネットワークで遅延する場合は [`hooks/hooks.json`](hooks/hooks.json) の `timeout` を調整する。

## ライセンス

MIT
