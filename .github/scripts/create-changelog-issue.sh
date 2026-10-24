#!/usr/bin/env bash
# CHANGELOG監視CI（changelog-monitor.yml）から Claude が呼び出す起票スクリプト。
# Issueタイトルの版数が CHANGELOG の見出しに実在するかを確かめてから Issue を作成する。
# 起票時に版数を取り違える例があったため（v2.1.290 の内容が v2.1.291 として起票された）。
#
# 入力（Claude が Write ツールで書き出す）:
#   /tmp/changelog-issue-title.txt  Issueタイトル（1行）
#   /tmp/changelog-issue.md         Issue本文
# 照合先:
#   current-changelog.md            最新のCHANGELOG（ワークフローが取得したもの）
#
# 各パスは環境変数で差し替えられる（ローカルでの動作確認用）。
#
# 認証の前提: gh は claude-code-action が Claude の実行環境に渡す GitHub App のトークンで動く。
# GITHUB_TOKEN で作った Issue やラベル付与では auto-implement.yml（issues: labeled）が起動しないため、
# このスクリプトをワークフローのシェルステップから GITHUB_TOKEN で呼ぶ形に変えてはならない。
set -euo pipefail

TITLE_FILE="${CHANGELOG_ISSUE_TITLE_FILE:-/tmp/changelog-issue-title.txt}"
BODY_FILE="${CHANGELOG_ISSUE_BODY_FILE:-/tmp/changelog-issue.md}"
CHANGELOG_FILE="${CHANGELOG_FILE:-current-changelog.md}"
LABEL="claude-code-update"

# auto-implement.yml の CHANGELOG_TITLE_RE と同じ形式（単一版数、または「古い版-新しい版」の範囲）
TITLE_RE='^\[CHANGELOG (v[0-9]+\.[0-9]+\.[0-9]+(-v[0-9]+\.[0-9]+\.[0-9]+)?)\] [^[:space:]]'

fail() {
  echo "エラー: $*" >&2
  echo "Issueは作成していません。内容を直してから再実行してください。" >&2
  exit 1
}

[ -s "$TITLE_FILE" ] || fail "${TITLE_FILE} がないか空です"
[ -s "$BODY_FILE" ] || fail "${BODY_FILE} がないか空です"
[ -s "$CHANGELOG_FILE" ] || fail "${CHANGELOG_FILE} がないか空です"

# 改行を含むタイトルは gh に渡す前に弾く
if [ "$(grep -c '' "$TITLE_FILE")" -ne 1 ]; then
  fail "${TITLE_FILE} は1行にしてください"
fi
TITLE=$(sed -e 's/[[:space:]]*$//' "$TITLE_FILE")

if ! [[ "$TITLE" =~ $TITLE_RE ]]; then
  fail "タイトルは「[CHANGELOG v2.1.290] 概要」または「[CHANGELOG v2.1.290-v2.1.291] 概要」の形式にしてください: ${TITLE}"
fi
VERSION="${BASH_REMATCH[1]}"

# 形式を検証済みなので、単語分割で範囲の両端を取り出してよい
VERSIONS=(${VERSION//-/ })
for V in "${VERSIONS[@]}"; do
  if ! grep -qxF "## ${V#v}" "$CHANGELOG_FILE"; then
    fail "タイトルの版数 ${V} に当たる見出し「## ${V#v}」が ${CHANGELOG_FILE} にありません。各項目がどの見出しの下にあるかを確かめ直してください"
  fi
done

if [ "${#VERSIONS[@]}" -eq 2 ]; then
  OLDER="${VERSIONS[0]#v}"
  NEWER="${VERSIONS[1]#v}"
  if [ "$OLDER" = "$NEWER" ] || ! printf '%s\n%s\n' "$OLDER" "$NEWER" | sort -C -V; then
    fail "範囲は「古い版-新しい版」の順で書いてください: ${VERSION}"
  fi
fi

echo "版数 ${VERSION} の見出しを ${CHANGELOG_FILE} で確認しました。Issueを作成します。"
gh issue create --title "$TITLE" --label "$LABEL" --body-file "$BODY_FILE"

# 続けて別のIssueを起票するときに、前のタイトル・本文を使い回さないよう消しておく
rm -f "$TITLE_FILE" "$BODY_FILE"
