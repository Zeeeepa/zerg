"""Adaptive detail level module for ZERG.

Tracks file modification counts and task success rates to intelligently
reduce detail level for familiar areas of the codebase.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class AdaptiveMetrics:
    """Metrics tracked for adaptive detail decisions.

    Attributes:
        file_modifications: Count of modifications per file path.
        directory_successes: Count of successful tasks per directory.
        directory_failures: Count of failed tasks per directory.
        last_updated: ISO timestamp of last update.
    """

    file_modifications: dict[str, int] = field(default_factory=dict)
    directory_successes: dict[str, int] = field(default_factory=dict)
    directory_failures: dict[str, int] = field(default_factory=dict)
    last_updated: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary for serialization."""
        return {
            "file_modifications": self.file_modifications,
            "directory_successes": self.directory_successes,
            "directory_failures": self.directory_failures,
            "last_updated": self.last_updated,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AdaptiveMetrics:
        """Create metrics from dictionary."""
        return cls(
            file_modifications=data.get("file_modifications", {}),
            directory_successes=data.get("directory_successes", {}),
            directory_failures=data.get("directory_failures", {}),
            last_updated=data.get("last_updated", ""),
        )


@dataclass
class TaskInfo:
    """Minimal task info needed for adaptive detail decisions.

    Attributes:
        task_id: Unique task identifier.
        files: List of file paths the task will modify.
        directory: Primary directory for the task (derived from files).
    """

    task_id: str
    files: list[str] = field(default_factory=list)
    directory: str = ""

    def __post_init__(self) -> None:
        """Derive directory from files if not set."""
        if not self.directory and self.files:
            # Use the common parent directory of all files
            if len(self.files) == 1:
                self.directory = str(Path(self.files[0]).parent)
            else:
                paths = [Path(f) for f in self.files]
                # Find common parent
                try:
                    common = Path(*[p for p in paths[0].parts if all(p in path.parts for path in paths)])
                    self.directory = str(common) if common.parts else str(paths[0].parent)
                except (TypeError, IndexError):
                    self.directory = str(paths[0].parent)


class AdaptiveDetailTracker:
    """Tracks metrics and determines when to reduce detail level.

    The tracker persists state to `.zerg/state/adaptive-detail.json` and
    provides the `should_reduce_detail` method to determine if a task
    should use reduced detail based on file familiarity and success rates.

    Attributes:
        state_path: Path to the state file.
        familiarity_threshold: Number of modifications before reducing detail.
        success_threshold: Success rate threshold (0.0-1.0) before reducing detail.
        metrics: Current adaptive metrics.
    """

    DEFAULT_STATE_PATH = Path(".zerg/state/adaptive-detail.json")
    DEFAULT_FAMILIARITY_THRESHOLD = 3
    DEFAULT_SUCCESS_THRESHOLD = 0.8

    def __init__(
        self,
        state_path: Path | str | None = None,
        familiarity_threshold: int | None = None,
        success_threshold: float | None = None,
        config: Any | None = None,
    ) -> None:
        """Initialize the adaptive detail tracker.

        Args:
            state_path: Path to persist state. Defaults to .zerg/state/adaptive-detail.json.
            familiarity_threshold: Number of modifications before reducing detail.
            success_threshold: Success rate threshold (0.0-1.0) for reducing detail.
            config: Optional ZergConfig with planning.adaptive_* settings.
        """
        self.state_path = Path(state_path) if state_path else self.DEFAULT_STATE_PATH

        # Extract thresholds from config if available
        if config is not None:
            planning = getattr(config, "planning", None)
            if planning is not None:
                familiarity_threshold = familiarity_threshold or getattr(
                    planning, "adaptive_familiarity_threshold", None
                )
                success_threshold = success_threshold or getattr(planning, "adaptive_success_threshold", None)

        self.familiarity_threshold = (
            familiarity_threshold if familiarity_threshold is not None else self.DEFAULT_FAMILIARITY_THRESHOLD
        )
        self.success_threshold = success_threshold if success_threshold is not None else self.DEFAULT_SUCCESS_THRESHOLD

        self.metrics = self._load_metrics()

    def _load_metrics(self) -> AdaptiveMetrics:
        """Load metrics from state file.

        Returns:
            AdaptiveMetrics loaded from file or fresh instance.
        """
        if not self.state_path.exists():
            return AdaptiveMetrics()

        try:
            with open(self.state_path) as f:
                data = json.load(f)
            return AdaptiveMetrics.from_dict(data)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to load adaptive metrics: {e}")
            return AdaptiveMetrics()

    def _save_metrics(self) -> None:
        """Save metrics to state file."""
        self.metrics.last_updated = datetime.now(UTC).isoformat()

        # Ensure directory exists
        self.state_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(self.state_path, "w") as f:
                json.dump(self.metrics.to_dict(), f, indent=2)
        except OSError as e:
            logger.error(f"Failed to save adaptive metrics: {e}")

    def record_file_modification(self, file_path: str) -> None:
        """Record a file modification.

        Args:
            file_path: Path to the modified file.
        """
        normalized = str(Path(file_path))
        self.metrics.file_modifications[normalized] = self.metrics.file_modifications.get(normalized, 0) + 1
        self._save_metrics()

    def record_task_result(self, task: TaskInfo, success: bool) -> None:
        """Record a task completion result.

        Args:
            task: TaskInfo with directory information.
            success: Whether the task succeeded.
        """
        directory = task.directory or "."
        if success:
            self.metrics.directory_successes[directory] = self.metrics.directory_successes.get(directory, 0) + 1
        else:
            self.metrics.directory_failures[directory] = self.metrics.directory_failures.get(directory, 0) + 1

        # Also record file modifications for successful tasks
        if success:
            for file_path in task.files:
                self.record_file_modification(file_path)
        else:
            self._save_metrics()

    def get_file_modification_count(self, file_path: str) -> int:
        """Get the modification count for a file.

        Args:
            file_path: Path to the file.

        Returns:
            Number of times the file has been modified.
        """
        normalized = str(Path(file_path))
        return self.metrics.file_modifications.get(normalized, 0)

    def get_directory_success_rate(self, directory: str) -> float:
        """Get the success rate for a directory.

        Args:
            directory: Directory path.

        Returns:
            Success rate as float (0.0-1.0), or 0.0 if no tasks.
        """
        successes = self.metrics.directory_successes.get(directory, 0)
        failures = self.metrics.directory_failures.get(directory, 0)
        total = successes + failures

        if total == 0:
            return 0.0
        return successes / total

    def should_reduce_detail(self, task: TaskInfo, metrics: AdaptiveMetrics | None = None) -> bool:
        """Determine if detail level should be reduced for a task.

        Reduces detail when:
        1. Any file in the task has been modified >= familiarity_threshold times, OR
        2. The task's directory has a success rate >= success_threshold

        Args:
            task: TaskInfo with files and directory.
            metrics: Optional metrics to use (defaults to self.metrics).

        Returns:
            True if detail should be reduced, False otherwise.
        """
        if metrics is None:
            metrics = self.metrics

        # Check file familiarity
        for file_path in task.files:
            normalized = str(Path(file_path))
            count = metrics.file_modifications.get(normalized, 0)
            if count >= self.familiarity_threshold:
                logger.debug(f"Reducing detail for {task.task_id}: file {file_path} modified {count} times")
                return True

        # Check directory success rate
        directory = task.directory or "."
        success_rate = self.get_directory_success_rate(directory)
        if success_rate >= self.success_threshold:
            total_tasks = metrics.directory_successes.get(directory, 0) + metrics.directory_failures.get(directory, 0)
            if total_tasks >= 2:  # Need at least 2 tasks for meaningful rate
                logger.debug(
                    f"Reducing detail for {task.task_id}: directory {directory} has {success_rate:.1%} success rate"
                )
                return True

        return False

    def reset_metrics(self) -> None:
        """Reset all metrics to initial state."""
        self.metrics = AdaptiveMetrics()
        self._save_metrics()

    def get_stats(self) -> dict[str, Any]:
        """Get summary statistics.

        Returns:
            Dictionary with summary statistics.
        """
        total_files = len(self.metrics.file_modifications)
        total_modifications = sum(self.metrics.file_modifications.values())
        total_successes = sum(self.metrics.directory_successes.values())
        total_failures = sum(self.metrics.directory_failures.values())
        total_tasks = total_successes + total_failures

        return {
            "total_files_tracked": total_files,
            "total_modifications": total_modifications,
            "total_tasks": total_tasks,
            "overall_success_rate": total_successes / total_tasks if total_tasks > 0 else 0.0,
            "directories_tracked": len(
                set(self.metrics.directory_successes.keys()) | set(self.metrics.directory_failures.keys())
            ),
            "familiarity_threshold": self.familiarity_threshold,
            "success_threshold": self.success_threshold,
            "last_updated": self.metrics.last_updated,
        }
