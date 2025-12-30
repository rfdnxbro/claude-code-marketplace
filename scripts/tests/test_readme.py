"""
readme.py のテスト
"""

from pathlib import Path
from textwrap import dedent

from scripts.validators.readme import validate_readme


class TestValidateReadme:
    """README.md検証のテスト"""

    def test_valid_readme_japanese(self):
        """日本語セクションを持つ有効なREADME"""
        content = dedent("""
            # プラグイン名

            ## 概要

            このプラグインは〜です。

            ## インストール

            ```bash
            claude plugin install example
            ```

            ## 使い方

            ```bash
            claude example
            ```
        """).strip()
        result = validate_readme(Path("README.md"), content)
        assert not result.has_errors()
        assert len(result.warnings) == 0

    def test_valid_readme_english(self):
        """英語セクションを持つ有効なREADME"""
        content = dedent("""
            # Plugin Name

            ## Overview

            This plugin does something.

            ## Installation

            ```bash
            claude plugin install example
            ```

            ## Usage

            ```bash
            claude example
            ```
        """).strip()
        result = validate_readme(Path("README.md"), content)
        assert not result.has_errors()
        assert len(result.warnings) == 0

    def test_valid_readme_mixed_language(self):
        """日本語・英語混合のセクション"""
        content = dedent("""
            # Plugin

            ## Overview

            説明

            ## インストール

            手順

            ## Usage

            使い方
        """).strip()
        result = validate_readme(Path("README.md"), content)
        assert not result.has_errors()

    def test_missing_overview_section(self):
        """概要セクションがない場合"""
        content = dedent("""
            # Plugin

            ## インストール

            手順

            ## 使い方

            使い方
        """).strip()
        result = validate_readme(Path("README.md"), content)
        assert result.has_errors()
        assert any("概要/Overview" in e for e in result.errors)

    def test_missing_installation_section(self):
        """インストールセクションがない場合"""
        content = dedent("""
            # Plugin

            ## 概要

            説明

            ## 使い方

            使い方
        """).strip()
        result = validate_readme(Path("README.md"), content)
        assert result.has_errors()
        assert any("インストール/Installation" in e for e in result.errors)

    def test_missing_usage_section(self):
        """使い方セクションがない場合"""
        content = dedent("""
            # Plugin

            ## 概要

            説明

            ## インストール

            手順
        """).strip()
        result = validate_readme(Path("README.md"), content)
        assert result.has_errors()
        assert any("使い方/Usage" in e for e in result.errors)

    def test_missing_all_sections(self):
        """すべての必須セクションがない場合"""
        content = dedent("""
            # Plugin

            Some content without proper sections.
        """).strip()
        result = validate_readme(Path("README.md"), content)
        assert result.has_errors()
        assert len(result.errors) == 3

    def test_case_insensitive_sections(self):
        """セクション名の大文字小文字を区別しない"""
        content = dedent("""
            # Plugin

            ## OVERVIEW

            説明

            ## INSTALLATION

            手順

            ## USAGE

            使い方
        """).strip()
        result = validate_readme(Path("README.md"), content)
        assert not result.has_errors()


class TestRelativeLinkCheck:
    """相対パスリンクチェックのテスト"""

    def test_valid_relative_link(self, tmp_path):
        """存在する相対リンク"""
        # テスト用ファイルを作成
        readme_path = tmp_path / "README.md"
        target_file = tmp_path / "docs" / "guide.md"
        target_file.parent.mkdir(parents=True)
        target_file.write_text("# Guide")

        content = dedent("""
            # Plugin

            ## 概要

            詳細は[ガイド](docs/guide.md)を参照。

            ## インストール

            手順

            ## 使い方

            使い方
        """).strip()
        readme_path.write_text(content)

        result = validate_readme(readme_path, content)
        assert not result.has_errors()

    def test_broken_relative_link(self, tmp_path):
        """存在しない相対リンク"""
        readme_path = tmp_path / "README.md"
        content = dedent("""
            # Plugin

            ## 概要

            詳細は[ガイド](docs/nonexistent.md)を参照。

            ## インストール

            手順

            ## 使い方

            使い方
        """).strip()
        readme_path.write_text(content)

        result = validate_readme(readme_path, content)
        assert result.has_errors()
        assert any("リンク切れ" in e for e in result.errors)

    def test_external_url_ignored(self):
        """外部URLはチェックしない"""
        content = dedent("""
            # Plugin

            ## 概要

            [Google](https://google.com)へのリンク。

            ## インストール

            手順

            ## 使い方

            使い方
        """).strip()
        result = validate_readme(Path("README.md"), content)
        # 外部リンクはリンク切れチェックの対象外
        link_errors = [e for e in result.errors if "リンク切れ" in e]
        assert len(link_errors) == 0

    def test_anchor_link_ignored(self):
        """アンカーリンクはチェックしない"""
        content = dedent("""
            # Plugin

            ## 概要

            [使い方へ](#使い方)

            ## インストール

            手順

            ## 使い方

            使い方
        """).strip()
        result = validate_readme(Path("README.md"), content)
        link_errors = [e for e in result.errors if "リンク切れ" in e]
        assert len(link_errors) == 0

    def test_broken_image_link(self, tmp_path):
        """存在しない画像リンク"""
        readme_path = tmp_path / "README.md"
        content = dedent("""
            # Plugin

            ## 概要

            ![スクリーンショット](images/screenshot.png)

            ## インストール

            手順

            ## 使い方

            使い方
        """).strip()
        readme_path.write_text(content)

        result = validate_readme(readme_path, content)
        assert result.has_errors()
        assert any("画像リンク切れ" in e for e in result.errors)

    def test_valid_image_link(self, tmp_path):
        """存在する画像リンク"""
        readme_path = tmp_path / "README.md"
        image_path = tmp_path / "images" / "screenshot.png"
        image_path.parent.mkdir(parents=True)
        image_path.write_bytes(b"fake image data")

        content = dedent("""
            # Plugin

            ## 概要

            ![スクリーンショット](images/screenshot.png)

            ## インストール

            手順

            ## 使い方

            使い方
        """).strip()
        readme_path.write_text(content)

        result = validate_readme(readme_path, content)
        assert not result.has_errors()

    def test_external_image_ignored(self):
        """外部画像URLはチェックしない"""
        content = dedent("""
            # Plugin

            ## 概要

            ![Badge](https://img.shields.io/badge/test-pass-green)

            ## インストール

            手順

            ## 使い方

            使い方
        """).strip()
        result = validate_readme(Path("README.md"), content)
        image_errors = [e for e in result.errors if "画像リンク切れ" in e]
        assert len(image_errors) == 0

    def test_link_with_anchor(self, tmp_path):
        """アンカー付きリンク（ファイル部分のみチェック）"""
        readme_path = tmp_path / "README.md"
        target_file = tmp_path / "docs" / "guide.md"
        target_file.parent.mkdir(parents=True)
        target_file.write_text("# Guide\n## Section")

        content = dedent("""
            # Plugin

            ## 概要

            詳細は[ガイド](docs/guide.md#section)を参照。

            ## インストール

            手順

            ## 使い方

            使い方
        """).strip()
        readme_path.write_text(content)

        result = validate_readme(readme_path, content)
        assert not result.has_errors()


class TestCodeBlockCheck:
    """コードブロック言語指定チェックのテスト"""

    def test_code_block_with_language(self):
        """言語指定ありのコードブロック"""
        content = dedent("""
            # Plugin

            ## 概要

            説明

            ## インストール

            ```bash
            echo "hello"
            ```

            ## 使い方

            ```python
            print("hello")
            ```
        """).strip()
        result = validate_readme(Path("README.md"), content)
        assert len(result.warnings) == 0

    def test_code_block_without_language(self):
        """言語指定なしのコードブロック"""
        content = dedent("""
            # Plugin

            ## 概要

            説明

            ## インストール

            ```
            echo "hello"
            ```

            ## 使い方

            使い方
        """).strip()
        result = validate_readme(Path("README.md"), content)
        assert any("言語指定がありません" in w for w in result.warnings)

    def test_multiple_code_blocks_without_language(self):
        """複数の言語指定なしコードブロック"""
        content = dedent("""
            # Plugin

            ## 概要

            説明

            ## インストール

            ```
            first block
            ```

            ## 使い方

            ```
            second block
            ```
        """).strip()
        result = validate_readme(Path("README.md"), content)
        # 2つの警告があるはず
        lang_warnings = [w for w in result.warnings if "言語指定がありません" in w]
        assert len(lang_warnings) == 2

    def test_inline_code_ignored(self):
        """インラインコードはチェックしない"""
        content = dedent("""
            # Plugin

            ## 概要

            `code`のようなインラインコードは問題ない。

            ## インストール

            手順

            ## 使い方

            使い方
        """).strip()
        result = validate_readme(Path("README.md"), content)
        assert len(result.warnings) == 0
