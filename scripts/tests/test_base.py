"""
base.py のテスト
"""

from textwrap import dedent

from scripts.validators.base import ValidationResult, parse_frontmatter


class TestValidationResult:
    """ValidationResultのテスト"""

    def test_initial_state(self):
        result = ValidationResult()
        assert not result.has_errors()
        assert result.errors == []
        assert result.warnings == []

    def test_add_error(self):
        result = ValidationResult()
        result.add_error("エラーメッセージ")
        assert result.has_errors()
        assert "エラーメッセージ" in result.errors

    def test_add_warning(self):
        result = ValidationResult()
        result.add_warning("警告メッセージ")
        assert not result.has_errors()
        assert "警告メッセージ" in result.warnings

    def test_to_message(self):
        result = ValidationResult()
        result.add_error("エラー1")
        result.add_warning("警告1")
        message = result.to_message()
        assert "エラー" in message
        assert "警告" in message


class TestParseFrontmatter:
    """parse_frontmatterのテスト"""

    def test_valid_frontmatter(self):
        content = dedent("""
            ---
            name: test
            description: テスト説明
            ---
            本文
        """).strip()
        fm, body, warnings = parse_frontmatter(content)
        assert fm["name"] == "test"
        assert fm["description"] == "テスト説明"
        assert body.strip() == "本文"
        assert len(warnings) == 0

    def test_no_frontmatter(self):
        content = "本文のみ"
        fm, body, warnings = parse_frontmatter(content)
        assert fm == {}
        assert body == "本文のみ"
        assert len(warnings) == 0

    def test_quoted_values(self):
        content = dedent("""
            ---
            name: "quoted-name"
            description: 'single quoted'
            ---
        """).strip()
        fm, body, warnings = parse_frontmatter(content)
        assert fm["name"] == "quoted-name"
        assert fm["description"] == "single quoted"

    def test_unclosed_frontmatter(self):
        content = dedent("""
            ---
            name: test
            本文（閉じタグなし）
        """).strip()
        fm, body, warnings = parse_frontmatter(content)
        assert fm == {}

    def test_boolean_conversion(self):
        content = dedent("""
            ---
            enabled: true
            disabled: false
            ---
        """).strip()
        fm, body, warnings = parse_frontmatter(content)
        assert fm["enabled"] is True
        assert fm["disabled"] is False

    def test_integer_conversion(self):
        content = dedent("""
            ---
            count: 42
            timeout: 30
            ---
        """).strip()
        fm, body, warnings = parse_frontmatter(content)
        assert fm["count"] == 42
        assert fm["timeout"] == 30

    def test_unsupported_multiline(self):
        content = dedent("""
            ---
            description: |
              複数行の説明
            ---
        """).strip()
        fm, body, warnings = parse_frontmatter(content)
        assert any("複数行" in w for w in warnings)

    def test_unsupported_list(self):
        content = dedent("""
            ---
            tools:
              - Read
              - Write
            ---
        """).strip()
        fm, body, warnings = parse_frontmatter(content)
        assert any("リスト" in w or "ネスト" in w for w in warnings)

    def test_comment_ignored(self):
        content = dedent("""
            ---
            # コメント行
            name: test
            ---
        """).strip()
        fm, body, warnings = parse_frontmatter(content)
        assert fm["name"] == "test"
        assert "#" not in fm

    def test_nested_object_warning(self):
        """ネストされたオブジェクトで警告が出ることを確認"""
        content = dedent("""
            ---
            env:
              KEY: value
            ---
        """).strip()
        fm, body, warnings = parse_frontmatter(content)
        assert any("ネスト" in w for w in warnings)
