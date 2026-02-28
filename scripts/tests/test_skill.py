"""
skill.py のテスト
"""

from pathlib import Path
from textwrap import dedent

from scripts.validators.skill import validate_skill


class TestValidateSkill:
    """スキル検証のテスト"""

    def test_valid_skill(self):
        content = dedent("""
            ---
            name: processing-pdfs
            description: PDFファイルを処理する。ユーザーがPDFについて言及した時に使用。
            ---
            スキル本文
        """).strip()
        result = validate_skill(Path("SKILL.md"), content)
        assert not result.has_errors()
        assert len(result.warnings) == 0

    def test_missing_name(self):
        content = dedent("""
            ---
            description: 説明
            ---
            本文
        """).strip()
        result = validate_skill(Path("SKILL.md"), content)
        assert result.has_errors()
        assert any("name" in e for e in result.errors)

    def test_name_too_long(self):
        content = dedent(f"""
            ---
            name: {"a" * 65}
            description: 説明
            ---
            本文
        """).strip()
        result = validate_skill(Path("SKILL.md"), content)
        assert result.has_errors()
        assert any("64文字" in e for e in result.errors)

    def test_name_invalid_format(self):
        content = dedent("""
            ---
            name: Invalid_Name
            description: 説明
            ---
            本文
        """).strip()
        result = validate_skill(Path("SKILL.md"), content)
        assert result.has_errors()
        assert any("小文字" in e for e in result.errors)

    def test_name_reserved_word_claude(self):
        content = dedent("""
            ---
            name: my-claude-plugin
            description: 説明
            ---
            本文
        """).strip()
        result = validate_skill(Path("SKILL.md"), content)
        assert result.has_errors()
        assert any("予約語" in e for e in result.errors)

    def test_name_reserved_word_anthropic(self):
        content = dedent("""
            ---
            name: anthropic-helper
            description: 説明
            ---
            本文
        """).strip()
        result = validate_skill(Path("SKILL.md"), content)
        assert result.has_errors()
        assert any("予約語" in e for e in result.errors)

    def test_missing_description(self):
        content = dedent("""
            ---
            name: test-skill
            ---
            本文
        """).strip()
        result = validate_skill(Path("SKILL.md"), content)
        assert result.has_errors()
        assert any("description" in e for e in result.errors)

    def test_description_too_long(self):
        content = dedent(f"""
            ---
            name: test-skill
            description: {"あ" * 1025}
            ---
            本文
        """).strip()
        result = validate_skill(Path("SKILL.md"), content)
        assert result.has_errors()
        assert any("1024文字" in e for e in result.errors)

    def test_body_too_long(self):
        long_body = "\n".join([f"行 {i}" for i in range(501)])
        content = f"""---
name: test-skill
description: 説明
---
{long_body}"""
        result = validate_skill(Path("SKILL.md"), content)
        assert not result.has_errors()
        assert any("500行" in w for w in result.warnings)

    def test_yaml_warning_multiline(self):
        """YAMLの複数行構文で警告が出ることを確認"""
        content = dedent("""
            ---
            name: test-skill
            description: >
              折り畳み形式の説明
            ---
            本文
        """).strip()
        result = validate_skill(Path("SKILL.md"), content)
        assert any("複数行" in w for w in result.warnings)

    def test_valid_context_fork(self):
        """context: forkが有効であることを確認"""
        content = dedent("""
            ---
            name: test-skill
            description: テストスキルの説明
            context: fork
            ---
            本文
        """).strip()
        result = validate_skill(Path("SKILL.md"), content)
        assert not result.has_errors()

    def test_invalid_context(self):
        """無効なcontext値でエラーが出ることを確認"""
        content = dedent("""
            ---
            name: test-skill
            description: テストスキルの説明
            context: invalid
            ---
            本文
        """).strip()
        result = validate_skill(Path("SKILL.md"), content)
        assert result.has_errors()
        assert any("context" in e for e in result.errors)

    def test_context_main_invalid(self):
        """context: mainは無効（forkのみサポート）"""
        content = dedent("""
            ---
            name: test-skill
            description: テストスキルの説明
            context: main
            ---
            本文
        """).strip()
        result = validate_skill(Path("SKILL.md"), content)
        assert result.has_errors()
        assert any("context" in e and "fork" in e for e in result.errors)

    def test_user_invocable_boolean(self):
        """user-invocableがブール値であることを確認"""
        content = dedent("""
            ---
            name: test-skill
            description: テストスキルの説明
            user-invocable: true
            ---
            本文
        """).strip()
        result = validate_skill(Path("SKILL.md"), content)
        assert not result.has_errors()

    def test_user_invocable_invalid(self):
        """user-invocableがブール値でない場合エラー"""
        content = dedent("""
            ---
            name: test-skill
            description: テストスキルの説明
            user-invocable: yes
            ---
            本文
        """).strip()
        result = validate_skill(Path("SKILL.md"), content)
        assert result.has_errors()
        assert any("user-invocable" in e for e in result.errors)

    def test_agent_valid(self):
        """agentが空でない文字列であることを確認"""
        content = dedent("""
            ---
            name: test-skill
            description: テストスキルの説明
            agent: my-agent
            ---
            本文
        """).strip()
        result = validate_skill(Path("SKILL.md"), content)
        assert not result.has_errors()

    def test_agent_empty_error(self):
        """agentが空の場合エラー"""
        content = dedent("""
            ---
            name: test-skill
            description: テストスキルの説明
            agent:
            ---
            本文
        """).strip()
        result = validate_skill(Path("SKILL.md"), content)
        assert result.has_errors()
        assert any("agent" in e for e in result.errors)

    def test_allowed_tools_list_format(self):
        """allowed-toolsがリスト形式で指定できることを確認"""
        content = dedent("""
            ---
            name: test-skill
            description: テストスキルの説明
            allowed-tools:
              - Read
              - Write
              - Bash(git:*)
            ---
            本文
        """).strip()
        result = validate_skill(Path("SKILL.md"), content)
        assert not result.has_errors()

    def test_allowed_tools_list_bash_wildcard_warning(self):
        """allowed-toolsリスト形式でBash(*)警告が出ることを確認"""
        content = dedent("""
            ---
            name: test-skill
            description: テストスキルの説明
            allowed-tools:
              - Read
              - Bash(*)
            ---
            本文
        """).strip()
        result = validate_skill(Path("SKILL.md"), content)
        assert not result.has_errors()
        assert any("Bash(*)" in w for w in result.warnings)

    def test_hooks_warning(self):
        """hooksが設定されている場合に警告が出ることを確認"""
        content = dedent("""
            ---
            name: test-skill
            description: テストスキルの説明
            hooks: some-hooks
            ---
            本文
        """).strip()
        result = validate_skill(Path("SKILL.md"), content)
        assert not result.has_errors()
        assert any("hooks" in w for w in result.warnings)

    def test_allowed_tools_string_format(self):
        """allowed-toolsが文字列形式で指定できることを確認"""
        content = dedent("""
            ---
            name: test-skill
            description: テストスキルの説明
            allowed-tools: Read, Write, Grep
            ---
            本文
        """).strip()
        result = validate_skill(Path("SKILL.md"), content)
        assert not result.has_errors()

    def test_allowed_tools_string_bash_wildcard_warning(self):
        """allowed-tools文字列形式でBash(*)警告が出ることを確認"""
        content = dedent("""
            ---
            name: test-skill
            description: テストスキルの説明
            allowed-tools: Read, Bash(*)
            ---
            本文
        """).strip()
        result = validate_skill(Path("SKILL.md"), content)
        assert not result.has_errors()
        assert any("Bash(*)" in w for w in result.warnings)

    def test_valid_model_sonnet(self):
        """model: sonnetが有効であることを確認"""
        content = dedent("""
            ---
            name: test-skill
            description: テストスキルの説明
            model: sonnet
            ---
            本文
        """).strip()
        result = validate_skill(Path("SKILL.md"), content)
        assert not result.has_errors()
        assert not any("model" in w for w in result.warnings)

    def test_valid_model_opus(self):
        """model: opusが有効であることを確認"""
        content = dedent("""
            ---
            name: test-skill
            description: テストスキルの説明
            model: opus
            ---
            本文
        """).strip()
        result = validate_skill(Path("SKILL.md"), content)
        assert not result.has_errors()
        assert not any("model" in w for w in result.warnings)

    def test_valid_model_haiku(self):
        """model: haikuが有効であることを確認"""
        content = dedent("""
            ---
            name: test-skill
            description: テストスキルの説明
            model: haiku
            ---
            本文
        """).strip()
        result = validate_skill(Path("SKILL.md"), content)
        assert not result.has_errors()
        assert not any("model" in w for w in result.warnings)

    def test_invalid_model(self):
        """無効なmodel値で警告が出ることを確認"""
        content = dedent("""
            ---
            name: test-skill
            description: テストスキルの説明
            model: gpt-4
            ---
            本文
        """).strip()
        result = validate_skill(Path("SKILL.md"), content)
        assert any("model" in w for w in result.warnings)
