# CLAUDE.md

このファイルはClaude Codeがこのリポジトリで作業する際のガイダンスを提供します。

## プロジェクト概要

Claude Codeのマーケットプレイスプラグイン。Claude Codeの拡張機能やプラグインを管理・配布するためのプラットフォームを提供します。

## 開発ガイドライン

- すべてのコミュニケーションは日本語で行う
- コード内のコメントは日本語で記述する
- コミットメッセージは日本語で記述する
- 複数の選択肢を提示する場合は `AskUserQuestion` ツールを使用する
- 並列実行しても副作用がない調査・検証タスクはサブエージェント（Taskツール）で並列実行する

## コマンド

### プラグイン検証

```bash
# 単一ファイルを検証
python3 scripts/validate_plugin.py plugins/my-plugin/commands/review.md

# プラグイン全体を検証
python3 scripts/validate_plugin.py plugins/my-plugin/**/*.md plugins/my-plugin/**/*.json
```

#### 警告のスキップ

バリデーターの警告を意図的にスキップするには、ファイル内にHTMLコメントを追加:

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

### Linter/Formatter（pre-commit）

品質チェックはpre-commitで一括管理されています。

```bash
# 初回セットアップ
brew install pre-commit  # または pip install pre-commit
pre-commit install

# 手動で全ファイルに実行
pre-commit run --all-files
```

pre-commitで実行されるチェック:

- gitleaks: 機密情報検出（自動ダウンロード）
- ruff: Python lint/format
- markdownlint: Markdown lint
- yamllint: YAML lint
- validate-plugin: プラグインファイル検証
- pytest: テスト実行（push時のみ）

個別に手動実行する場合:

```bash
# Pythonファイルのチェック
uvx ruff check scripts/

# Pythonファイルのフォーマット（CIでは --check で検証）
uvx ruff format scripts/

# Markdownのチェック
npx markdownlint-cli --config .markdownlint.json README.md CLAUDE.md scripts/README.md '.claude/rules/*.md' '.claude/skills/**/SKILL.md'

# YAMLのチェック
uvx yamllint -c .yamllint.yml .github/workflows/
```

## プロジェクト構造

- `.claude/rules/` - Claude Code機能の仕様ドキュメント
- `scripts/validators/` - 各定義ファイルのバリデーター
- `scripts/tests/` - バリデーターのテスト
- `.github/workflows/` - GitHub Actionsワークフロー

## GitHub Actionsワークフロー

### 自動実装ワークフロー（auto-implement.yml）

Issueに特定のラベルが付与されると、Claude Codeが自動で実装を行う。

- `claude-code-update`: Claude Codeのアップデートに伴うドキュメント・バリデーター更新
- `plugin-update`: プラグインの改善提案を実装

### claude-code-actionでのIssue作成

`claude-code-action`でIssueを作成する際は、`--body-file`オプションを使用すること。

```bash
# NG: シェルエスケープの問題で本文が欠落する可能性がある
gh issue create --title "..." --body "複雑なマークダウン..."

# OK: ファイル経由で本文を渡す
gh issue create --title "..." --body-file /tmp/issue.md
```

**理由**: `--body`オプションで複雑なマークダウン（JSONコードブロック、バッククォート、`${}`変数参照など）を渡すと、シェルエスケープの問題で本文が空になることがある。

**プロンプトでの指示例**:

```markdown
- **Issue作成時は必ず`--body-file`オプションを使用する**:
  1. Writeツールでissue本文を`/tmp/<name>-issue.md`に書き込む
  2. `gh issue create --title "..." --label "..." --body-file /tmp/<name>-issue.md`を実行
```

**必要な設定**: `allowed-tools`に`Write`を追加すること。

## .claude/rules/の変更ガイドライン

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

## 注意事項

- セキュリティに関わる機密情報（APIキー、認証情報など）はコミットしない
- `.env`ファイルや`credentials.json`などはgitignoreに追加すること
