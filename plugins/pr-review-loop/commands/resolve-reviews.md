---
description: PRのbotレビューコメントを確認し、妥当な指摘を修正する。/loop と組み合わせて定期実行に最適。
allowed-tools: Bash(gh api:*), Bash(gh pr view:*), Bash(gh pr comment:*), Bash(gh repo view:*), Bash(git add:*), Bash(git commit:*), Bash(git push:*), Bash(git diff:*), Read, Edit, Glob, Grep
argument-hint: "[PR番号]"
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

```bash
gh api repos/$REPO/pulls/$1/comments --jq '.[] | select(.user.type == "Bot") | {id, user: .user.login, body, path, line: .original_line, in_reply_to_id, created_at}'
gh api repos/$REPO/pulls/$1/reviews --jq '.[] | select(.user.type == "Bot") | {id, user: .user.login, state, body}'
```

### 2. 未対応コメントの特定

取得したbotコメントを分析し、以下に分類:

- **修正が必要**: コードの品質・バグ・セキュリティに関する妥当な指摘
- **対応不要**: 誤検知、スタイル上の好み、プロジェクト方針と合わない指摘
- **判断保留**: 修正の妥当性が判断できない指摘

**重複処理の防止**: 既に返信済み（`in_reply_to_id`で自分の返信が存在する）のコメントや、bot自身が「Resolved」と返信しているコメントはスキップすること。

### 3. コードの修正

「修正が必要」と判断した指摘について:

1. 該当ファイルを読み込む
2. 指摘内容に基づいてコードを修正する
3. 修正が他の箇所に影響しないか確認する

### 4. 変更のコミットとプッシュ

修正がある場合、PRのヘッドブランチを取得して明示的にプッシュする。コミットメッセージには修正内容の概要を含めること:

```bash
git add <修正したファイル>
git commit -m "fix: PR #$1 botレビュー対応 - <修正内容の概要>"
HEAD_BRANCH=$(gh pr view $1 --json headRefName -q .headRefName)
git push origin "$HEAD_BRANCH"
```

### 5. 修正内容をPRコメントとして投稿

コミット・プッシュ後、対応内容をPRコメントとして投稿する。
これにより、レビュー履歴上で「何をどう直したか」が追跡可能になる。

コメントの種類に応じて投稿方法を使い分ける:

**インラインコメント（diff上の特定行への指摘）への返信:**

```bash
gh api repos/$REPO/pulls/$1/comments/{comment_id}/replies \
  --method POST -f body='対応内容'
```

**PRレベルのコメント（レビューサマリー等）への対応:**

インラインコメントではないPRレベルのコメントにはスレッド返信APIがないため、PRに新規コメントとして投稿する。元コメントのURLを引用して紐づける。

```bash
gh pr comment $1 --body '対応内容'
```

投稿本文は以下の形式:

```markdown
## botレビュー対応報告

> **元の指摘**: [bot名のコメント](元コメントのURL)へ対応

### ✅ 修正済み
| 指摘 | 修正内容 | ファイル |
|------|----------|----------|
| 指摘の要約 | 変更内容の説明 | `path/to/file` |

### ⏭️ 対応不要
| 指摘 | 理由 |
|------|------|
| 指摘の要約 | 不要と判断した理由 |

**コミット**: `ハッシュ`
```

### 6. 結果報告

以下の形式で報告:

```text
## レビュー対応状況

**PR**: #$1
**確認したbotコメント数**: X件

### 修正済み
- [bot名] ファイル:行 - 指摘内容の要約

### 対応不要（理由付き）
- [bot名] ファイル:行 - 指摘内容 → 不要理由

### 判断保留
- [bot名] ファイル:行 - 指摘内容

### ステータス
- [ ] 全指摘対応完了 → ループを停止してください
- [ ] 未対応あり → 次回ループで再確認
```

### 7. ループ終了判定

全ての指摘が「修正済み」「対応不要」「判断保留」のいずれかに分類済みで、新規の未処理コメントがない場合、「全指摘対応完了。ループを停止してください。」と報告し、ループのキャンセルを提案する。

「判断保留」の指摘はユーザーの判断が必要なため、ループを継続しても自動解決できない。判断保留のみが残っている場合もループを終了し、判断保留の一覧をユーザーに提示すること。

**重要**: プッシュ後にCIが再実行され新たなコメントが付く可能性があるため、最低1回は再確認してから完了と判断すること。
