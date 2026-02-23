"""
agent.py のテスト
"""

from pathlib import Path
from textwrap import dedent

from scripts.validators.agent import validate_agent


class TestValidateAgent:
    """サブエージェント検証のテスト"""

    def test_valid_agent(self):
        content = dedent("""
            ---
            name: code-reviewer
            description: コードレビュー専門家。品質・セキュリティ・保守性を確認。
            model: sonnet
            ---
            システムプロンプト
        """).strip()
        result = validate_agent(Path("agent.md"), content)
        assert not result.has_errors()
        assert len(result.warnings) == 0

    def test_missing_name(self):
        content = dedent("""
            ---
            description: 説明
            ---
            本文
        """).strip()
        result = validate_agent(Path("agent.md"), content)
        assert result.has_errors()
        assert any("name" in e for e in result.errors)

    def test_invalid_name_format(self):
        content = dedent("""
            ---
            name: Code_Reviewer
            description: 説明があります
            ---
            本文
        """).strip()
        result = validate_agent(Path("agent.md"), content)
        assert result.has_errors()
        assert any("kebab-case" in e for e in result.errors)

    def test_missing_description(self):
        content = dedent("""
            ---
            name: test-agent
            ---
            本文
        """).strip()
        result = validate_agent(Path("agent.md"), content)
        assert result.has_errors()
        assert any("description" in e for e in result.errors)

    def test_short_description(self):
        content = dedent("""
            ---
            name: test-agent
            description: 短い
            ---
            本文
        """).strip()
        result = validate_agent(Path("agent.md"), content)
        assert not result.has_errors()
        assert any("短すぎ" in w for w in result.warnings)

    def test_invalid_model(self):
        content = dedent("""
            ---
            name: test-agent
            description: これは十分に長い説明です
            model: invalid-model
            ---
            本文
        """).strip()
        result = validate_agent(Path("agent.md"), content)
        assert any("model" in w for w in result.warnings)

    def test_invalid_permission_mode(self):
        content = dedent("""
            ---
            name: test-agent
            description: これは十分に長い説明です
            permissionMode: invalid
            ---
            本文
        """).strip()
        result = validate_agent(Path("agent.md"), content)
        assert result.has_errors()
        assert any("permissionMode" in e for e in result.errors)

    def test_empty_body_warning(self):
        content = dedent("""
            ---
            name: test-agent
            description: これは十分に長い説明です
            ---
        """).strip()
        result = validate_agent(Path("agent.md"), content)
        assert not result.has_errors()
        assert any("システムプロンプト" in w for w in result.warnings)

    def test_yaml_warning_multiline(self):
        """YAMLの複数行構文で警告が出ることを確認"""
        content = dedent("""
            ---
            name: test-agent
            description: |
              複数行の説明
            ---
            本文
        """).strip()
        result = validate_agent(Path("agent.md"), content)
        assert any("複数行" in w for w in result.warnings)

    def test_tools_string_format(self):
        """toolsが文字列形式で指定できることを確認"""
        content = dedent("""
            ---
            name: test-agent
            description: これは十分に長い説明です
            tools: Read, Grep, Glob
            ---
            本文
        """).strip()
        result = validate_agent(Path("agent.md"), content)
        assert not result.has_errors()

    def test_tools_list_format(self):
        """toolsがリスト形式で指定できることを確認"""
        content = dedent("""
            ---
            name: test-agent
            description: これは十分に長い説明です
            tools:
              - Read
              - Grep
              - Glob
            ---
            本文
        """).strip()
        result = validate_agent(Path("agent.md"), content)
        assert not result.has_errors()

    def test_tools_list_empty_item(self):
        """toolsリストに空アイテムがある場合エラー"""
        content = dedent("""
            ---
            name: test-agent
            description: これは十分に長い説明です
            tools:
              - Read
              -
            ---
            本文
        """).strip()
        result = validate_agent(Path("agent.md"), content)
        assert result.has_errors()
        assert any("tools" in e for e in result.errors)

    def test_disallowed_tools_string_format(self):
        """disallowedToolsが文字列形式で指定できることを確認"""
        content = dedent("""
            ---
            name: test-agent
            description: これは十分に長い説明です
            disallowedTools: Edit, Write
            ---
            本文
        """).strip()
        result = validate_agent(Path("agent.md"), content)
        assert not result.has_errors()

    def test_disallowed_tools_list_format(self):
        """disallowedToolsがリスト形式で指定できることを確認"""
        content = dedent("""
            ---
            name: test-agent
            description: これは十分に長い説明です
            disallowedTools:
              - Edit
              - Write
            ---
            本文
        """).strip()
        result = validate_agent(Path("agent.md"), content)
        assert not result.has_errors()

    def test_disallowed_tools_list_empty_item(self):
        """disallowedToolsリストに空アイテムがある場合エラー"""
        content = dedent("""
            ---
            name: test-agent
            description: これは十分に長い説明です
            disallowedTools:
              - Edit
              -
            ---
            本文
        """).strip()
        result = validate_agent(Path("agent.md"), content)
        assert result.has_errors()
        assert any("disallowedTools" in e for e in result.errors)

    def test_skills_string_format(self):
        """skillsが文字列形式で指定できることを確認"""
        content = dedent("""
            ---
            name: test-agent
            description: これは十分に長い説明です
            skills: skill-one, skill-two
            ---
            本文
        """).strip()
        result = validate_agent(Path("agent.md"), content)
        assert not result.has_errors()

    def test_skills_list_format(self):
        """skillsがリスト形式で指定できることを確認"""
        content = dedent("""
            ---
            name: test-agent
            description: これは十分に長い説明です
            skills:
              - skill-one
              - skill-two
            ---
            本文
        """).strip()
        result = validate_agent(Path("agent.md"), content)
        assert not result.has_errors()

    def test_skills_list_empty_item(self):
        """skillsリストに空アイテムがある場合エラー"""
        content = dedent("""
            ---
            name: test-agent
            description: これは十分に長い説明です
            skills:
              - skill-one
              -
            ---
            本文
        """).strip()
        result = validate_agent(Path("agent.md"), content)
        assert result.has_errors()
        assert any("skills" in e for e in result.errors)

    def test_tools_invalid_type(self):
        """toolsが文字列でもリストでもない場合エラー"""
        content = dedent("""
            ---
            name: test-agent
            description: これは十分に長い説明です
            tools: 123
            ---
            本文
        """).strip()
        result = validate_agent(Path("agent.md"), content)
        assert result.has_errors()
        assert any("tools" in e and "文字列またはリスト" in e for e in result.errors)

    def test_disallowed_tools_invalid_type(self):
        """disallowedToolsが文字列でもリストでもない場合エラー"""
        content = dedent("""
            ---
            name: test-agent
            description: これは十分に長い説明です
            disallowedTools: 456
            ---
            本文
        """).strip()
        result = validate_agent(Path("agent.md"), content)
        assert result.has_errors()
        assert any("disallowedTools" in e and "文字列またはリスト" in e for e in result.errors)

    def test_skills_invalid_type(self):
        """skillsが文字列でもリストでもない場合エラー"""
        content = dedent("""
            ---
            name: test-agent
            description: これは十分に長い説明です
            skills: 789
            ---
            本文
        """).strip()
        result = validate_agent(Path("agent.md"), content)
        assert result.has_errors()
        assert any("skills" in e and "文字列またはリスト" in e for e in result.errors)

    def test_task_agent_type_syntax_string_format(self):
        """Task(agent_type)構文が文字列形式で有効であることを確認"""
        content = dedent("""
            ---
            name: test-agent
            description: これは十分に長い説明です
            tools: Read, Grep, Task(code-reviewer)
            ---
            本文
        """).strip()
        result = validate_agent(Path("agent.md"), content)
        assert not result.has_errors()

    def test_task_agent_type_syntax_list_format(self):
        """Task(agent_type)構文がリスト形式で有効であることを確認"""
        content = dedent("""
            ---
            name: test-agent
            description: これは十分に長い説明です
            tools:
              - Read
              - Grep
              - Task(code-reviewer)
              - Task(test-runner)
            ---
            本文
        """).strip()
        result = validate_agent(Path("agent.md"), content)
        assert not result.has_errors()

    def test_task_agent_type_syntax_empty_parentheses(self):
        """Task()の括弧が空の場合に警告"""
        content = dedent("""
            ---
            name: test-agent
            description: これは十分に長い説明です
            tools: Read, Task()
            ---
            本文
        """).strip()
        result = validate_agent(Path("agent.md"), content)
        assert any("Task()" in w for w in result.warnings)

    def test_memory_valid_user_scope(self):
        """memory: userが有効であることを確認"""
        content = dedent("""
            ---
            name: test-agent
            description: これは十分に長い説明です
            memory: user
            ---
            本文
        """).strip()
        result = validate_agent(Path("agent.md"), content)
        assert not result.has_errors()

    def test_memory_valid_project_scope(self):
        """memory: projectが有効であることを確認"""
        content = dedent("""
            ---
            name: test-agent
            description: これは十分に長い説明です
            memory: project
            ---
            本文
        """).strip()
        result = validate_agent(Path("agent.md"), content)
        assert not result.has_errors()

    def test_memory_valid_local_scope(self):
        """memory: localが有効であることを確認"""
        content = dedent("""
            ---
            name: test-agent
            description: これは十分に長い説明です
            memory: local
            ---
            本文
        """).strip()
        result = validate_agent(Path("agent.md"), content)
        assert not result.has_errors()

    def test_memory_invalid_scope(self):
        """memory: に不正な値が指定された場合エラー"""
        content = dedent("""
            ---
            name: test-agent
            description: これは十分に長い説明です
            memory: global
            ---
            本文
        """).strip()
        result = validate_agent(Path("agent.md"), content)
        assert result.has_errors()
        assert any("memory" in e and "不正" in e for e in result.errors)

    def test_isolation_valid_worktree(self):
        """isolation: worktreeが有効であることを確認（v2.1.50以降）"""
        content = dedent("""
            ---
            name: test-agent
            description: これは十分に長い説明です
            isolation: worktree
            ---
            本文
        """).strip()
        result = validate_agent(Path("agent.md"), content)
        assert not result.has_errors()

    def test_isolation_invalid_value(self):
        """isolation: に不正な値が指定された場合エラー"""
        content = dedent("""
            ---
            name: test-agent
            description: これは十分に長い説明です
            isolation: container
            ---
            本文
        """).strip()
        result = validate_agent(Path("agent.md"), content)
        assert result.has_errors()
        assert any("isolation" in e and "不正" in e for e in result.errors)

    def test_background_valid_true(self):
        """background: trueが有効であることを確認"""
        content = dedent("""
            ---
            name: test-agent
            description: これは十分に長い説明です
            background: true
            ---
            本文
        """).strip()
        result = validate_agent(Path("agent.md"), content)
        assert not result.has_errors()

    def test_background_valid_false(self):
        """background: falseが有効であることを確認"""
        content = dedent("""
            ---
            name: test-agent
            description: これは十分に長い説明です
            background: false
            ---
            本文
        """).strip()
        result = validate_agent(Path("agent.md"), content)
        assert not result.has_errors()

    def test_background_invalid_string(self):
        """background: にブール値以外の文字列が指定された場合エラー"""
        content = dedent("""
            ---
            name: test-agent
            description: これは十分に長い説明です
            background: yes
            ---
            本文
        """).strip()
        result = validate_agent(Path("agent.md"), content)
        assert result.has_errors()
        assert any("background" in e for e in result.errors)

    def test_isolation_and_background_combined(self):
        """isolationとbackgroundを同時に指定できることを確認"""
        content = dedent("""
            ---
            name: test-agent
            description: これは十分に長い説明です
            isolation: worktree
            background: true
            ---
            本文
        """).strip()
        result = validate_agent(Path("agent.md"), content)
        assert not result.has_errors()
