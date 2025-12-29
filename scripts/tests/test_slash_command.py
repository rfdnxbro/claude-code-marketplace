"""
slash_command.py のテスト
"""


from pathlib import Path
from textwrap import dedent

from scripts.validators.slash_command import validate_slash_command


class TestValidateSlashCommand:
    """スラッシュコマンド検証のテスト"""

    def test_valid_command(self):
        content = dedent("""
            ---
            description: テストコマンド
            allowed-tools: Bash(git add:*)
            ---
            コマンド本文
        """).strip()
        result = validate_slash_command(Path("test.md"), content)
        assert not result.has_errors()
        assert len(result.warnings) == 0

    def test_missing_description_with_body(self):
        content = dedent("""
            ---
            allowed-tools: Read(*)
            ---
            本文があるのでデフォルトが使われる
        """).strip()
        result = validate_slash_command(Path("test.md"), content)
        assert not result.has_errors()
        assert len(result.warnings) == 1
        assert "description" in result.warnings[0]

    def test_missing_description_empty_body(self):
        content = dedent("""
            ---
            allowed-tools: Read(*)
            ---
        """).strip()
        result = validate_slash_command(Path("test.md"), content)
        assert result.has_errors()
        assert "description" in result.errors[0]

    def test_broad_bash_wildcard(self):
        content = dedent("""
            ---
            description: テスト
            allowed-tools: Bash(*)
            ---
            本文
        """).strip()
        result = validate_slash_command(Path("test.md"), content)
        assert not result.has_errors()
        assert len(result.warnings) == 1
        assert "Bash(*)" in result.warnings[0]

    def test_dangerous_command_without_disable(self):
        content = dedent("""
            ---
            description: 本番デプロイ
            ---
            deployコマンドを実行
        """).strip()
        result = validate_slash_command(Path("test.md"), content)
        assert not result.has_errors()
        assert any("disable-model-invocation" in w for w in result.warnings)

    def test_dangerous_command_with_disable(self):
        content = dedent("""
            ---
            description: 本番デプロイ
            disable-model-invocation: true
            ---
            deployコマンドを実行
        """).strip()
        result = validate_slash_command(Path("test.md"), content)
        assert not result.has_errors()
        assert not any("disable-model-invocation" in w for w in result.warnings)

    def test_invalid_model(self):
        content = dedent("""
            ---
            description: テスト
            model: invalid-model
            ---
            本文
        """).strip()
        result = validate_slash_command(Path("test.md"), content)
        assert any("model" in w for w in result.warnings)
