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

    def test_valid_context_fork(self):
        """context: forkが有効であることを確認"""
        content = dedent("""
            ---
            description: テストコマンド
            context: fork
            ---
            本文
        """).strip()
        result = validate_slash_command(Path("test.md"), content)
        assert not result.has_errors()

    def test_invalid_context(self):
        """無効なcontext値でエラーが出ることを確認"""
        content = dedent("""
            ---
            description: テストコマンド
            context: invalid
            ---
            本文
        """).strip()
        result = validate_slash_command(Path("test.md"), content)
        assert result.has_errors()
        assert any("context" in e for e in result.errors)

    def test_context_main_invalid(self):
        """context: mainは無効（forkのみサポート）"""
        content = dedent("""
            ---
            description: テストコマンド
            context: main
            ---
            本文
        """).strip()
        result = validate_slash_command(Path("test.md"), content)
        assert result.has_errors()
        assert any("context" in e and "fork" in e for e in result.errors)

    def test_agent_valid(self):
        """agentが空でない文字列であることを確認"""
        content = dedent("""
            ---
            description: テストコマンド
            agent: my-agent
            ---
            本文
        """).strip()
        result = validate_slash_command(Path("test.md"), content)
        assert not result.has_errors()

    def test_agent_empty_error(self):
        """agentが空の場合エラー"""
        content = dedent("""
            ---
            description: テストコマンド
            agent:
            ---
            本文
        """).strip()
        result = validate_slash_command(Path("test.md"), content)
        assert result.has_errors()
        assert any("agent" in e for e in result.errors)

    def test_allowed_tools_list_format(self):
        """allowed-toolsがリスト形式で指定できることを確認"""
        content = dedent("""
            ---
            description: テストコマンド
            allowed-tools:
              - Read
              - Write
              - Bash(git:*)
            ---
            本文
        """).strip()
        result = validate_slash_command(Path("test.md"), content)
        assert not result.has_errors()

    def test_allowed_tools_list_bash_wildcard_warning(self):
        """allowed-toolsリスト形式でBash(*)警告が出ることを確認"""
        content = dedent("""
            ---
            description: テストコマンド
            allowed-tools:
              - Read
              - Bash(*)
            ---
            本文
        """).strip()
        result = validate_slash_command(Path("test.md"), content)
        assert not result.has_errors()
        assert any("Bash(*)" in w for w in result.warnings)

    def test_valid_effort_low(self):
        """effort: lowが有効であることを確認（v2.1.80以降）"""
        content = dedent("""
            ---
            description: テストコマンド
            effort: low
            ---
            本文
        """).strip()
        result = validate_slash_command(Path("test.md"), content)
        assert not result.has_errors()
        assert not any("effort" in w for w in result.warnings)

    def test_valid_effort_normal(self):
        """effort: normalが有効であることを確認（v2.1.80以降）"""
        content = dedent("""
            ---
            description: テストコマンド
            effort: normal
            ---
            本文
        """).strip()
        result = validate_slash_command(Path("test.md"), content)
        assert not result.has_errors()
        assert not any("effort" in w for w in result.warnings)

    def test_valid_effort_high(self):
        """effort: highが有効であることを確認（v2.1.80以降）"""
        content = dedent("""
            ---
            description: テストコマンド
            effort: high
            ---
            本文
        """).strip()
        result = validate_slash_command(Path("test.md"), content)
        assert not result.has_errors()
        assert not any("effort" in w for w in result.warnings)

    def test_valid_argument_hint(self):
        """argument-hintが文字列で指定できることを確認"""
        content = dedent("""
            ---
            description: テストコマンド
            argument-hint: "[message]"
            ---
            本文
        """).strip()
        result = validate_slash_command(Path("test.md"), content)
        assert not result.has_errors()
        assert not any("argument-hint" in w for w in result.warnings)

    def test_argument_hint_empty_warning(self):
        """argument-hintが空の場合に警告"""
        content = dedent("""
            ---
            description: テストコマンド
            argument-hint:
            ---
            本文
        """).strip()
        result = validate_slash_command(Path("test.md"), content)
        assert any("argument-hint" in w for w in result.warnings)

    def test_invalid_effort(self):
        """無効なeffort値で警告が出ることを確認（v2.1.80以降）"""
        content = dedent("""
            ---
            description: テストコマンド
            effort: ultra
            ---
            本文
        """).strip()
        result = validate_slash_command(Path("test.md"), content)
        assert any("effort" in w for w in result.warnings)

    def test_description_yaml_bool_keyword_on(self):
        """descriptionに'on'がYAMLブール値キーワードとして警告される"""
        content = dedent("""
            ---
            description: on
            ---
            本文
        """).strip()
        result = validate_slash_command(Path("test.md"), content)
        assert any("YAML" in w or "ブール" in w for w in result.warnings)

    def test_description_yaml_bool_keyword_off(self):
        """descriptionに'off'がYAMLブール値キーワードとして警告される"""
        content = dedent("""
            ---
            description: off
            ---
            本文
        """).strip()
        result = validate_slash_command(Path("test.md"), content)
        assert any("YAML" in w or "ブール" in w for w in result.warnings)

    def test_description_yaml_bool_keyword_yes(self):
        """descriptionに'yes'がYAMLブール値キーワードとして警告される"""
        content = dedent("""
            ---
            description: yes
            ---
            本文
        """).strip()
        result = validate_slash_command(Path("test.md"), content)
        assert any("YAML" in w or "ブール" in w for w in result.warnings)

    def test_description_yaml_bool_keyword_quoted(self):
        """descriptionに'on'を引用符で囲めば警告されない"""
        content = dedent("""
            ---
            description: "on"
            ---
            本文
        """).strip()
        result = validate_slash_command(Path("test.md"), content)
        assert not any("ブール" in w for w in result.warnings)

    def test_description_yaml_bool_true_warns(self):
        """descriptionにtrue（引用符なし）が使われた場合に警告される"""
        content = dedent("""
            ---
            description: true
            ---
            本文
        """).strip()
        result = validate_slash_command(Path("test.md"), content)
        assert any("YAML" in w or "ブール" in w for w in result.warnings)

    def test_name_yaml_bool_keyword_warns(self):
        """nameにYAMLブール値キーワードが使われた場合に警告される"""
        content = dedent("""
            ---
            description: テストコマンド
            name: on
            ---
            本文
        """).strip()
        result = validate_slash_command(Path("test.md"), content)
        assert any("name" in w and "ブール" in w for w in result.warnings)

    def test_name_yaml_bool_keyword_quoted_no_warn(self):
        """nameに引用符付きYAMLブール値キーワードが使われた場合は警告されない"""
        content = dedent("""
            ---
            description: テストコマンド
            name: "on"
            ---
            本文
        """).strip()
        result = validate_slash_command(Path("test.md"), content)
        assert not any("name" in w and "ブール" in w for w in result.warnings)

    def test_no_frontmatter_no_bool_warning(self):
        """frontmatterがない（`---`で始まらない）場合はブール値警告が出ないことを確認"""
        content = "description: on\n本文のみ"
        result = validate_slash_command(Path("test.md"), content)
        assert not any("ブール" in w for w in result.warnings)

    def test_unclosed_frontmatter_no_bool_warning(self):
        """frontmatterの閉じ`---`がない場合はブール値警告が出ないことを確認"""
        content = dedent("""
            ---
            description: on
            name: off
            本文
        """).strip()
        result = validate_slash_command(Path("test.md"), content)
        assert not any("ブール" in w for w in result.warnings)
