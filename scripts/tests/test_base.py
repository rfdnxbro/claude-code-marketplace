"""
base.py のテスト
"""

from pathlib import Path
from textwrap import dedent

from scripts.validators.base import (
    WARNING_BROAD_BASH_WILDCARD,
    ValidationResult,
    add_yaml_warnings,
    normalize_path,
    parse_frontmatter,
    to_str,
    validate_agent_field,
    validate_allow_ask_glob_fields,
    validate_allowed_tools,
    validate_context_field,
    validate_effort_field,
    validate_string_or_list_field,
)


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

    def test_yaml_list_parse(self):
        """YAMLリスト形式がパースできることを確認"""
        content = dedent("""
            ---
            tools:
              - Read
              - Write
              - Bash(git:*)
            ---
        """).strip()
        fm, body, warnings = parse_frontmatter(content)
        assert "tools" in fm
        assert isinstance(fm["tools"], list)
        assert fm["tools"] == ["Read", "Write", "Bash(git:*)"]
        assert len(warnings) == 0

    def test_yaml_list_with_quoted_items(self):
        """クォート付きリストアイテムがパースできることを確認"""
        content = dedent("""
            ---
            allowed-tools:
              - "Bash(git add:*)"
              - 'Read'
            ---
        """).strip()
        fm, body, warnings = parse_frontmatter(content)
        assert "allowed-tools" in fm
        assert fm["allowed-tools"] == ["Bash(git add:*)", "Read"]

    def test_yaml_list_empty_key_no_items(self):
        """リスト開始後にアイテムがない場合"""
        content = dedent("""
            ---
            tools:
            name: test
            ---
        """).strip()
        fm, body, warnings = parse_frontmatter(content)
        # tools は空文字列として格納される（リストアイテムがなかったため）
        assert fm["tools"] == ""
        assert fm["name"] == "test"

    def test_yaml_list_orphan_item(self):
        """キーなしのリストアイテムで警告が出ることを確認"""
        content = dedent("""
            ---
            - orphan-item
            name: test
            ---
        """).strip()
        fm, body, warnings = parse_frontmatter(content)
        assert any("キーの後" in w for w in warnings)

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

    def test_inline_comment_after_value(self):
        """値の末尾のインラインコメントが除去されることを確認"""
        content = dedent("""
            ---
            model: sonnet # 説明のコメント
            ---
        """).strip()
        fm, body, warnings = parse_frontmatter(content)
        assert fm["model"] == "sonnet"

    def test_quoted_value_with_hash_inside(self):
        """クォート内のシャープ記号はコメントとして除去されないことを確認"""
        content = dedent("""
            ---
            description: "Use # to comment in bash"
            ---
        """).strip()
        fm, body, warnings = parse_frontmatter(content)
        assert fm["description"] == "Use # to comment in bash"

    def test_quoted_value_followed_by_inline_comment(self):
        """クォートされた値の後に続く本当のインラインコメントが除去されることを確認"""
        content = dedent("""
            ---
            description: "実際の値" # これはコメント
            ---
        """).strip()
        fm, body, warnings = parse_frontmatter(content)
        assert fm["description"] == "実際の値"

    def test_value_is_comment_only_becomes_list_key(self):
        """値がシャープ記号のみで始まる場合は空値としてリストキー扱いになることを確認"""
        content = dedent("""
            ---
            key: # comment only
            name: test
            ---
        """).strip()
        fm, body, warnings = parse_frontmatter(content)
        assert fm["key"] == ""
        assert fm["name"] == "test"

    def test_list_item_inline_comment_stripped(self):
        """リスト項目のインラインコメントが除去されることを確認"""
        content = dedent("""
            ---
            tools:
              - item1 # コメント
              - item2
            ---
        """).strip()
        fm, body, warnings = parse_frontmatter(content)
        assert fm["tools"] == ["item1", "item2"]

    def test_unclosed_quote_value_kept_as_is(self):
        """閉じクォートが見つからない場合は値全体をそのまま保持することを確認"""
        content = dedent("""
            ---
            description: "unterminated
            ---
        """).strip()
        fm, body, warnings = parse_frontmatter(content)
        assert fm["description"] == '"unterminated'

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


class TestToStr:
    """to_strのテスト"""

    def test_none(self):
        assert to_str(None) == ""

    def test_empty_string(self):
        assert to_str("") == ""

    def test_zero(self):
        assert to_str(0) == ""

    def test_false(self):
        assert to_str(False) == ""

    def test_normal_string(self):
        assert to_str("hello") == "hello"

    def test_integer(self):
        assert to_str(42) == "42"

    def test_true(self):
        assert to_str(True) == "True"


class TestAddYamlWarnings:
    """add_yaml_warningsのテスト"""

    def test_empty_warnings(self):
        result = ValidationResult()
        add_yaml_warnings(result, Path("test.md"), [])
        assert result.warnings == []

    def test_multiple_warnings(self):
        result = ValidationResult()
        add_yaml_warnings(result, Path("test.md"), ["警告1", "警告2"])
        assert len(result.warnings) == 2
        assert "test.md: 警告1" in result.warnings[0]
        assert "test.md: 警告2" in result.warnings[1]


class TestValidateContextField:
    """validate_context_fieldのテスト"""

    def test_not_specified(self):
        result = ValidationResult()
        validate_context_field(result, Path("test.md"), {})
        assert not result.has_errors()

    def test_fork_valid(self):
        result = ValidationResult()
        validate_context_field(result, Path("test.md"), {"context": "fork"})
        assert not result.has_errors()

    def test_invalid_value(self):
        result = ValidationResult()
        validate_context_field(result, Path("test.md"), {"context": "invalid"})
        assert result.has_errors()
        assert any("context" in e for e in result.errors)


class TestValidateAgentField:
    """validate_agent_fieldのテスト"""

    def test_not_specified(self):
        result = ValidationResult()
        validate_agent_field(result, Path("test.md"), {})
        assert not result.has_errors()

    def test_valid_agent(self):
        result = ValidationResult()
        validate_agent_field(result, Path("test.md"), {"agent": "my-agent"})
        assert not result.has_errors()

    def test_empty_agent(self):
        result = ValidationResult()
        validate_agent_field(result, Path("test.md"), {"agent": ""})
        assert result.has_errors()
        assert any("agent" in e for e in result.errors)


class TestValidateAllowedTools:
    """validate_allowed_toolsのテスト"""

    def test_not_specified(self):
        result = ValidationResult()
        validate_allowed_tools(result, Path("test.md"), {}, set())
        assert not result.has_errors()
        assert len(result.warnings) == 0

    def test_list_format(self):
        result = ValidationResult()
        fm = {"allowed-tools": ["Read", "Write"]}
        validate_allowed_tools(result, Path("test.md"), fm, set())
        assert len(result.warnings) == 0

    def test_bash_wildcard_warning(self):
        result = ValidationResult()
        fm = {"allowed-tools": "Bash(*)"}
        validate_allowed_tools(result, Path("test.md"), fm, set())
        assert any("Bash(*)" in w for w in result.warnings)

    def test_bash_wildcard_disabled(self):
        result = ValidationResult()
        fm = {"allowed-tools": "Bash(*)"}
        validate_allowed_tools(result, Path("test.md"), fm, {WARNING_BROAD_BASH_WILDCARD})
        assert len(result.warnings) == 0

    def test_param_value_syntax_accepted(self):
        """Tool(param:value)構文がエラーなしで受け入れられることを確認（v2.1.178以降）"""
        result = ValidationResult()
        fm = {"allowed-tools": ["Agent(model:opus)", "Bash(git:*)"]}
        validate_allowed_tools(result, Path("test.md"), fm, set())
        assert not result.has_errors()
        assert len(result.warnings) == 0


class TestValidateEffortField:
    """validate_effort_fieldのテスト"""

    def test_not_specified(self):
        result = ValidationResult()
        validate_effort_field(
            result, Path("test.md"), {}, ["low", "medium", "high", "xhigh", "max"]
        )
        assert not result.has_errors()
        assert len(result.warnings) == 0

    def test_valid_value(self):
        result = ValidationResult()
        validate_effort_field(
            result, Path("test.md"), {"effort": "low"}, ["low", "medium", "high", "xhigh", "max"]
        )
        assert not result.has_errors()
        assert len(result.warnings) == 0

    def test_invalid_value_warning(self):
        result = ValidationResult()
        validate_effort_field(
            result, Path("test.md"), {"effort": "ultra"}, ["low", "medium", "high", "xhigh", "max"]
        )
        assert any("effort" in w for w in result.warnings)

    def test_invalid_value_error(self):
        result = ValidationResult()
        validate_effort_field(
            result,
            Path("test.md"),
            {"effort": "ultra"},
            ["low", "medium", "high", "max"],
            level="error",
        )
        assert result.has_errors()
        assert any("effort" in e for e in result.errors)


class TestValidateStringOrListField:
    """validate_string_or_list_fieldのテスト"""

    def test_none_value(self):
        result = ValidationResult()
        validate_string_or_list_field(result, Path("test.md"), "tools", None)
        assert not result.has_errors()

    def test_string_value(self):
        result = ValidationResult()
        validate_string_or_list_field(result, Path("test.md"), "tools", "Read, Write")
        assert not result.has_errors()

    def test_valid_list(self):
        result = ValidationResult()
        validate_string_or_list_field(result, Path("test.md"), "tools", ["Read", "Write"])
        assert not result.has_errors()

    def test_list_with_empty_item(self):
        result = ValidationResult()
        validate_string_or_list_field(result, Path("test.md"), "tools", ["Read", ""])
        assert result.has_errors()
        assert any("tools" in e for e in result.errors)

    def test_invalid_type(self):
        result = ValidationResult()
        validate_string_or_list_field(result, Path("test.md"), "tools", 123)
        assert result.has_errors()
        assert any("文字列またはリスト" in e for e in result.errors)


class TestNormalizePath:
    """normalize_pathのテスト"""

    def test_strips_leading_and_trailing_slashes(self):
        assert normalize_path("/path/to/plugin/") == "path/to/plugin"

    def test_collapses_consecutive_slashes(self):
        assert normalize_path("path//to///plugin") == "path/to/plugin"

    def test_simple_path_unchanged(self):
        assert normalize_path("path/to/plugin") == "path/to/plugin"


class TestValidateAllowAskGlobFields:
    """validate_allow_ask_glob_fieldsのテスト（v2.1.166以降）"""

    def test_comma_separated_string_without_glob_valid(self):
        """allow/askがカンマ区切り文字列でグロブを含まない場合はエラーなし"""
        result = ValidationResult()
        validate_allow_ask_glob_fields(result, Path("SKILL.md"), {"allow": "Bash, Read"})
        assert not result.has_errors()

    def test_comma_separated_string_with_glob_error(self):
        """allow/askがカンマ区切り文字列でグロブを含む場合はエラー"""
        result = ValidationResult()
        validate_allow_ask_glob_fields(result, Path("SKILL.md"), {"ask": "Bash, Read*"})
        assert result.has_errors()
        assert any("グロブパターンは使用不可" in e for e in result.errors)

    def test_non_string_non_list_value_skipped(self):
        """allow/askがリストでも文字列でもない場合はスキップしエラーなし"""
        result = ValidationResult()
        validate_allow_ask_glob_fields(result, Path("SKILL.md"), {"allow": 123})
        assert not result.has_errors()
