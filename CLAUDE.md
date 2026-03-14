# CLAUDE.md

Claude Codeがこのリポジトリで作業する際のガイダンスを提供します。

## 目次

- [プロジェクト概要](#プロジェクト概要)
- [クイックスタート](#クイックスタート)
- [開発ガイドライン](#開発ガイドライン)
- [コマンドリファレンス](#コマンドリファレンス)
- [プロジェクト構造](#プロジェクト構造)
- [開発ワークフロー](#開発ワークフロー)
- [注意事項](#注意事項)

## プロジェクト概要

Claude Codeのマーケットプレイスプラグイン。Claude Codeの拡張機能やプラグインを管理・配布するためのプラットフォームを提供します。

## クイックスタート

よく使うコマンド:

```bash
# プラグイン検証
python3 scripts/validate_plugin.py plugins/my-plugin/**/*.md plugins/my-plugin/**/*.json

# テスト実行
uvx pytest scripts/tests/ -v

# 品質チェック（pre-commit）
pre-commit run --all-files
```

## 開発ガイドライン

| ルール | 説明 |
|--------|------|
| 言語 | すべてのコミュニケーション、コメント、コミットメッセージは日本語 |
| 選択肢提示 | 複数の選択肢がある場合は `AskUserQuestion` ツールを使用 |
| 並列処理 | 副作用のない調査・検証タスクはサブエージェントで並列実行 |

## コマンドリファレンス

### プラグイン検証

```bash
# 単一ファイルを検証
python3 scripts/validate_plugin.py plugins/my-plugin/commands/review.md

# プラグイン全体を検証
python3 scripts/validate_plugin.py plugins/my-plugin/**/*.md plugins/my-plugin/**/*.json
```

#### バリデーター警告のスキップ

ファイル内にHTMLコメントを追加:

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
# 基本実行
uvx pytest scripts/tests/ -v

# カバレッジ付き
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

**pre-commitで実行されるチェック:**

| ツール | 対象 |
|--------|------|
| gitleaks | 機密情報検出 |
| ruff | Python lint/format |
| markdownlint | Markdown lint |
| yamllint | YAML lint |
| validate-plugin | プラグインファイル検証 |
| pytest | テスト実行（push時のみ） |

**個別実行:**

```bash
# Python
uvx ruff check scripts/
uvx ruff format scripts/

# Markdown
npx markdownlint-cli --config .markdownlint.json README.md CLAUDE.md scripts/README.md '.claude/rules/*.md' '.claude/skills/**/SKILL.md'

# YAML
uvx yamllint -c .yamllint.yml .github/workflows/
```

## プロジェクト構造

| ディレクトリ | 説明 |
|-------------|------|
| `.claude/rules/` | Claude Code機能の仕様ドキュメント（[索引](.claude/rules/README.md)） |
| `.claude/skills/` | カスタムスキル定義 |
| `scripts/validators/` | 各定義ファイルのバリデーター |
| `scripts/tests/` | バリデーターのテスト |
| `.github/workflows/` | GitHub Actionsワークフロー |

## 開発ワークフロー

### .claude/rules/の変更

#### 新規定義を追加する場合

1. `.claude/rules/xxx.md` - 仕様ドキュメント作成
2. `scripts/validators/xxx.py` - バリデーター作成
3. `scripts/tests/test_xxx.py` - テスト作成
4. `scripts/validators/__init__.py` - エクスポート追加
5. `scripts/validate_plugin.py` - パス検出ロジック追加
6. 関連する既存ドキュメントからのリンク追加

詳細は `scripts/README.md` の「新しいバリデーターの追加方法」を参照。

#### 既存定義を更新する場合

ドキュメントの変更に合わせて、バリデーターとテストも同期:

- フィールドの有効値を変更 → バリデーターの許可リストを更新
- 新しいフィールドを追加 → バリデーターに検証ロジックを追加
- 新しいイベント/オプションを追加 → バリデーターの許可リストに追加

### GitHub Actions

#### 自動実装ワークフロー（auto-implement.yml）

Issueに特定のラベルが付与されると、Claude Codeが自動で実装を行う:

| ラベル | 動作 |
|--------|------|
| `claude-code-update` | Claude Codeのアップデートに伴うドキュメント・バリデーター更新 |
| `plugin-update` | プラグインの改善提案を実装 |

#### claude-code-actionでのIssue作成

`--body-file`オプションを使用すること:

```bash
# NG: シェルエスケープの問題で本文が欠落する可能性
gh issue create --title "..." --body "複雑なマークダウン..."

# OK: ファイル経由で本文を渡す
gh issue create --title "..." --body-file /tmp/issue.md
```

**理由**: 複雑なマークダウン（JSONコードブロック、バッククォート、`${}`変数参照など）はシェルエスケープの問題で本文が空になることがある。

**プロンプトでの指示例**:

```markdown
- **Issue作成時は必ず`--body-file`オプションを使用する**:
  1. Writeツールでissue本文を`/tmp/<name>-issue.md`に書き込む
  2. `gh issue create --title "..." --label "..." --body-file /tmp/<name>-issue.md`を実行
```

**必要な設定**: `allowed-tools`に`Write`を追加すること。

## 注意事項

- **機密情報**: APIキー、認証情報などはコミットしない
- **gitignore**: `.env`ファイルや`credentials.json`などは必ず除外
