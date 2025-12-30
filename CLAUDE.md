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

### テスト実行

```bash
# テストを実行（uvを使用）
uvx pytest scripts/tests/ -v
```

### Linter/Formatter

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
