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

# Pythonファイルのフォーマット
uvx ruff format scripts/

# Markdownのチェック
npx markdownlint-cli2 "**/*.md"

# YAMLのチェック
uvx yamllint .
```

## 注意事項

- セキュリティに関わる機密情報（APIキー、認証情報など）はコミットしない
- `.env`ファイルや`credentials.json`などはgitignoreに追加すること
