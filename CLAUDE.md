# CLAUDE.md

このファイルはClaude Codeがこのリポジトリで作業する際のガイダンスを提供します。

## プロジェクト概要

Claude Codeのマーケットプレイスプラグイン。Claude Codeの拡張機能やプラグインを管理・配布するためのプラットフォームを提供します。

## 開発ガイドライン

- すべてのコミュニケーション・コミットメッセージ・コード内コメントは日本語で記述する
- 複数の選択肢を提示する場合は `AskUserQuestion` ツールを使用する
- 並列実行しても副作用がない調査・検証タスクはサブエージェント（Taskツール）で並列実行する
- セキュリティに関わる機密情報（APIキー、認証情報など）はコミットしない
- `.env`ファイルや`credentials.json`などはgitignoreに追加すること

## プロジェクト構造

| ディレクトリ | 説明 |
|-------------|------|
| `.claude/rules/` | Claude Code機能の仕様ドキュメント |
| `scripts/validators/` | 各定義ファイルのバリデーター |
| `scripts/tests/` | バリデーターのテスト |
| `.github/workflows/` | GitHub Actionsワークフロー |

## コマンド

### プラグイン検証

```bash
# 単一ファイルを検証
python3 scripts/validate_plugin.py plugins/my-plugin/commands/review.md

# プラグイン全体を検証
python3 scripts/validate_plugin.py plugins/my-plugin/**/*.md plugins/my-plugin/**/*.json
```

#### claude plugin validate（v2.1.77以降）

`claude plugin validate` コマンドの検証範囲が拡張されました:

- スキル・エージェント・コマンドのfrontmatter（YAMLパースエラー・スキーマ違反を検出）
- `hooks/hooks.json`（YAMLパースエラー・スキーマ違反を検出）

```bash
# Claude Code CLIによるプラグイン検証（v2.1.77以降）
claude plugin validate
```

#### 警告のスキップ

ファイル内にHTMLコメントを追加してバリデーター警告をスキップ:

```markdown
<!-- validator-disable dangerous-operation -->
```

| 警告ID | 説明 |
|--------|------|
| `dangerous-operation` | 危険なキーワード（deploy, delete等）検出時 |
| `broad-bash-wildcard` | `Bash(*)`使用時 |

詳細は `.claude/rules/slash-commands.md` を参照。

### テスト実行

```bash
# テストを実行（uvを使用）
uvx pytest scripts/tests/ -v

# カバレッジ付きでテストを実行
uvx --with pytest-cov pytest scripts/tests/ -v --cov=scripts/validators --cov-report=term
```

### Linter/Formatter

品質チェックはpre-commitで一括管理。基本的に `pre-commit run --all-files` で全チェックを実行する。

```bash
# 初回セットアップ
brew install pre-commit  # または pip install pre-commit
pre-commit install

# 手動で全ファイルに実行
pre-commit run --all-files
```

含まれるチェック: gitleaks（機密情報検出）、ruff（Python lint/format）、markdownlint、yamllint、validate-plugin、pytest（push時のみ）

## .claude/rules/ の変更ガイドライン

### 新規定義を追加する場合

ドキュメント作成だけでなく、対応するバリデーターとテストも追加すること：

1. `.claude/rules/xxx.md` - 仕様ドキュメント作成
2. `scripts/validators/xxx.py` - バリデーター作成
3. `scripts/tests/test_xxx.py` - テスト作成
4. `scripts/validators/__init__.py` - エクスポート追加
5. `scripts/validate_plugin.py` - パス検出ロジック追加
6. 関連する既存ドキュメントからのリンク追加（例: `plugin-manifest.md`）

詳細は `scripts/README.md` の「新しいバリデーターの追加方法」を参照。

### 既存定義を更新する場合

ドキュメントの変更に合わせて、対応するバリデーターとテストも必ず同期すること：

- フィールドの有効値を変更 → バリデーターの許可リストを更新
- 新しいフィールドを追加 → バリデーターに検証ロジックを追加
- 新しいイベント/オプションを追加 → バリデーターの許可リストに追加
- 上記すべてに対応するテストを追加・更新

## GitHub Actionsワークフロー

### 自動実装ワークフロー（auto-implement.yml）

Issueに特定のラベルが付与されると、Claude Codeが自動で実装を行う。

- `claude-code-update`: Claude Codeのアップデートに伴うドキュメント・バリデーター更新
- `plugin-update`: プラグインの改善提案を実装

### claude-code-actionでのIssue作成

`claude-code-action`でIssueを作成する際は、シェルエスケープの問題を避けるため`--body-file`オプションを使用すること。

```bash
# NG: シェルエスケープの問題で本文が欠落する可能性がある
gh issue create --title "..." --body "複雑なマークダウン..."

# OK: ファイル経由で本文を渡す
gh issue create --title "..." --body-file /tmp/issue.md
```

`allowed-tools`に`Write`を追加し、Writeツールでissue本文を一時ファイルに書き込んでから`--body-file`で渡す。
