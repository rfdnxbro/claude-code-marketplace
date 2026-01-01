# CLAUDE.md

このファイルはClaude Codeがこのリポジトリで作業する際のガイダンスを提供します。

## プロジェクト概要

Claude Codeのマーケットプレイスプラグイン。Claude Codeの拡張機能やプラグインを管理・配布するためのプラットフォームを提供します。

## 開発ガイドライン

- すべてのコミュニケーションは日本語で行う
- コード内のコメントは日本語で記述する
- コミットメッセージは日本語で記述する

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
brew install pre-commit gitleaks  # または pip install pre-commit
pre-commit install

# 手動で全ファイルに実行
pre-commit run --all-files
```

pre-commitで実行されるチェック:

- gitleaks: 機密情報検出
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

## .claude/rules/に新規定義を追加する場合

ドキュメント作成だけでなく、対応するバリデーターとテストも追加すること：

1. `.claude/rules/xxx.md` - 仕様ドキュメント作成
2. `scripts/validators/xxx.py` - バリデーター作成
3. `scripts/tests/test_xxx.py` - テスト作成
4. `scripts/validators/__init__.py` - エクスポート追加
5. `scripts/validate_plugin.py` - パス検出ロジック追加
6. 関連する既存ドキュメントからのリンク追加（例: `plugin-manifest.md`）

詳細は `scripts/README.md` の「新しいバリデーターの追加方法」を参照。

## 注意事項

- セキュリティに関わる機密情報（APIキー、認証情報など）はコミットしない
- `.env`ファイルや`credentials.json`などはgitignoreに追加すること
