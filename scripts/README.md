# プラグイン検証スクリプト

Claude Codeプラグインのベストプラクティス準拠を自動検証するスクリプト。

CI/CDとローカルhookの両方で利用可能。

## hookとしてセットアップ（任意）

`.claude/settings.json`に以下を追加:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PROJECT_DIR}/scripts/validate_plugin.py",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

## 検証対象

| ファイル種別 | パス | 検証内容 |
|------------|------|----------|
| スラッシュコマンド | `**/commands/**/*.md` | description、allowed-tools、disable-model-invocation、model |
| サブエージェント | `**/agents/**/*.md` | name（必須・kebab-case）、description、model、permissionMode |
| スキル | `**/SKILL.md` | name（64文字・形式・予約語）、description（1024文字）、本文500行 |
| hooks.json | `**/hooks.json` | イベント名、hookタイプ、必須フィールド |
| MCP設定 | `**/.mcp.json` | サーバータイプ、必須フィールド、機密情報検出 |
| LSP設定 | `**/.lsp.json` | command、extensionToLanguage、transport、機密情報検出 |
| プラグイン定義 | `**/.claude-plugin/plugin.json` | name（必須・kebab-case）、version形式、パス記述 |
| README | `**/plugins/**/README.md` | 必須セクション、相対リンク切れ、コードブロック言語指定 |
| 出力スタイル | `**/output-styles/**/*.md` | name、description、keep-coding-instructions、本文 |

## 機密情報検出

`.mcp.json`と`.lsp.json`で以下の機密情報パターンを検出してエラーとして報告:

- OpenAI APIキー (`sk-...`, `sk-proj-...`)
- GitHub Token (`ghp_...`, `gho_...`, `ghu_...`, `ghs_...`)
- Slack Token (`xoxb-...`, `xoxa-...`, `xoxp-...`)
- AWS Access Key ID (`AKIA...`)
- Google API Key (`AIza...`)

機密情報は`${VAR}`形式で環境変数から参照してください。

## 手動実行

```bash
# 単一ファイルを検証
python3 scripts/validate_plugin.py plugins/my-plugin/commands/review.md

# 複数ファイルを検証
python3 scripts/validate_plugin.py plugins/my-plugin/commands/*.md

# プラグイン全体を検証（ディレクトリ内の対象ファイルすべて）
python3 scripts/validate_plugin.py plugins/my-plugin/**/*.md plugins/my-plugin/**/*.json
```

## テスト実行

### uvを使用する場合（推奨）

```bash
# プロジェクトルートで実行
uvx pytest scripts/tests/ -v

# カバレッジ付きで実行
uvx --with pytest-cov pytest scripts/tests/ -v --cov=scripts/validators --cov-report=term
```

### venvを使用する場合

```bash
# 仮想環境を作成・有効化
python3 -m venv scripts/.venv
source scripts/.venv/bin/activate

# 依存関係をインストール
pip install -e "scripts/[dev]"

# テスト実行
pytest scripts/tests/ -v
```

## 新しいバリデーターの追加方法

以下のパスはプロジェクトルートからの相対パスです。

1. `scripts/validators/`に新しいファイルを作成:

```python
# scripts/validators/new_file.py
from pathlib import Path
from .base import ValidationResult, parse_frontmatter

def validate_new_file(file_path: Path, content: str) -> ValidationResult:
    result = ValidationResult()
    frontmatter, body, yaml_warnings = parse_frontmatter(content)

    for w in yaml_warnings:
        result.add_warning(f"{file_path.name}: {w}")

    # 検証ロジック
    if not frontmatter.get("required_field"):
        result.add_error(f"{file_path.name}: required_fieldが必須です")

    return result
```

2. `scripts/validators/__init__.py`でインポートと`__all__`に追加:

```python
from .new_file import validate_new_file

__all__ = [
    # ... 既存のエクスポート ...
    "validate_new_file",
]
```

3. `scripts/validate_plugin.py`を修正:

```python
# importに追加
from validators import (
    # ... 既存のインポート ...
    validate_new_file,
)

# main()内のパス判定に追加（elseの前に）
elif file_path.name == "new_file.ext":
    content = read_file_content(file_path)
    if content is not None:
        result = validate_new_file(file_path, content)
```

4. `scripts/tests/test_new_file.py`でテストを追加:

```python
# scripts/tests/test_new_file.py
from pathlib import Path
from textwrap import dedent

from scripts.validators.new_file import validate_new_file


class TestValidateNewFile:
    """new_file検証のテスト"""

    def test_valid_file(self):
        content = dedent("""
            ---
            required_field: value
            ---
            本文
        """).strip()
        result = validate_new_file(Path("test.ext"), content)
        assert not result.has_errors()
```

## 制限事項

### YAMLパーサー

簡易YAMLパーサーを使用しているため、以下の機能はサポートされていません:

- 複数行の値（`|`, `>`）
- リスト/配列
- ネストされたオブジェクト

サポートされていない機能を使用した場合は警告が表示されます。

### パス判定

ファイルパスに`commands`、`agents`などのディレクトリ名が含まれているかで判定しています。
意図しないファイルが検証対象になる可能性があります。

## トラブルシューティング

### hookが動作しない

1. `.claude/settings.json`の設定を確認
2. スクリプトのパスが正しいか確認
3. Python 3.10以上がインストールされているか確認

### エンコーディングエラー

ファイルがUTF-8でエンコードされていることを確認してください。
