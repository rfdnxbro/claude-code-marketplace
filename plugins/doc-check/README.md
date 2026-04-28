# doc-check

## 概要

変更に関連するドキュメント（README.md、CLAUDE.mdなど）の整合性を自動チェックするプラグインです。
Claude Codeがファイルを書き込み・編集した後（PostToolUseフック）に、変更内容とドキュメントの不一致がないかを確認し、問題があれば報告します。

## インストール

マーケットプレイス経由:

```bash
claude plugin install --marketplace ./path/to/claude-code-marketplace doc-check
```

ローカルで直接指定する場合:

```bash
claude plugin install ./plugins/doc-check
```

## 使い方

インストール後、特別な操作は不要です。Claude CodeがWriteまたはEditツールでファイルを変更するたびに、自動的にドキュメント整合性チェックが実行されます。

- 不一致が検出された場合: 具体的な問題箇所が報告されます
- 問題がない場合: 「✓ ドキュメント整合性OK」と表示されます

## 設定（オプション）

デフォルトでは `README.md` と `CLAUDE.md` が整合性チェックの対象です。
以下の設定でカスタマイズできます:

| 設定キー | デフォルト | 説明 |
|---------|-----------|------|
| `docPatterns` | `README.md,CLAUDE.md` | チェック対象ドキュメントのファイルパターン（カンマ区切り） |
| `skipPatterns` | （空） | チェックをスキップするファイルパターン（カンマ区切り） |

### 設定例

テストファイルの変更時にチェックをスキップする場合:

```
skipPatterns: *.test.ts,*.spec.ts
```

`docs/` ディレクトリ内のMarkdownもチェック対象に含める場合:

```
docPatterns: README.md,CLAUDE.md,docs/*.md
```

## 高度な設定

### セッション終了フックのタイムアウト調整 (v2.1.74以降)

セッション終了時のログ記録スクリプトのタイムアウトを調整するには:

```bash
CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS=30000  # 30秒に延長
```

## 注意事項

このプラグインはファイルの書き込み・編集のたびにLLMを呼び出してチェックを行います。ファイル変更が多いセッションでは複数回実行されるため、コストと待ち時間が増加する場合があります。
