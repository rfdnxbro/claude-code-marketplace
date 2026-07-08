"""
secret_detection.py のテスト
"""

from pathlib import Path

from scripts.validators.secret_detection import detect_hardcoded_secrets

from scripts.validators.base import ValidationResult


class TestDetectHardcodedSecrets:
    """detect_hardcoded_secretsのテスト"""

    def test_openai_api_key_detected(self):
        """OpenAI APIキーのハードコードを検出する"""
        content = '{"env": {"OPENAI_API_KEY": "sk-abcdefghijklmnopqrstuvwxyz123456"}}'
        result = ValidationResult()
        detect_hardcoded_secrets(result, Path(".mcp.json"), content)
        assert result.has_errors()
        assert any("OpenAI APIキー" in e for e in result.errors)

    def test_openai_api_key_proj_detected(self):
        """OpenAI APIキー（sk-proj-）のハードコードを検出する"""
        content = '{"env": {"OPENAI_API_KEY": "sk-proj-abcdefghijklmnopqrstuvwxyz123456"}}'
        result = ValidationResult()
        detect_hardcoded_secrets(result, Path(".mcp.json"), content)
        assert result.has_errors()
        assert any("OpenAI APIキー" in e for e in result.errors)

    def test_openai_api_key_placeholder_not_detected(self):
        """${VAR}形式のプレースホルダーは検出しない"""
        content = '{"env": {"OPENAI_API_KEY": "${OPENAI_API_KEY}"}}'
        result = ValidationResult()
        detect_hardcoded_secrets(result, Path(".mcp.json"), content)
        assert not result.has_errors()

    def test_github_token_detected(self):
        """GitHub Tokenのハードコードを検出する"""
        content = '{"env": {"GITHUB_TOKEN": "ghp_abcdefghijklmnopqrstuvwxyz1234"}}'
        result = ValidationResult()
        detect_hardcoded_secrets(result, Path(".mcp.json"), content)
        assert result.has_errors()
        assert any("GitHub Token" in e for e in result.errors)

    def test_github_token_variants_detected(self):
        """GitHub Tokenの各プレフィックス（gho_/ghu_/ghs_）を検出する"""
        for prefix in ("gho_", "ghu_", "ghs_"):
            content = f'{{"token": "{prefix}abcdefghijklmnopqrstuvwxyz1234"}}'
            result = ValidationResult()
            detect_hardcoded_secrets(result, Path(".mcp.json"), content)
            assert result.has_errors(), f"{prefix} should be detected"
            assert any("GitHub Token" in e for e in result.errors)

    def test_github_token_placeholder_not_detected(self):
        """${VAR}形式のプレースホルダーは検出しない"""
        content = '{"env": {"GITHUB_TOKEN": "${GITHUB_TOKEN}"}}'
        result = ValidationResult()
        detect_hardcoded_secrets(result, Path(".mcp.json"), content)
        assert not result.has_errors()

    def test_slack_token_detected(self):
        """Slack Tokenのハードコードを検出する"""
        content = '{"env": {"SLACK_TOKEN": "xoxb-1234567890-abcdefghij"}}'
        result = ValidationResult()
        detect_hardcoded_secrets(result, Path(".mcp.json"), content)
        assert result.has_errors()
        assert any("Slack Token" in e for e in result.errors)

    def test_slack_token_variants_detected(self):
        """Slack Tokenの各プレフィックス（xoxa-/xoxp-）を検出する"""
        for prefix in ("xoxa-", "xoxp-"):
            content = f'{{"token": "{prefix}1234567890-abcdefghij"}}'
            result = ValidationResult()
            detect_hardcoded_secrets(result, Path(".mcp.json"), content)
            assert result.has_errors(), f"{prefix} should be detected"
            assert any("Slack Token" in e for e in result.errors)

    def test_slack_token_placeholder_not_detected(self):
        """${VAR}形式のプレースホルダーは検出しない"""
        content = '{"env": {"SLACK_TOKEN": "${SLACK_TOKEN}"}}'
        result = ValidationResult()
        detect_hardcoded_secrets(result, Path(".mcp.json"), content)
        assert not result.has_errors()

    def test_aws_access_key_detected(self):
        """AWS Access Key IDのハードコードを検出する"""
        content = '{"env": {"AWS_ACCESS_KEY_ID": "AKIAIOSFODNN7EXAMPLE"}}'
        result = ValidationResult()
        detect_hardcoded_secrets(result, Path(".mcp.json"), content)
        assert result.has_errors()
        assert any("AWS Access Key ID" in e for e in result.errors)

    def test_aws_access_key_placeholder_not_detected(self):
        """${VAR}形式のプレースホルダーは検出しない"""
        content = '{"env": {"AWS_ACCESS_KEY_ID": "${AWS_ACCESS_KEY_ID}"}}'
        result = ValidationResult()
        detect_hardcoded_secrets(result, Path(".mcp.json"), content)
        assert not result.has_errors()

    def test_google_api_key_detected(self):
        """Google APIキーのハードコードを検出する"""
        content = '{"env": {"GOOGLE_API_KEY": "AIzaFAKEFAKEFAKEFAKEFAKEFAKEFAKEFAKEFAK"}}'
        result = ValidationResult()
        detect_hardcoded_secrets(result, Path(".mcp.json"), content)
        assert result.has_errors()
        assert any("Google APIキー" in e for e in result.errors)

    def test_google_api_key_placeholder_not_detected(self):
        """${VAR}形式のプレースホルダーは検出しない"""
        content = '{"env": {"GOOGLE_API_KEY": "${GOOGLE_API_KEY}"}}'
        result = ValidationResult()
        detect_hardcoded_secrets(result, Path(".mcp.json"), content)
        assert not result.has_errors()

    def test_google_api_key_ending_with_hyphen_detected(self):
        """鍵の末尾がハイフンの場合でも\\b境界判定に依存せず検出されることを確認"""
        key = "AIza" + "A" * 34 + "-"
        content = f'{{"env": {{"GOOGLE_API_KEY": "{key}"}}}}'
        result = ValidationResult()
        detect_hardcoded_secrets(result, Path(".mcp.json"), content)
        assert result.has_errors()
        assert any("Google APIキー" in e for e in result.errors)

    def test_no_secrets_no_errors(self):
        """機密情報がない場合はエラーなし"""
        content = '{"env": {"FOO": "${FOO:-bar}", "PATH": "/usr/local/bin"}}'
        result = ValidationResult()
        detect_hardcoded_secrets(result, Path(".mcp.json"), content)
        assert not result.has_errors()

    def test_error_message_mentions_var_placeholder(self):
        """エラーメッセージに${VAR}形式の案内が含まれる"""
        content = '{"env": {"OPENAI_API_KEY": "sk-abcdefghijklmnopqrstuvwxyz123456"}}'
        result = ValidationResult()
        detect_hardcoded_secrets(result, Path(".mcp.json"), content)
        assert any("${VAR}" in e for e in result.errors)
