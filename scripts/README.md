# プラグイン検証スクリプト

Claude Codeプラグインのベストプラクティス準拠を自動検証するhookスクリプト。

## セットアップ

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
| プラグイン定義 | `**/.claude-plugin/plugin.json` | name（必須・kebab-case）、version形式、パス記述 |

## 機密情報検出

`.mcp.json`で以下の機密情報パターンを検出してエラーとして報告:

- OpenAI APIキー (`sk-...`, `sk-proj-...`)
- GitHub Token (`ghp_...`, `gho_...`, `ghu_...`, `ghs_...`)
- Slack Token (`xoxb-...`, `xoxa-...`, `xoxp-...`)
- AWS Access Key ID (`AKIA...`)
- Google API Key (`AIza...`)

機密情報は`${VAR}`形式で環境変数から参照してください。

## テスト実行

```bash
# プロジェクトルートで実行
cd scripts

# 手動テスト（pytest不要）
python3 -c "
import sys
sys.path.insert(0, '.')
from tests.test_base import *
from tests.test_slash_command import *
from tests.test_agent import *
from tests.test_skill import *
from tests.test_hooks_json import *
from tests.test_mcp_json import *
from tests.test_plugin_json import *
from tests.test_integration import *

test_classes = [
    TestValidationResult, TestParseFrontmatter,
    TestValidateSlashCommand, TestValidateAgent, TestValidateSkill,
    TestValidateHooksJson, TestValidateMcpJson, TestValidatePluginJson,
    TestIntegration,
]

total = passed = 0
for cls in test_classes:
    for method in dir(cls()):
        if method.startswith('test_'):
            total += 1
            try:
                getattr(cls(), method)()
                passed += 1
                print(f'  ✓ {cls.__name__}.{method}')
            except Exception as e:
                print(f'  ✗ {cls.__name__}.{method}: {e}')
print(f'\n結果: {passed}/{total}')
"

# pytest（インストール済みの場合）
python -m pytest tests/ -v
```

## 新しいバリデーターの追加方法

1. `validators/`に新しいファイルを作成:

```python
# validators/new_file.py
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

2. `validators/__init__.py`でエクスポート:

```python
from .new_file import validate_new_file
__all__ = [..., "validate_new_file"]
```

3. `validate_plugin.py`のパス判定に追加:

```python
elif file_path.name == "new_file.ext":
    content = read_file_content(file_path)
    if content is not None:
        result = validate_new_file(file_path, content)
```

4. `tests/test_new_file.py`でテストを追加

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
