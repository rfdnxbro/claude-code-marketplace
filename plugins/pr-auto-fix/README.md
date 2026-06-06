# pr-auto-fix

## 概要

`gh pr create` で PR を作成した直後から、PR の **CI 失敗 / レビューコメント / ベースブランチからのコンフリクト** をバックグラウンドで自動監視し、自明な範囲なら修正・commit・push を自動で繰り返すプラグインです。修正完了や対応不可の理由は **GitHub PR にもコメントとして自動投稿** されます（v0.2.0〜）。

主な構成：

- **Hook**: `gh pr create` が成功すると PR URL を抽出し、監視対象として登録
- **Monitor**: スキル起動を起点にバックグラウンドで `gh pr checks` / `gh pr view` を polling し、CI 失敗・レビュー・コンフリクトを JSON Lines で通知
- **Skill / Agent**: 通知を受けて専用エージェント `pr-auto-fixer` が前提ガードを通過した上で修正・commit・push を実行。完了 or 対応不可は PR にコメント

「自明な変更」と「悩む変更」の判断基準：

| カテゴリ | 自動修正（PR に完了コメント） | エスカレーション（PR に理由コメント） |
|---------|----------|-----------------|
| CI 失敗 | lint / format 違反、typo、import 漏れ、修正候補が一意な型エラー、機械的なスナップショット更新 | テストロジック変更、環境問題、flaky、依存性更新が必要なもの |
| レビュー（人間/Bot 共通） | typo / 命名 / import / 局所 null guard など 5 行以内 1 ファイルの局所修正で、コメントに具体案がある | ロジック / 設計 / API シグネチャ変更 / 矛盾する複数提案 / false positive 疑い |
| コンフリクト | rebase で機械的に解決できるもの（import 並び、末尾改行、整形差分） | 意味解釈が必要なもの |

## Claude Code プリセット `/autofix-pr` との違い

公式の [`/autofix-pr`](https://code.claude.com/docs/en/claude-code-on-the-web#auto-fix-pull-requests) はクラウド VM 上で動くプリセットコマンドで、設計が根本的に異なります。

| 項目 | プリセット `/autofix-pr` | このプラグイン |
|---|---|---|
| 動作場所 | Anthropic 管理のクラウド VM（[claude.ai/code](https://claude.ai/code)） | ローカルの Claude Code セッション |
| トリガー | GitHub Webhook（Claude GitHub App 経由） | ローカル `gh` の polling（デフォルト 45 秒） |
| 必須環境 | Claude GitHub App、**Pro/Max/Team プラン限定**、GitHub のみ | ローカル `gh`/`jq`/`git`、プラン制限なし、GitHub のみ（`gh` CLI 前提） |
| コンフリクト対応 | 不可（GitHub が webhook を出さないため） | 可能（polling で `mergeable` を見て機械的解決を試みる） |
| ローカル設定の持ち込み | repo にコミットされたもののみ | ローカルセッションそのまま |
| セッション継続 | クラウドで永続化 | ローカルセッションが開いている間のみ |
| 対応不可の理由を PR に投稿 | session 内 confirm が中心 | **PR コメントとして自動投稿**（v0.2.0〜） |

**このプラグインを選ぶシーン**: GitHub App を入れたくない／Pro 未満のプラン／コンフリクトも自動対応したい／ローカル設定を持ち込みたい。

**プリセットを選ぶシーン**: シンプルに済ませたい／リアルタイム webhook が必要／ローカルセッションを開きっぱなしにしたくない。

> **注**: 両方とも GitHub 限定です。Hook の URL 抽出が `github.com` ハードコードのため GitHub Enterprise Server / GitLab / Bitbucket では動作しません。

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
   │ systemMessage で Claude にスキル起動を促す
   ▼
[auto-fix-pr スキル invoke]
   │ on-skill-invoke で Monitor が起動
   ▼
[pr-auto-fix-watcher Monitor]
   │ INTERVAL ごとに以下を poll：
   │   - gh pr checks --json bucket（CI 失敗）
   │   - gh api repos/<owner>/<repo>/issues/<n>/comments --paginate（PR トップレベルコメント）
   │   - gh api repos/<owner>/<repo>/pulls/<n>/reviews --paginate（レビュー本文）
   │   - gh api repos/<owner>/<repo>/pulls/<n>/comments --paginate（line-level inline コメント）
   │   - gh pr view --json mergeable,mergeStateStatus,baseRefName（コンフリクト）
   │ 新規イベント（ci_failure / review / conflict）を JSON Lines で通知
   ▼
[auto-fix-pr スキル]
   │ kind で分岐し pr-auto-fixer エージェントへ委譲
   ▼
[pr-auto-fixer エージェント]
   │ 1. 前提ガード（現ブランチ・dirty worktree・試行回数・fork 権限）
   │ 2. kind 別修正（CI ログ解析 / 自明性判定 / rebase）
   │ 3. commit & push（rebase 後は --force-with-lease）
   │ 4. PR コメント投稿（成功: 完了報告 / permanent escalation: 対応不可の理由）
   │    - inline review コメント由来なら該当スレッドへ in-reply
   │    - それ以外は PR トップレベルコメント
   │    - 重複投稿は ${CLAUDE_PLUGIN_DATA}/posted-comments.json でガード
   │ 5. 結果ログ or escalation 通知
```

### PR コメント投稿の例

修正成功時（PR トップレベル）：

```markdown
✅ **pr-auto-fix**: `ci_failure` を自動修正しました。

- 修正対象: `lint`
- 修正内容: `pnpm lint --fix` を実行し prettier 整形差分を解消
- コミット: `a1b2c3d4e5f6`

<!-- pr-auto-fix: a1b2c3d4e5f6abcd -->
```

対応不可時（inline review への in-reply）：

```markdown
⚠️ **pr-auto-fix**: `review` は自動対応できませんでした。

- 理由: `judgment_required`
- 詳細: `useState` を `useReducer` に書き換える提案だが、コンポーネントの責務見直しを含む設計判断のため自動修正の範囲外と判断。

人間のレビューまたは手動対応をお願いします。

<!-- pr-auto-fix: f1e2d3c4b5a69876 -->
```

`<!-- pr-auto-fix: <hash> -->` の HTML コメントは重複投稿判定にも使えます（同じ hash の二重投稿を防ぐ）。

## 必要環境

- **Claude Code v2.1.105 以上**（プラグイン Monitor 機能が必要）
  - `${CLAUDE_PLUGIN_DATA}` 永続ディレクトリは v2.1.78+
  - `Bash(... *)` の Hook `if` フィールドは v2.1.85+
- `gh` CLI（認証済み）
- `jq`
- `git`
- bash 4.x 以上（macOS 標準の `/bin/bash` は 3.x のため `brew install bash` を推奨）

## 制限

- **GitHub のみ対応**: `gh pr create` Hook が抽出する PR URL の正規表現が `https://github.com/...` ハードコードのため、GitHub Enterprise Server（GHES）/ GitLab / Bitbucket では Hook が silent fail します。
- `gh pr create` を **Bash ツール経由で実行した場合のみ** 監視が起動します（GitHub MCP 経由などは現時点で対象外）
- `watch-targets.json` が空のまま起動した Monitor は、短時間 sleep したあと自動終了します。新しい PR を作成すると Hook が再度スキル起動を促します
- fork からの PR で `maintainerCanModify=false` の場合は push できないため、初回ガードで escalation します
- flaky / 環境依存の CI 失敗には自動対応せず、`maxAttemptsPerSig` 回失敗で escalation します
- ユーザーが PR ブランチから別ブランチに切り替えている間は修正をスキップします（戻ってくれば次回 poll で自動再開）
- uncommitted changes がある状態では勝手に stash せず escalation します（コミット or stash したら次回 poll で再開）
- PR コメント投稿はユーザーの `gh` 認証アカウント名義で行われます。`issue_comment` イベントで動く GitHub Actions（Atlantis 等）がある場合は意図せず発火する可能性があるため注意（プリセット `/autofix-pr` でも同様の警告あり）
- transient escalation（`not_on_pr_branch` / `dirty_worktree`）は PR コメントを投稿しません（ローカル状況依存でレビュアーに無関係なため）

## ライセンス

MIT
