---
description: PRのbotレビューコメントを確認し、妥当な指摘を修正する。/loop と組み合わせて定期実行に最適。
allowed-tools: Bash(gh api:*), Bash(gh pr view:*), Bash(gh pr comment:*), Bash(gh repo view:*), Bash(git add:*), Bash(git commit:*), Bash(git push:*), Bash(git diff:*), Read, Edit, Glob, Grep
argument-hint: "[PR番号]"
context: fork
model: sonnet
effort: high
---

# PRレビューコメント対応

PR `$1` のbotによるレビューコメントを確認し、未対応の指摘事項を修正します。

## 手順

### 1. PR情報の取得

まずリポジトリ情報を変数として取得し、以降のAPIコマンドで使用する:

```bash
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
gh pr view $1 --json number,title,state,headRefName
```

次にbotのレビューコメントを取得:

`targetBots` 設定が空の場合は全Botを対象にし、設定されている場合は指定したbotのみを対象にする。

```bash
# targetBots設定を確認（カンマ区切りのbot名リスト、空の場合は全Bot対象）
TARGET_BOTS="${CLAUDE_USER_CONFIG_targetBots:-}"

# インラインコメント（diff上のコメント）
# targetBotsが設定されている場合は指定botのみ、未設定の場合は全Botを対象
if [ -z "$TARGET_BOTS" ]; then
  gh api repos/$REPO/pulls/$1/comments --jq '.[] | select(.user.type == "Bot") | {id, user: .user.login, body, path, line: .original_line, in_reply_to_id, created_at, html_url}'
else
  # カンマ区切りのbot名リストをjqの条件式に変換して絞り込む
  gh api repos/$REPO/pulls/$1/comments --jq --arg bots "$TARGET_BOTS" '
    ($bots | split(",") | map(ltrimstr(" ") | rtrimstr(" "))) as $bot_list |
    .[] | select(.user.type == "Bot" and (.user.login | IN($bot_list[]))) |
    {id, user: .user.login, body, path, line: .original_line, in_reply_to_id, created_at, html_url}
  '
fi

# レビューサマリー
if [ -z "$TARGET_BOTS" ]; then
  gh api repos/$REPO/pulls/$1/reviews --jq '.[] | select(.user.type == "Bot") | {id, user: .user.login, state, body}'
else
  gh api repos/$REPO/pulls/$1/reviews --jq --arg bots "$TARGET_BOTS" '
    ($bots | split(",") | map(ltrimstr(" ") | rtrimstr(" "))) as $bot_list |
    .[] | select(.user.type == "Bot" and (.user.login | IN($bot_list[]))) |
    {id, user: .user.login, state, body}
  '
fi
```

### 2. 未対応コメントの特定

取得したbotコメントを分析し、以下に分類:

- **修正が必要**: コードの品質・バグ・セキュリティに関する妥当な指摘
- **対応不要（スキップ）**: 誤検知、スタイル上の好み、プロジェクト方針と合わない指摘
- **判断保留**: 修正の妥当性が判断できない指摘

`autoSkipStyleIssues` 設定が `true` の場合、スタイル・フォーマット・命名規則などに関する指摘は自動的に「対応不要（スキップ）」に分類する。スキップ理由は「スタイル系の指摘のため自動スキップ（autoSkipStyleIssues=true）」と記録する。

**重複処理の防止**: 既に返信済みのコメントはスキップすること。以下の条件で判定する:

- そのコメントへの返信スレッド内に自分（GitHub Actions bot等）の返信が存在する
- 返信の本文に「✅」「⏭️」「対応済み」「スキップ」等の対応マーカーが含まれる

```bash
# 各コメントの返信スレッドを確認して対応済みかチェック
gh api repos/$REPO/pulls/$1/comments --jq '[.[] | select(.in_reply_to_id == COMMENT_ID)] | length'
```

### 3. コメント単位の対応サイクル

**各コメントに対して以下のサイクルを個別に実行する。** 全コメントをまとめて処理するのではなく、1件ずつ「判断→修正/スキップ」を実行する。返信はコミット・プッシュ後にまとめて行う（Step 5参照）。

#### 3a. 修正が必要な場合

1. 該当ファイルを読み込む
2. 指摘内容に基づいてコードを修正する
3. 修正が他の箇所に影響しないか確認する
4. 返信内容を記録しておく（返信はStep 5で実施）

#### 3b. 対応不要（スキップ）の場合

修正は行わず、**スキップ理由を記録しておく。**（返信はStep 5で実施）

#### 3c. 判断保留の場合

修正・返信は行わず、結果報告に含める。ユーザーの判断を待つ。

### 4. 変更のコミットとプッシュ

全コメントの対応サイクルが完了した後、修正がある場合はまとめてコミット・プッシュする:

```bash
git add <修正したファイル>
git commit -m "fix: PR #$1 botレビュー対応 - <修正内容の概要>"
HEAD_BRANCH=$(gh pr view $1 --json headRefName -q .headRefName)
git push origin "$HEAD_BRANCH"
```

### 5. コメントへの個別返信

コミット・プッシュ後（またはスキップ判断後）、**各コメントに対して個別に返信を投稿する。**

#### インラインコメントへの返信

```bash
gh api repos/$REPO/pulls/$1/comments/{comment_id}/replies \
  --method POST -f body='返信内容'
```

#### PRレベルコメントへの返信

インラインコメントではないPRレベルのコメントにはスレッド返信APIがないため、PRに新規コメントとして投稿する。元コメントのURLを引用して紐づける。

```bash
gh pr comment $1 --body '返信内容'
```

#### 返信テンプレート

**修正した場合:**

```markdown
✅ 対応済み

<修正内容の説明（1〜2文）>

**コミット**: `<ハッシュ>`
```

**スキップした場合:**

```markdown
⏭️ スキップ

<スキップ理由の説明（1〜2文）>
```

**PRレベルコメントへの対応報告（複数指摘を含むレビューサマリー向け）:**

```markdown
## botレビュー対応報告

> **元の指摘**: [bot名のコメント](元コメントのURL)へ対応

### ✅ 修正済み
| 指摘 | 修正内容 | ファイル |
|------|----------|----------|
| 指摘の要約 | 変更内容の説明 | `path/to/file` |

### ⏭️ スキップ
| 指摘 | 理由 |
|------|------|
| 指摘の要約 | スキップした理由 |

**コミット**: `ハッシュ`
```

### 6. 結果報告

以下の形式で報告:

```text
## レビュー対応状況

**PR**: #$1
**確認したbotコメント数**: X件

### 修正済み（返信済み）
- [bot名] ファイル:行 - 指摘内容の要約

### スキップ（返信済み）
- [bot名] ファイル:行 - 指摘内容 → スキップ理由

### 判断保留（未返信）
- [bot名] ファイル:行 - 指摘内容

### ステータス
- [ ] 全指摘対応完了 → ループを停止してください
- [ ] 未対応あり → 次回ループで再確認
```

### 7. ループ終了判定

全ての指摘が「修正済み」「スキップ」「判断保留」のいずれかに分類済みで、新規の未処理コメントがない場合、「全指摘対応完了。ループを停止してください。」と報告し、ループのキャンセルを提案する。

「判断保留」の指摘はユーザーの判断が必要なため、ループを継続しても自動解決できない。判断保留のみが残っている場合もループを終了し、判断保留の一覧をユーザーに提示すること。

**重要**: プッシュ後にCIが再実行され新たなコメントが付く可能性があるため、最低1回は再確認してから完了と判断すること。
