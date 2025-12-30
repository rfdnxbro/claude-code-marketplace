"""
output_style.py のテスト
"""

from pathlib import Path
from textwrap import dedent

from scripts.validators.output_style import validate_output_style


class TestValidateOutputStyle:
    """出力スタイル検証のテスト"""

    def test_valid_output_style(self):
        content = dedent("""
            ---
            name: teaching-mode
            description: コーディング中に概念を説明する
            keep-coding-instructions: true
            ---
            # Teaching Mode

            実装時に詳しく説明してください。
        """).strip()
        result = validate_output_style(Path("teaching-mode.md"), content)
        assert not result.has_errors()
        assert len(result.warnings) == 0

    def test_minimal_valid_style(self):
        content = dedent("""
            ---
            description: 最小限のスタイル
            ---
            スタイル指示
        """).strip()
        result = validate_output_style(Path("minimal.md"), content)
        assert not result.has_errors()
        assert len(result.warnings) == 0

    def test_missing_body(self):
        content = dedent("""
            ---
            name: empty-style
            description: 説明
            ---
        """).strip()
        result = validate_output_style(Path("empty-style.md"), content)
        assert result.has_errors()
        assert any("本文" in e for e in result.errors)

    def test_missing_description_warning(self):
        content = dedent("""
            ---
            name: no-desc
            ---
            スタイル指示
        """).strip()
        result = validate_output_style(Path("no-desc.md"), content)
        assert not result.has_errors()
        assert any("description" in w for w in result.warnings)

    def test_name_mismatch_warning(self):
        content = dedent("""
            ---
            name: different-name
            description: 説明
            ---
            スタイル指示
        """).strip()
        result = validate_output_style(Path("actual-filename.md"), content)
        assert not result.has_errors()
        assert any("ファイル名が異なります" in w for w in result.warnings)

    def test_invalid_keep_coding_instructions(self):
        content = dedent("""
            ---
            name: test
            description: 説明
            keep-coding-instructions: yes
            ---
            スタイル指示
        """).strip()
        result = validate_output_style(Path("test.md"), content)
        assert result.has_errors()
        assert any("keep-coding-instructions" in e for e in result.errors)

    def test_keep_coding_instructions_false(self):
        content = dedent("""
            ---
            name: data-analysis
            description: データ分析用スタイル
            keep-coding-instructions: false
            ---
            データ分析アシスタントとして動作します。
        """).strip()
        result = validate_output_style(Path("data-analysis.md"), content)
        assert not result.has_errors()
        assert len(result.warnings) == 0

    def test_no_frontmatter(self):
        content = "スタイル指示のみ"
        result = validate_output_style(Path("no-frontmatter.md"), content)
        assert not result.has_errors()
        # descriptionがないので警告
        assert any("description" in w for w in result.warnings)

    def test_invalid_name_type(self):
        content = dedent("""
            ---
            name: 123
            description: 説明
            ---
            スタイル指示
        """).strip()
        result = validate_output_style(Path("test.md"), content)
        assert result.has_errors()
        assert any("nameは文字列" in e for e in result.errors)

    def test_invalid_description_type(self):
        content = dedent("""
            ---
            name: test
            description: true
            ---
            スタイル指示
        """).strip()
        result = validate_output_style(Path("test.md"), content)
        assert result.has_errors()
        assert any("descriptionは文字列" in e for e in result.errors)

    def test_empty_body_with_whitespace_only(self):
        content = dedent("""
            ---
            name: test
            description: 説明
            ---


        """).strip()
        result = validate_output_style(Path("test.md"), content)
        assert result.has_errors()
        assert any("本文" in e for e in result.errors)
