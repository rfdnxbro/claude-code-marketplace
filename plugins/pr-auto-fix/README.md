# pr-auto-fix

## 概要

`gh pr create` で PR を作成した直後から、PR の **CI 失敗 / レビューコメント / main からのコンフリクト** をバックグラウンドで自動監視し、自明な範囲なら修正・commit・push を自動で繰り返すプラグインです。判断に悩む変更は人間にエスカレーションします。

主な構成：

- **Hook**: `gh pr create` が成功すると PR URL を抽出し、監視対象として登録
- **Monitor**: スキル起動を起点にバックグラウンドで `gh pr checks` / `gh pr view` を polling し、CI 失敗・レビュー・コンフリクトを JSON Lines で通知
- **Skill / Agent**: 通知を受けて専用エージェント `pr-auto-fixer` が前提ガードを通過した上で修正・commit・push を実行

「自明な変更」と「悩む変更」の判断基準：

| カテゴリ | 自動修正 | エスカレーション |
|---------|----------|-----------------|
| CI 失敗 | lint / format 違反、typo、import 漏れ、修正候補が一意な型エラー、機械的なスナップショット更新 | テストロジック変更、環境問題、flaky、依存性更新が必要なもの |
| レビュー（人間/Bot 共通） | typo / 命名 / import / 局所 null guard など 5 行以内 1 ファイルの局所修正で、コメントに具体案がある | ロジック / 設計 / API シグネチャ変更 / 矛盾する複数提案 / false positive 疑い |
| コンフリクト | rebase で機械的に解決できるもの（import 並び、末尾改行、整形差分） | 意味解釈が必要なもの |

## インストール

マーケットプレイス経由：

```bash
claude plugin install --marketplace ./path/to/claude-code-marketplace pr-auto-fix
```

ローカルディレクトリを直接指定する場合：

```bash
claude plugin install ./plugins/pr-auto-fix
```

## 使い方

特別な操作は不要です。Claude Code セッション内で `gh pr create ...` を実行すると、PostToolUse Hook が PR URL を抽出して監視対象に登録します。続いて Claude が `pr-auto-fix:auto-fix-pr` スキルを起動することで Monitor がバックグラウンドで動き始め、CI / レビュー / コンフリクトの通知が届くたびに自動で修正フローへ進みます。

```bash
# 通常の流れ（ユーザー視点）
gh pr create --title "..." --body "..."
# → Hook が PR を監視対象に登録
# → Claude が自動的に auto-fix-pr スキルを起動（ユーザー操作不要）
# → Monitor が CI を追跡し、失敗があれば pr-auto-fixer エージェントが修正→push
```

## 設定（オプション）

`userConfig` で以下をカスタマイズできます：

| 設定キー | デフォルト | 説明 |
|---------|-----------|------|
| `pollIntervalSec` | `45` | PR 監視 poll 間隔（秒） |
| `maxAttemptsPerSig` | `3` | 同一イベントへの最大連続修正試行回数 |
| `botPattern` | `copilot\|coderabbit\|claude.*review` | Bot レビュアー判定の正規表現（小文字・extended regex） |

## 動作の仕組み

```text
[ユーザー]
   │ gh pr create
   ▼
[PostToolUse Hook]
   │ PR URL を抽出
   │ watch-targets.json に登録
   │ additionalContext で Claude にスキル起動を促す
   ▼
[auto-fix-pr スキル invoke]
   │ on-skill-invoke で Monitor が起動
   ▼
[pr-auto-fix-watcher Monitor]
   │ INTERVAL ごとに以下を poll：
   │   - gh pr checks --json bucket（CI 失敗）
   │   - gh pr view --json comments,reviews（PR トップレベル + レビュー本文）
   │   - gh api repos/<owner>/<repo>/pulls/<n>/comments（line-level inline コメント）
   │   - gh pr view --json mergeable,mergeStateStatus（コンフリクト）
   │ 新規イベント（ci_failure / review / conflict）を JSON Lines で通知
   ▼
[auto-fix-pr スキル]
   │ kind で分岐し pr-auto-fixer エージェントへ委譲
   ▼
[pr-auto-fixer エージェント]
   │ 1. 前提ガード（現ブランチ・dirty worktree・試行回数・fork 権限）
   │ 2. kind 別修正（CI ログ解析 / 自明性判定 / rebase）
   │ 3. commit & push（rebase 後は --force-with-lease）
   │ 4. 結果ログ or escalation 通知
```

## 必要環境

- **Claude Code v2.1.105 以上**（プラグイン Monitor 機能が必要）
  - `${CLAUDE_PLUGIN_DATA}` 永続ディレクトリは v2.1.78+
  - `Bash(... *)` の Hook `if` フィールドは v2.1.85+
- `gh` CLI（認証済み）
- `jq`
- `git`
- bash 4.x 以上（macOS 標準の `/bin/bash` は 3.x のため `brew install bash` を推奨）

## 制限

- `gh pr create` を **Bash ツール経由で実行した場合のみ** 監視が起動します（GitHub MCP 経由などは現時点で対象外）
- fork からの PR で `maintainerCanModify=false` の場合は push できないため、初回ガードで escalation します
- flaky / 環境依存の CI 失敗には自動対応せず、`maxAttemptsPerSig` 回失敗で escalation します
- ユーザーが PR ブランチから別ブランチに切り替えている間は修正をスキップします（戻ってくれば次回 poll で自動再開）
- uncommitted changes がある状態では勝手に stash せず escalation します（コミット or stash したら次回 poll で再開）

## ライセンス

MIT
