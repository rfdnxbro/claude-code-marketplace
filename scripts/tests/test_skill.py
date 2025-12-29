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
