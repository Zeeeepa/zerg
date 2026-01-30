"""ZERG performance analysis package — comprehensive performance auditing."""

from zerg.performance.aggregator import PerformanceAuditor
from zerg.performance.catalog import FactorCatalog
from zerg.performance.formatters import format_json, format_markdown, format_rich, format_sarif
from zerg.performance.stack_detector import detect_stack
from zerg.performance.tool_registry import ToolRegistry
from zerg.performance.types import (
    CategoryScore,
    DetectedStack,
    PerformanceFinding,
    PerformanceReport,
    Severity,
    ToolStatus,
)

__all__ = [
    "CategoryScore",
    "DetectedStack",
    "FactorCatalog",
    "PerformanceAuditor",
    "PerformanceFinding",
    "PerformanceReport",
    "Severity",
    "ToolRegistry",
    "ToolStatus",
    "detect_stack",
    "format_json",
    "format_markdown",
    "format_rich",
    "format_sarif",
]
