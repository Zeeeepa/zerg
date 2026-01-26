"""Tests for ZERG v2 Troubleshoot Command."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestTroubleshootPhase:
    """Tests for troubleshoot phase enumeration."""

    def test_phases_exist(self):
        """Test troubleshoot phases are defined."""
        from troubleshoot import TroubleshootPhase

        assert hasattr(TroubleshootPhase, "SYMPTOM")
        assert hasattr(TroubleshootPhase, "HYPOTHESIS")
        assert hasattr(TroubleshootPhase, "TEST")
        assert hasattr(TroubleshootPhase, "ROOT_CAUSE")


class TestTroubleshootConfig:
    """Tests for troubleshoot configuration."""

    def test_config_defaults(self):
        """Test TroubleshootConfig has sensible defaults."""
        from troubleshoot import TroubleshootConfig

        config = TroubleshootConfig()
        assert config.verbose is False

    def test_config_custom(self):
        """Test TroubleshootConfig with custom values."""
        from troubleshoot import TroubleshootConfig

        config = TroubleshootConfig(verbose=True, max_hypotheses=5)
        assert config.verbose is True
        assert config.max_hypotheses == 5


class TestHypothesis:
    """Tests for hypothesis model."""

    def test_hypothesis_creation(self):
        """Test Hypothesis can be created."""
        from troubleshoot import Hypothesis

        hyp = Hypothesis(
            description="Database connection timeout",
            likelihood="high",
            test_command="ping db.local",
        )
        assert hyp.description == "Database connection timeout"

    def test_hypothesis_to_dict(self):
        """Test Hypothesis serialization."""
        from troubleshoot import Hypothesis

        hyp = Hypothesis(
            description="Memory leak",
            likelihood="medium",
            test_command="top -l 1",
        )
        data = hyp.to_dict()
        assert data["likelihood"] == "medium"


class TestDiagnosticResult:
    """Tests for diagnostic results."""

    def test_result_creation(self):
        """Test DiagnosticResult can be created."""
        from troubleshoot import DiagnosticResult

        result = DiagnosticResult(
            symptom="Application crash",
            hypotheses=[],
            root_cause="Memory exhaustion",
            recommendation="Increase memory limit",
        )
        assert result.symptom == "Application crash"

    def test_result_has_root_cause(self):
        """Test DiagnosticResult root cause detection."""
        from troubleshoot import DiagnosticResult

        with_cause = DiagnosticResult(
            symptom="Error",
            hypotheses=[],
            root_cause="Found it",
            recommendation="Fix it",
        )
        assert with_cause.has_root_cause is True

        without = DiagnosticResult(
            symptom="Error",
            hypotheses=[],
            root_cause="",
            recommendation="",
        )
        assert without.has_root_cause is False


class TestErrorParser:
    """Tests for error message parsing."""

    def test_parser_creation(self):
        """Test ErrorParser can be created."""
        from troubleshoot import ErrorParser

        parser = ErrorParser()
        assert parser is not None

    def test_parser_python_error(self):
        """Test parsing Python error."""
        from troubleshoot import ErrorParser

        parser = ErrorParser()
        error = """Traceback (most recent call last):
  File "test.py", line 10, in <module>
    raise ValueError("test error")
ValueError: test error"""
        result = parser.parse(error)
        assert result.error_type == "ValueError"

    def test_parser_extract_file_line(self):
        """Test extracting file and line from error."""
        from troubleshoot import ErrorParser

        parser = ErrorParser()
        error = 'File "test.py", line 10'
        result = parser.parse(error)
        assert result.file == "test.py"
        assert result.line == 10


class TestStackTraceAnalyzer:
    """Tests for stack trace analysis."""

    def test_analyzer_creation(self):
        """Test StackTraceAnalyzer can be created."""
        from troubleshoot import StackTraceAnalyzer

        analyzer = StackTraceAnalyzer()
        assert analyzer is not None


class TestTroubleshootCommand:
    """Tests for TroubleshootCommand class."""

    def test_command_creation(self):
        """Test TroubleshootCommand can be created."""
        from troubleshoot import TroubleshootCommand

        cmd = TroubleshootCommand()
        assert cmd is not None

    def test_command_run_returns_result(self):
        """Test run returns DiagnosticResult."""
        from troubleshoot import DiagnosticResult, TroubleshootCommand

        cmd = TroubleshootCommand()
        result = cmd.run(error="test error", dry_run=True)
        assert isinstance(result, DiagnosticResult)

    def test_command_format_text(self):
        """Test text output format."""
        from troubleshoot import DiagnosticResult, TroubleshootCommand

        cmd = TroubleshootCommand()
        result = DiagnosticResult(
            symptom="App crash",
            hypotheses=[],
            root_cause="Memory issue",
            recommendation="Add more RAM",
        )
        output = cmd.format_result(result, format="text")
        assert "Troubleshoot" in output or "Diagnostic" in output

    def test_command_format_json(self):
        """Test JSON output format."""
        import json

        from troubleshoot import DiagnosticResult, TroubleshootCommand

        cmd = TroubleshootCommand()
        result = DiagnosticResult(
            symptom="Error",
            hypotheses=[],
            root_cause="Bug",
            recommendation="Fix",
        )
        output = cmd.format_result(result, format="json")
        data = json.loads(output)
        assert "symptom" in data
