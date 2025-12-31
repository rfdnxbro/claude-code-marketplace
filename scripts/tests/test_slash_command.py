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

    def test_valid_short_models(self):
        """短縮形のmodelが受け入れられることを確認"""
        for model in ["sonnet", "opus", "haiku"]:
            content = dedent(f"""
                ---
                description: テスト
                model: {model}
                ---
                本文
            """).strip()
            result = validate_slash_command(Path("test.md"), content)
            assert not result.has_errors(), f"model={model} でエラーが発生"
            assert not any("model" in w for w in result.warnings), f"model={model} で警告が発生"

    def test_inherit_not_allowed(self):
        """スラッシュコマンドではinheritは使用不可"""
        content = dedent("""
            ---
            description: テスト
            model: inherit
            ---
            本文
        """).strip()
        result = validate_slash_command(Path("test.md"), content)
        assert any("model" in w for w in result.warnings)

    def test_full_model_id_not_allowed(self):
        """完全なモデルIDは警告される"""
        content = dedent("""
            ---
            description: テスト
            model: claude-3-5-haiku-20241022
            ---
            本文
        """).strip()
        result = validate_slash_command(Path("test.md"), content)
        assert any("model" in w for w in result.warnings)

    def test_yaml_warning_nested(self):
        """YAMLのネスト構文で警告が出ることを確認"""
        content = dedent("""
            ---
            description: テスト
            options:
              key: value
            ---
            本文
        """).strip()
        result = validate_slash_command(Path("test.md"), content)
        assert any("ネスト" in w for w in result.warnings)

    def test_disable_dangerous_operation_warning(self):
        """validator-disableコメントでdangerous-operation警告をスキップ"""
        content = dedent("""
            ---
            description: API作成
            ---

            <!-- validator-disable dangerous-operation -->

            本番環境へdeployを実行します
        """).strip()
        result = validate_slash_command(Path("api.md"), content)
        assert not result.has_errors()
        # deployキーワードがあるが、スキップコメントにより警告なし
        assert not any("disable-model-invocation" in w for w in result.warnings)

    def test_dangerous_operation_warning_not_skipped_without_comment(self):
        """スキップコメントがなければ警告が出ることを確認"""
        content = dedent("""
            ---
            description: API作成
            ---

            本番環境へdeployを実行します
        """).strip()
        result = validate_slash_command(Path("api.md"), content)
        assert not result.has_errors()
        # スキップコメントがないので警告が出る
        assert any("disable-model-invocation" in w for w in result.warnings)

    def test_disable_broad_bash_wildcard_warning(self):
        """validator-disableコメントでbroad-bash-wildcard警告をスキップ"""
        content = dedent("""
            ---
            description: テスト
            allowed-tools: Bash(*)
            ---

            <!-- validator-disable broad-bash-wildcard -->

            任意のコマンドを実行
        """).strip()
        result = validate_slash_command(Path("test.md"), content)
        assert not result.has_errors()
        assert not any("Bash(*)" in w for w in result.warnings)
