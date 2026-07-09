"""
統合テスト: validate_plugin.py のエンドツーエンドテスト
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from textwrap import dedent
from unittest.mock import patch

# validate_plugin.py を単体でインポートできるようにscriptsディレクトリをパスに追加
_scripts_dir = Path(__file__).parent.parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

import validate_plugin  # noqa: E402


class TestIntegration:
    """統合テスト"""

    def _run_validator(
        self, tool_name: str, file_path: str, file_content: str | None = None
    ) -> dict:
        """バリデーターを実行してJSON出力を取得"""
        # テスト用ファイルを作成
        if file_content is not None:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            Path(file_path).write_text(file_content, encoding="utf-8")

        hook_input = {"tool_name": tool_name, "tool_input": {"file_path": file_path}}

        scripts_dir = Path(__file__).parent.parent
        result = subprocess.run(
            [sys.executable, str(scripts_dir / "validate_plugin.py")],
            input=json.dumps(hook_input),
            capture_output=True,
            text=True,
            cwd=scripts_dir,
        )

        if result.stdout.strip():
            return json.loads(result.stdout)
        return {}

    def test_valid_skill_no_output(self):
        """正常なスキルファイルでは出力なし"""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = Path(tmpdir) / "skills" / "test" / "SKILL.md"
            content = dedent("""
                ---
                name: test-skill
                description: テストスキル。テスト時に使用する。
                ---
                スキル本文
            """).strip()

            result = self._run_validator("Write", str(skill_path), content)
            # 正常な場合は出力なし
            assert result == {} or not result.get("systemMessage")

    def test_invalid_skill_has_error(self):
        """無効なスキルファイルではエラーが出力される"""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = Path(tmpdir) / "skills" / "test" / "SKILL.md"
            content = dedent("""
                ---
                name: Invalid_Name
                ---
                本文
            """).strip()

            result = self._run_validator("Write", str(skill_path), content)
            assert "systemMessage" in result
            assert "エラー" in result["systemMessage"]

    def test_slash_command_validation(self):
        """スラッシュコマンドの検証"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cmd_path = Path(tmpdir) / "commands" / "test.md"
            content = dedent("""
                ---
                allowed-tools: Bash(*)
                ---
                本文
            """).strip()

            result = self._run_validator("Write", str(cmd_path), content)
            assert "systemMessage" in result
            # Bash(*)の警告があるはず
            assert "Bash(*)" in result["systemMessage"]

    def test_agent_validation(self):
        """サブエージェントの検証"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_path = Path(tmpdir) / "agents" / "test.md"
            content = dedent("""
                ---
                name: test-agent
                description: 短い
                ---
                本文
            """).strip()

            result = self._run_validator("Write", str(agent_path), content)
            assert "systemMessage" in result
            # 短いdescriptionの警告
            assert "短すぎ" in result["systemMessage"]

    def test_non_target_file_no_output(self):
        """対象外ファイルでは出力なし"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "random.txt"
            file_path.write_text("test content")

            result = self._run_validator("Write", str(file_path))
            assert result == {}

    def test_non_edit_write_tool_no_output(self):
        """Edit/Write以外のツールでは出力なし"""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = Path(tmpdir) / "skills" / "test" / "SKILL.md"
            content = dedent("""
                ---
                name: Invalid_Name
                ---
            """).strip()
            skill_path.parent.mkdir(parents=True, exist_ok=True)
            skill_path.write_text(content)

            result = self._run_validator("Read", str(skill_path))
            assert result == {}

    def test_continue_flag_is_true(self):
        """continueフラグが常にtrueであること"""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = Path(tmpdir) / "skills" / "test" / "SKILL.md"
            content = dedent("""
                ---
                name: Invalid_Name
                ---
            """).strip()

            result = self._run_validator("Write", str(skill_path), content)
            assert result.get("continue") is True

    def test_malformed_hooks_json_no_crash(self):
        """構造不正なhooks.json（配列であるべき箇所が文字列）でもクラッシュせずエラーを返す"""
        with tempfile.TemporaryDirectory() as tmpdir:
            hooks_path = Path(tmpdir) / "hooks" / "hooks.json"
            hooks_path.parent.mkdir(parents=True, exist_ok=True)
            hooks_path.write_text(
                json.dumps({"hooks": {"PreToolUse": "not-a-list"}}), encoding="utf-8"
            )

            hook_input = {
                "tool_name": "Write",
                "tool_input": {"file_path": str(hooks_path)},
            }
            scripts_dir = Path(__file__).parent.parent
            process = subprocess.run(
                [sys.executable, str(scripts_dir / "validate_plugin.py")],
                input=json.dumps(hook_input),
                capture_output=True,
                text=True,
                cwd=scripts_dir,
            )

            # Pythonのトレースバックでクラッシュせず、正常なJSON出力が返ること
            assert process.returncode == 0
            assert "Traceback" not in process.stderr
            result = json.loads(process.stdout)
            assert "systemMessage" in result
            assert "エラー" in result["systemMessage"]


class TestCLIMode:
    """CLIモードのテスト"""

    def _run_cli(self, *args: str) -> subprocess.CompletedProcess:
        """CLIモードでバリデーターを実行"""
        scripts_dir = Path(__file__).parent.parent
        return subprocess.run(
            [sys.executable, str(scripts_dir / "validate_plugin.py"), *args],
            capture_output=True,
            text=True,
            cwd=scripts_dir,
        )

    def test_cli_valid_file(self):
        """正常なファイルではexit code 0"""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = Path(tmpdir) / "skills" / "test" / "SKILL.md"
            skill_path.parent.mkdir(parents=True, exist_ok=True)
            skill_path.write_text(
                dedent("""
                ---
                name: test-skill
                description: テストスキル。テスト時に使用する。
                ---
                スキル本文
            """).strip()
            )

            result = self._run_cli(str(skill_path))
            assert result.returncode == 0

    def test_cli_invalid_file_error(self):
        """エラーのあるファイルではexit code 1"""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = Path(tmpdir) / "skills" / "test" / "SKILL.md"
            skill_path.parent.mkdir(parents=True, exist_ok=True)
            skill_path.write_text(
                dedent("""
                ---
                name: Invalid_Name
                ---
                本文
            """).strip()
            )

            result = self._run_cli(str(skill_path))
            assert result.returncode == 1
            assert "エラー" in result.stderr

    def test_cli_warning_without_strict(self):
        """--strictなしでは警告はexit code 0"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cmd_path = Path(tmpdir) / "commands" / "test.md"
            cmd_path.parent.mkdir(parents=True, exist_ok=True)
            # descriptionがない（警告のみ）
            cmd_path.write_text(
                dedent("""
                ---
                allowed-tools: Read
                ---
                本文があるのでdescription未設定は警告のみ
            """).strip()
            )

            result = self._run_cli(str(cmd_path))
            assert result.returncode == 0
            assert "警告" in result.stderr

    def test_cli_warning_with_strict(self):
        """--strictありでは警告もexit code 1"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cmd_path = Path(tmpdir) / "commands" / "test.md"
            cmd_path.parent.mkdir(parents=True, exist_ok=True)
            cmd_path.write_text(
                dedent("""
                ---
                allowed-tools: Read
                ---
                本文があるのでdescription未設定は警告のみ
            """).strip()
            )

            result = self._run_cli("--strict", str(cmd_path))
            assert result.returncode == 1

    def test_cli_multiple_files(self):
        """複数ファイルを一度に検証"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 正常なファイル
            valid_path = Path(tmpdir) / "skills" / "valid" / "SKILL.md"
            valid_path.parent.mkdir(parents=True, exist_ok=True)
            valid_path.write_text(
                dedent("""
                ---
                name: valid-skill
                description: 正常なスキル。テスト用。
                ---
                本文
            """).strip()
            )

            # エラーのあるファイル
            invalid_path = Path(tmpdir) / "skills" / "invalid" / "SKILL.md"
            invalid_path.parent.mkdir(parents=True, exist_ok=True)
            invalid_path.write_text(
                dedent("""
                ---
                name: Invalid_Name
                ---
                本文
            """).strip()
            )

            result = self._run_cli(str(valid_path), str(invalid_path))
            assert result.returncode == 1
            assert "Invalid_Name" in result.stderr or "invalid" in result.stderr.lower()

    def test_cli_non_target_file(self):
        """対象外ファイルはスキップされexit code 0"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "random.txt"
            file_path.write_text("test content")

            result = self._run_cli(str(file_path))
            assert result.returncode == 0

    def test_cli_malformed_hooks_json_no_crash(self):
        """構造不正なhooks.jsonをCLIモードで検証してもクラッシュせずexit code 1になる"""
        with tempfile.TemporaryDirectory() as tmpdir:
            hooks_path = Path(tmpdir) / "hooks" / "hooks.json"
            hooks_path.parent.mkdir(parents=True, exist_ok=True)
            hooks_path.write_text(
                json.dumps({"hooks": {"PreToolUse": "not-a-list"}}), encoding="utf-8"
            )

            result = self._run_cli(str(hooks_path))

            # Pythonのトレースバックでクラッシュせず、エラーメッセージが出力されること
            assert "Traceback" not in result.stderr
            assert result.returncode == 1
            assert "エラー" in result.stderr


class TestValidateFileExceptionIsolation:
    """validate_fileがバリデーター内部の例外を隔離することを確認する単体テスト"""

    def test_validator_exception_does_not_propagate(self):
        """validate_hooks_jsonが例外を送出してもvalidate_fileから伝播しない"""
        with tempfile.TemporaryDirectory() as tmpdir:
            hooks_path = Path(tmpdir) / "hooks.json"
            hooks_path.write_text(json.dumps({"hooks": {}}), encoding="utf-8")

            with patch.object(
                validate_plugin,
                "validate_hooks_json",
                side_effect=AttributeError("'str' object has no attribute 'get'"),
            ):
                result = validate_plugin.validate_file(hooks_path)

            assert result.has_errors()
            assert any("予期しないエラー" in e for e in result.errors)
