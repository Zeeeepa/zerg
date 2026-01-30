"""Unit tests for performance analysis report formatters."""

from __future__ import annotations

import json
from io import StringIO

from rich.console import Console

from zerg.performance.formatters import (
    format_json,
    format_markdown,
    format_rich,
    format_sarif,
)
from zerg.performance.types import (
    CategoryScore,
    DetectedStack,
    PerformanceFinding,
    PerformanceReport,
    Severity,
    ToolStatus,
)

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _sample_finding(
    severity: Severity = Severity.MEDIUM,
    factor_id: int = 1,
    category: str = "TestCat",
) -> PerformanceFinding:
    return PerformanceFinding(
        factor_id=factor_id,
        factor_name="Test factor",
        category=category,
        severity=severity,
        message="A test finding",
        file="test.py",
        line=42,
        tool="test-tool",
        rule_id="TEST-001",
        suggestion="Fix the thing",
    )


def _sample_report(
    findings: list[PerformanceFinding] | None = None,
    overall_score: float | None = 85.0,
) -> PerformanceReport:
    if findings is None:
        findings = [_sample_finding()]
    return PerformanceReport(
        overall_score=overall_score,
        categories=[
            CategoryScore(
                category="TestCat",
                score=85.0 if findings else None,
                findings=findings,
                factors_checked=5,
                factors_total=10,
            ),
        ],
        tool_statuses=[
            ToolStatus(name="test-tool", available=True, version="1.0", factors_covered=5),
        ],
        findings=findings,
        factors_checked=5,
        factors_total=10,
        detected_stack=DetectedStack(
            languages=["python"],
            frameworks=["flask"],
            has_docker=True,
        ),
    )


def _empty_report() -> PerformanceReport:
    return PerformanceReport(
        overall_score=None,
        categories=[],
        tool_statuses=[],
        findings=[],
        factors_checked=0,
        factors_total=0,
        detected_stack=DetectedStack(languages=[], frameworks=[]),
    )


# ===================================================================
# format_json
# ===================================================================


class TestFormatJson:
    """Tests for the JSON formatter."""

    def test_valid_json(self) -> None:
        """Output should be valid JSON with expected keys."""
        report = _sample_report()
        output = format_json(report)
        data = json.loads(output)

        assert "overall_score" in data
        assert "categories" in data
        assert "findings" in data
        assert data["overall_score"] == 85.0
        assert len(data["findings"]) == 1

    def test_empty_report(self) -> None:
        """Empty report produces valid JSON."""
        output = format_json(_empty_report())
        data = json.loads(output)

        assert data["overall_score"] is None
        assert data["findings"] == []
        assert data["categories"] == []


# ===================================================================
# format_sarif
# ===================================================================


class TestFormatSarif:
    """Tests for the SARIF formatter."""

    def test_valid_sarif_structure(self) -> None:
        """SARIF output should have correct structure."""
        report = _sample_report()
        output = format_sarif(report)
        data = json.loads(output)

        assert "$schema" in data
        assert data["version"] == "2.1.0"
        assert "runs" in data
        assert len(data["runs"]) == 1

        run = data["runs"][0]
        assert "tool" in run
        assert "results" in run
        assert "driver" in run["tool"]
        assert "rules" in run["tool"]["driver"]

    def test_sarif_rules_and_results(self) -> None:
        """SARIF should have matching rules and results."""
        report = _sample_report()
        output = format_sarif(report)
        data = json.loads(output)

        run = data["runs"][0]
        assert len(run["results"]) == 1
        assert len(run["tool"]["driver"]["rules"]) == 1

        result = run["results"][0]
        assert result["ruleId"] == "PERF-1"
        assert result["message"]["text"] == "A test finding"
        assert "locations" in result

    def test_empty_report(self) -> None:
        """Empty report produces valid SARIF."""
        output = format_sarif(_empty_report())
        data = json.loads(output)

        assert data["version"] == "2.1.0"
        assert data["runs"][0]["results"] == []


# ===================================================================
# format_markdown
# ===================================================================


class TestFormatMarkdown:
    """Tests for the Markdown formatter."""

    def test_contains_expected_headers(self) -> None:
        """Markdown should contain the expected sections."""
        report = _sample_report()
        output = format_markdown(report)

        assert "# Performance Analysis Report" in output
        assert "## Summary" in output
        assert "## Tool Availability" in output
        assert "## TestCat" in output

    def test_contains_severity_counts(self) -> None:
        """Markdown summary should show severity counts."""
        report = _sample_report()
        output = format_markdown(report)

        assert "Medium: 1" in output
        assert "Critical: 0" in output

    def test_contains_score(self) -> None:
        """Markdown should display the overall score."""
        report = _sample_report()
        output = format_markdown(report)

        assert "85/100" in output

    def test_empty_report(self) -> None:
        """Empty report produces valid markdown."""
        output = format_markdown(_empty_report())

        assert "# Performance Analysis Report" in output
        assert "N/A/100" in output
        assert "Total findings: 0" in output

    def test_detected_stack_in_summary(self) -> None:
        """Summary should include detected stack info."""
        report = _sample_report()
        output = format_markdown(report)

        assert "python" in output
        assert "flask" in output


# ===================================================================
# format_rich
# ===================================================================


class TestFormatRich:
    """Tests for the Rich console formatter."""

    def test_does_not_crash(self) -> None:
        """Rich formatting should not raise any exceptions."""
        report = _sample_report()
        console = Console(file=StringIO(), force_terminal=True)
        format_rich(report, console)
        output = console.file.getvalue()  # type: ignore[union-attr]
        assert len(output) > 0

    def test_empty_report_does_not_crash(self) -> None:
        """Empty report should not crash the Rich formatter."""
        report = _empty_report()
        console = Console(file=StringIO(), force_terminal=True)
        format_rich(report, console)
        output = console.file.getvalue()  # type: ignore[union-attr]
        assert len(output) > 0

    def test_multiple_findings(self) -> None:
        """Report with multiple findings should render without error."""
        findings = [
            _sample_finding(Severity.CRITICAL, factor_id=1),
            _sample_finding(Severity.HIGH, factor_id=2),
            _sample_finding(Severity.LOW, factor_id=3),
            _sample_finding(Severity.INFO, factor_id=4),
        ]
        report = _sample_report(findings=findings, overall_score=60.0)
        console = Console(file=StringIO(), force_terminal=True)
        format_rich(report, console)
        output = console.file.getvalue()  # type: ignore[union-attr]
        assert len(output) > 0

    def test_score_none(self) -> None:
        """Score of None should display N/A."""
        report = _sample_report(findings=[], overall_score=None)
        console = Console(file=StringIO(), force_terminal=True)
        format_rich(report, console)
        output = console.file.getvalue()  # type: ignore[union-attr]
        assert "N/A" in output
