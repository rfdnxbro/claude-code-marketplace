"""
base.py のテスト
"""

from pathlib import Path
from textwrap import dedent

from scripts.validators.base import (
    MarkdownValidationContext,
    ValidationResult,
    coerce_str,
    normalize_path,
    parse_frontmatter,
    validate_agent_ref_field,
    validate_allowed_tools_field,
    validate_bool_field,
    validate_context_field,
    validate_effort_field,
    validate_enum_field,
    validate_string_list_field,
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


class TestNormalizePath:
    """normalize_pathのテスト"""

    def test_strips_leading_and_trailing_slashes(self):
        assert normalize_path("/path/to/plugin/") == "path/to/plugin"

    def test_collapses_consecutive_slashes(self):
        assert normalize_path("path//to///plugin") == "path/to/plugin"

    def test_simple_path_unchanged(self):
        assert normalize_path("path/to/plugin") == "path/to/plugin"


class TestCoerceStr:
    """coerce_strのテスト"""

    def test_none(self):
        assert coerce_str(None) == ""

    def test_empty_string(self):
        assert coerce_str("") == ""

    def test_normal_string(self):
        assert coerce_str("hello") == "hello"

    def test_false_value(self):
        assert coerce_str(False) == ""

    def test_zero(self):
        assert coerce_str(0) == ""

    def test_integer(self):
        assert coerce_str(42) == "42"

    def test_true_value(self):
        assert coerce_str(True) == "True"


class TestMarkdownValidationContext:
    """MarkdownValidationContextのテスト"""

    def test_basic_setup(self):
        content = dedent("""
            ---
            name: test
            description: テスト
            ---
            本文
        """).strip()
        ctx = MarkdownValidationContext(Path("test.md"), content)
        assert ctx.frontmatter["name"] == "test"
        assert ctx.body.strip() == "本文"
        assert not ctx.result.has_errors()
        assert ctx.result.warnings == []
        assert ctx.disabled_warnings == set()

    def test_yaml_warnings_auto_added(self):
        content = dedent("""
            ---
            description: |
              複数行
            ---
        """).strip()
        ctx = MarkdownValidationContext(Path("test.md"), content)
        assert any("複数行" in w for w in ctx.result.warnings)

    def test_disabled_warnings_detected(self):
        content = dedent("""
            ---
            name: test
            ---
            <!-- validator-disable dangerous-operation -->
            本文
        """).strip()
        ctx = MarkdownValidationContext(Path("test.md"), content)
        assert "dangerous-operation" in ctx.disabled_warnings


class TestValidateEnumField:
    """validate_enum_fieldのテスト"""

    def test_valid_value(self):
        result = ValidationResult()
        fm = {"status": "active"}
        val = validate_enum_field(fm, "status", ["active", "inactive"], Path("t.md"), result)
        assert val == "active"
        assert not result.has_errors()

    def test_invalid_value_error(self):
        result = ValidationResult()
        fm = {"status": "unknown"}
        validate_enum_field(fm, "status", ["active", "inactive"], Path("t.md"), result)
        assert result.has_errors()
        assert "status" in result.errors[0]

    def test_invalid_value_warning(self):
        result = ValidationResult()
        fm = {"level": "ultra"}
        validate_enum_field(fm, "level", ["low", "high"], Path("t.md"), result, level="warning")
        assert not result.has_errors()
        assert len(result.warnings) == 1

    def test_missing_field(self):
        result = ValidationResult()
        fm = {}
        val = validate_enum_field(fm, "status", ["active"], Path("t.md"), result)
        assert val == ""
        assert not result.has_errors()

    def test_custom_label(self):
        result = ValidationResult()
        fm = {"model": "gpt4"}
        validate_enum_field(
            fm,
            "model",
            ["sonnet", "opus"],
            Path("t.md"),
            result,
            level="warning",
            label="sonnet/opus/haiku",
        )
        assert "sonnet/opus/haiku" in result.warnings[0]


class TestValidateBoolField:
    """validate_bool_fieldのテスト"""

    def test_true(self):
        result = ValidationResult()
        val = validate_bool_field({"flag": True}, "flag", Path("t.md"), result)
        assert val is True
        assert not result.has_errors()

    def test_false(self):
        result = ValidationResult()
        val = validate_bool_field({"flag": False}, "flag", Path("t.md"), result)
        assert val is False
        assert not result.has_errors()

    def test_non_bool(self):
        result = ValidationResult()
        validate_bool_field({"flag": "yes"}, "flag", Path("t.md"), result)
        assert result.has_errors()

    def test_missing(self):
        result = ValidationResult()
        val = validate_bool_field({}, "flag", Path("t.md"), result)
        assert val is None
        assert not result.has_errors()

    def test_custom_message(self):
        result = ValidationResult()
        validate_bool_field(
            {"flag": "yes"},
            "flag",
            Path("t.md"),
            result,
            message_suffix="true/falseで指定してください",
        )
        assert "true/false" in result.errors[0]


class TestValidateStringListField:
    """validate_string_list_fieldのテスト"""

    def test_string_value(self):
        result = ValidationResult()
        val = validate_string_list_field({"tools": "Read"}, "tools", Path("t.md"), result)
        assert val == "Read"
        assert not result.has_errors()

    def test_list_value(self):
        result = ValidationResult()
        val = validate_string_list_field(
            {"tools": ["Read", "Write"]}, "tools", Path("t.md"), result
        )
        assert val == ["Read", "Write"]
        assert not result.has_errors()

    def test_invalid_type(self):
        result = ValidationResult()
        validate_string_list_field({"tools": 42}, "tools", Path("t.md"), result)
        assert result.has_errors()

    def test_empty_list_item(self):
        result = ValidationResult()
        validate_string_list_field({"tools": ["Read", ""]}, "tools", Path("t.md"), result)
        assert result.has_errors()

    def test_missing(self):
        result = ValidationResult()
        val = validate_string_list_field({}, "tools", Path("t.md"), result)
        assert val is None
        assert not result.has_errors()


class TestValidateContextField:
    """validate_context_fieldのテスト"""

    def test_fork_valid(self):
        result = ValidationResult()
        validate_context_field({"context": "fork"}, Path("t.md"), result)
        assert not result.has_errors()

    def test_invalid_context(self):
        result = ValidationResult()
        validate_context_field({"context": "main"}, Path("t.md"), result)
        assert result.has_errors()
        assert "forkのみ有効" in result.errors[0]

    def test_missing_context(self):
        result = ValidationResult()
        validate_context_field({}, Path("t.md"), result)
        assert not result.has_errors()


class TestValidateAllowedToolsField:
    """validate_allowed_tools_fieldのテスト"""

    def test_no_tools(self):
        result = ValidationResult()
        validate_allowed_tools_field({}, Path("t.md"), result, set())
        assert not result.warnings

    def test_bash_wildcard_warning(self):
        result = ValidationResult()
        validate_allowed_tools_field(
            {"allowed-tools": ["Bash(*)", "Read"]}, Path("t.md"), result, set()
        )
        assert len(result.warnings) == 1
        assert "Bash(*)" in result.warnings[0]

    def test_bash_wildcard_disabled(self):
        result = ValidationResult()
        validate_allowed_tools_field(
            {"allowed-tools": "Bash(*)"}, Path("t.md"), result, {"broad-bash-wildcard"}
        )
        assert not result.warnings

    def test_string_format(self):
        result = ValidationResult()
        validate_allowed_tools_field(
            {"allowed-tools": "Bash(*), Read"}, Path("t.md"), result, set()
        )
        assert len(result.warnings) == 1


class TestValidateAgentRefField:
    """validate_agent_ref_fieldのテスト"""

    def test_valid_agent(self):
        result = ValidationResult()
        validate_agent_ref_field({"agent": "my-agent"}, Path("t.md"), result)
        assert not result.has_errors()

    def test_empty_agent(self):
        result = ValidationResult()
        validate_agent_ref_field({"agent": ""}, Path("t.md"), result)
        assert result.has_errors()

    def test_missing_agent(self):
        result = ValidationResult()
        validate_agent_ref_field({}, Path("t.md"), result)
        assert not result.has_errors()


class TestValidateEffortField:
    """validate_effort_fieldのテスト"""

    def test_valid_default(self):
        result = ValidationResult()
        validate_effort_field({"effort": "low"}, Path("t.md"), result)
        assert not result.warnings

    def test_invalid_default(self):
        result = ValidationResult()
        validate_effort_field({"effort": "max"}, Path("t.md"), result)
        assert len(result.warnings) == 1

    def test_custom_values(self):
        result = ValidationResult()
        validate_effort_field(
            {"effort": "max"}, Path("t.md"), result, valid_values=["low", "medium", "high", "max"]
        )
        assert not result.warnings

    def test_missing(self):
        result = ValidationResult()
        validate_effort_field({}, Path("t.md"), result)
        assert not result.warnings

    def test_error_level(self):
        result = ValidationResult()
        validate_effort_field({"effort": "invalid"}, Path("t.md"), result, level="error")
        assert result.has_errors()
