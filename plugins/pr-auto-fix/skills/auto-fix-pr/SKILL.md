---
name: auto-fix-pr
description: pr-auto-fix プラグインの監視ループを起動するトリガースキル。Hook で PR 作成が検知された後、Claude が `pr-auto-fix:auto-fix-pr` として呼び出すと Monitor (`pr-auto-fix-watcher`) がバックグラウンドで起動する。Monitor からの通知を受けて pr-auto-fixer エージェントへディスパッチする責務を持つ。
---

# auto-fix-pr

このスキルは pr-auto-fix プラグインの **Monitor 起動トリガー** です。スキルが invoke されると、`monitors/monitors.json` の `when: "on-skill-invoke:auto-fix-pr"` に従って Monitor (`pr-auto-fix-watcher`) が起動し、`watch-targets.json` に登録された PR を継続監視します。

## 役割

1. Monitor を起動し、PR の CI / レビュー / コンフリクトの監視を開始する
2. Monitor が stdout に流す通知（JSON Lines）を受け取り、`kind` で分岐する
3. 修正が必要な通知は `pr-auto-fixer` エージェントへディスパッチする
4. `escalation` 通知はユーザーに `AskUserQuestion` で対応方針を尋ねる

## 通知の取り扱い

Monitor の通知 JSON は次の形式です：

```json
{"plugin":"pr-auto-fix","kind":"<event-kind>","pr":"<url>","signature":"<sig>", ...}
```

`kind` ごとの動作：

| kind | 動作 |
|------|------|
| `ci_failure` | Agent ツールで `pr-auto-fixer` を起動し、通知 JSON を渡して修正を依頼する |
| `review` | Agent ツールで `pr-auto-fixer` を起動し、コメント本文を読ませて自明性判定→修正 or escalation |
| `conflict` | Agent ツールで `pr-auto-fixer` を起動し、rebase 可能か判定→解決 or escalation |
| `escalation` | エージェント側からの「人間に確認してほしい」通知。`reason` と `details` をユーザーに伝え、`AskUserQuestion` で対応方針を確認する |
| `closed` | PR がマージ/クローズされ Monitor 側で監視解除済み。何もしない（既読扱い） |
| `auth_error` | gh CLI 未認証/接続エラー。ユーザーに `gh auth status` 確認を促す |

## エージェント起動の流儀

通知 JSON を一切加工せず、そのまま prompt に渡してエージェントへ委譲します。エージェント側で前提ガード（現ブランチ確認・dirty worktree 判定・試行回数チェック）を行います。

```text
Agent({
  description: "PR auto-fix dispatch",
  subagent_type: "pr-auto-fixer",
  prompt: "<通知 JSON 全文>"
})
```

## 自分で修正を試みない

メインセッションで直接 `Edit` や `git commit` を実行しないでください。エージェントを経由しないと現ブランチ確認や dirty worktree 検出のガードが働かず、ユーザーの作業を破壊する恐れがあります。

## escalation の扱い例

`{"plugin":"pr-auto-fix","kind":"escalation","pr":"...","reason":"judgment_required","signature":"...","details":"..."}` を受け取ったら：

1. `reason` を見てユーザーに状況を要約
2. `AskUserQuestion` で「修正案を提示」「手動対応する」「無視」などの方針を確認
3. 「修正案を提示」が選ばれたら別途 `pr-auto-fixer` を起動し直す（`AUTO_FIX_PR_OVERRIDE=1` 等のヒントを含めて）

## メモ

- `${CLAUDE_PLUGIN_DATA}` 配下の状態ファイル（`watch-targets.json` / `seen.json` / `attempts.json` / `escalations.json`）は Hook と Monitor とエージェントが共有する。スキル内で直接書き換える必要はない
- Monitor のライフタイムはセッション終了まで。再起動は新しいセッションでスキルを invoke することで行う
