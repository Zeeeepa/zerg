"""Comprehensive tests for ZERG adaptive detail module."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from zerg.adaptive_detail import (
    AdaptiveDetailTracker,
    AdaptiveMetrics,
    TaskInfo,
)


class TestAdaptiveMetrics:
    """Tests for AdaptiveMetrics dataclass."""

    def test_default_values(self) -> None:
        """Test default metric values."""
        metrics = AdaptiveMetrics()
        assert metrics.file_modifications == {}
        assert metrics.directory_successes == {}
        assert metrics.directory_failures == {}
        assert metrics.last_updated == ""

    def test_to_dict(self) -> None:
        """Test to_dict serialization."""
        metrics = AdaptiveMetrics(
            file_modifications={"src/main.py": 5, "src/utils.py": 2},
            directory_successes={"src": 10},
            directory_failures={"src": 2},
            last_updated="2026-02-04T10:00:00",
        )
        data = metrics.to_dict()

        assert data["file_modifications"] == {"src/main.py": 5, "src/utils.py": 2}
        assert data["directory_successes"] == {"src": 10}
        assert data["directory_failures"] == {"src": 2}
        assert data["last_updated"] == "2026-02-04T10:00:00"

    def test_from_dict(self) -> None:
        """Test from_dict deserialization."""
        data = {
            "file_modifications": {"src/main.py": 3},
            "directory_successes": {"src": 5},
            "directory_failures": {"src": 1},
            "last_updated": "2026-02-04T11:00:00",
        }
        metrics = AdaptiveMetrics.from_dict(data)

        assert metrics.file_modifications == {"src/main.py": 3}
        assert metrics.directory_successes == {"src": 5}
        assert metrics.directory_failures == {"src": 1}
        assert metrics.last_updated == "2026-02-04T11:00:00"

    def test_from_dict_missing_fields(self) -> None:
        """Test from_dict with missing fields uses defaults."""
        data = {"file_modifications": {"src/main.py": 1}}
        metrics = AdaptiveMetrics.from_dict(data)

        assert metrics.file_modifications == {"src/main.py": 1}
        assert metrics.directory_successes == {}
        assert metrics.directory_failures == {}
        assert metrics.last_updated == ""

    def test_from_dict_empty(self) -> None:
        """Test from_dict with empty dict."""
        metrics = AdaptiveMetrics.from_dict({})
        assert metrics.file_modifications == {}
        assert metrics.directory_successes == {}

    def test_roundtrip(self) -> None:
        """Test to_dict/from_dict roundtrip preserves data."""
        original = AdaptiveMetrics(
            file_modifications={"a.py": 1, "b.py": 2},
            directory_successes={"src": 3},
            directory_failures={"tests": 1},
            last_updated="2026-02-04T12:00:00",
        )
        restored = AdaptiveMetrics.from_dict(original.to_dict())

        assert restored.file_modifications == original.file_modifications
        assert restored.directory_successes == original.directory_successes
        assert restored.directory_failures == original.directory_failures
        assert restored.last_updated == original.last_updated


class TestTaskInfo:
    """Tests for TaskInfo dataclass."""

    def test_basic_init(self) -> None:
        """Test basic TaskInfo initialization."""
        task = TaskInfo(task_id="TASK-001")
        assert task.task_id == "TASK-001"
        assert task.files == []
        assert task.directory == ""

    def test_with_files(self) -> None:
        """Test TaskInfo derives directory from files."""
        task = TaskInfo(task_id="TASK-001", files=["src/module/main.py"])
        assert task.directory == "src/module"

    def test_with_multiple_files_same_dir(self) -> None:
        """Test TaskInfo with multiple files in same directory."""
        task = TaskInfo(
            task_id="TASK-001",
            files=["src/main.py", "src/utils.py"],
        )
        # Should use common parent
        assert "src" in task.directory

    def test_with_explicit_directory(self) -> None:
        """Test TaskInfo with explicit directory."""
        task = TaskInfo(
            task_id="TASK-001",
            files=["src/main.py"],
            directory="custom/dir",
        )
        assert task.directory == "custom/dir"

    def test_empty_files_empty_dir(self) -> None:
        """Test TaskInfo with no files has empty directory."""
        task = TaskInfo(task_id="TASK-001", files=[])
        assert task.directory == ""


class TestAdaptiveDetailTracker:
    """Tests for AdaptiveDetailTracker class."""

    @pytest.fixture
    def temp_state_path(self, tmp_path: Path) -> Path:
        """Create a temporary state path."""
        return tmp_path / ".zerg" / "state" / "adaptive-detail.json"

    @pytest.fixture
    def tracker(self, temp_state_path: Path) -> AdaptiveDetailTracker:
        """Create a tracker with temporary state path."""
        return AdaptiveDetailTracker(state_path=temp_state_path)

    def test_default_init(self, temp_state_path: Path) -> None:
        """Test default initialization."""
        tracker = AdaptiveDetailTracker(state_path=temp_state_path)
        assert tracker.familiarity_threshold == 3
        assert tracker.success_threshold == 0.8
        assert tracker.metrics.file_modifications == {}

    def test_custom_thresholds(self, temp_state_path: Path) -> None:
        """Test initialization with custom thresholds."""
        tracker = AdaptiveDetailTracker(
            state_path=temp_state_path,
            familiarity_threshold=5,
            success_threshold=0.9,
        )
        assert tracker.familiarity_threshold == 5
        assert tracker.success_threshold == 0.9

    def test_config_based_init(self, temp_state_path: Path) -> None:
        """Test initialization from config object."""
        mock_config = MagicMock()
        mock_config.planning.adaptive_familiarity_threshold = 10
        mock_config.planning.adaptive_success_threshold = 0.95

        tracker = AdaptiveDetailTracker(state_path=temp_state_path, config=mock_config)
        assert tracker.familiarity_threshold == 10
        assert tracker.success_threshold == 0.95

    def test_config_without_planning(self, temp_state_path: Path) -> None:
        """Test initialization with config missing planning section."""
        mock_config = MagicMock()
        mock_config.planning = None

        tracker = AdaptiveDetailTracker(state_path=temp_state_path, config=mock_config)
        # Should use defaults
        assert tracker.familiarity_threshold == 3
        assert tracker.success_threshold == 0.8

    def test_record_file_modification(self, tracker: AdaptiveDetailTracker) -> None:
        """Test recording file modifications."""
        tracker.record_file_modification("src/main.py")
        assert tracker.get_file_modification_count("src/main.py") == 1

        tracker.record_file_modification("src/main.py")
        assert tracker.get_file_modification_count("src/main.py") == 2

    def test_record_file_modification_normalizes_path(self, tracker: AdaptiveDetailTracker) -> None:
        """Test that file paths are normalized."""
        # Record with ./prefix - should be normalized
        tracker.record_file_modification("./src/main.py")
        # Both forms should find the same file
        assert tracker.get_file_modification_count("src/main.py") == 1
        assert tracker.get_file_modification_count("./src/main.py") == 1

    def test_record_task_result_success(self, tracker: AdaptiveDetailTracker) -> None:
        """Test recording successful task."""
        task = TaskInfo(task_id="TASK-001", files=["src/main.py"], directory="src")
        tracker.record_task_result(task, success=True)

        assert tracker.metrics.directory_successes.get("src") == 1
        assert tracker.get_file_modification_count("src/main.py") == 1

    def test_record_task_result_failure(self, tracker: AdaptiveDetailTracker) -> None:
        """Test recording failed task."""
        task = TaskInfo(task_id="TASK-001", files=["src/main.py"], directory="src")
        tracker.record_task_result(task, success=False)

        assert tracker.metrics.directory_failures.get("src") == 1
        # File modifications should NOT be recorded on failure
        assert tracker.get_file_modification_count("src/main.py") == 0

    def test_get_directory_success_rate_no_tasks(self, tracker: AdaptiveDetailTracker) -> None:
        """Test success rate with no tasks."""
        assert tracker.get_directory_success_rate("src") == 0.0

    def test_get_directory_success_rate_all_success(self, tracker: AdaptiveDetailTracker) -> None:
        """Test success rate with all successes."""
        tracker.metrics.directory_successes["src"] = 5
        assert tracker.get_directory_success_rate("src") == 1.0

    def test_get_directory_success_rate_mixed(self, tracker: AdaptiveDetailTracker) -> None:
        """Test success rate with mixed results."""
        tracker.metrics.directory_successes["src"] = 8
        tracker.metrics.directory_failures["src"] = 2
        assert tracker.get_directory_success_rate("src") == 0.8


class TestShouldReduceDetail:
    """Tests for should_reduce_detail method."""

    @pytest.fixture
    def tracker(self, tmp_path: Path) -> AdaptiveDetailTracker:
        """Create tracker with known thresholds."""
        return AdaptiveDetailTracker(
            state_path=tmp_path / "adaptive.json",
            familiarity_threshold=3,
            success_threshold=0.8,
        )

    def test_no_reduction_for_new_file(self, tracker: AdaptiveDetailTracker) -> None:
        """Test no reduction for files never modified."""
        task = TaskInfo(task_id="TASK-001", files=["src/new.py"])
        assert tracker.should_reduce_detail(task) is False

    def test_reduction_on_familiarity_threshold(self, tracker: AdaptiveDetailTracker) -> None:
        """Test reduction when file modification count reaches threshold."""
        # Record 3 modifications
        for _ in range(3):
            tracker.record_file_modification("src/main.py")

        task = TaskInfo(task_id="TASK-001", files=["src/main.py"])
        assert tracker.should_reduce_detail(task) is True

    def test_reduction_on_success_threshold(self, tracker: AdaptiveDetailTracker) -> None:
        """Test reduction when directory success rate reaches threshold."""
        # Record 8 successes and 2 failures (80% success rate)
        tracker.metrics.directory_successes["src"] = 8
        tracker.metrics.directory_failures["src"] = 2

        task = TaskInfo(task_id="TASK-001", files=["src/new.py"], directory="src")
        assert tracker.should_reduce_detail(task) is True

    def test_no_reduction_below_success_threshold(self, tracker: AdaptiveDetailTracker) -> None:
        """Test no reduction when success rate is below threshold."""
        tracker.metrics.directory_successes["src"] = 7
        tracker.metrics.directory_failures["src"] = 3  # 70% success rate

        task = TaskInfo(task_id="TASK-001", files=["src/new.py"], directory="src")
        assert tracker.should_reduce_detail(task) is False

    def test_no_reduction_with_single_task(self, tracker: AdaptiveDetailTracker) -> None:
        """Test no reduction with only one task in directory."""
        tracker.metrics.directory_successes["src"] = 1
        # Need at least 2 tasks for meaningful rate

        task = TaskInfo(task_id="TASK-001", files=["src/new.py"], directory="src")
        assert tracker.should_reduce_detail(task) is False

    def test_reduction_with_custom_metrics(self, tracker: AdaptiveDetailTracker) -> None:
        """Test should_reduce_detail with explicit metrics."""
        custom_metrics = AdaptiveMetrics(
            file_modifications={"src/main.py": 5},
        )
        task = TaskInfo(task_id="TASK-001", files=["src/main.py"])

        assert tracker.should_reduce_detail(task, metrics=custom_metrics) is True

    def test_any_file_over_threshold_triggers_reduction(self, tracker: AdaptiveDetailTracker) -> None:
        """Test that any file over threshold triggers reduction."""
        # Only one file over threshold
        tracker.metrics.file_modifications["src/familiar.py"] = 5
        tracker.metrics.file_modifications["src/new.py"] = 0

        task = TaskInfo(task_id="TASK-001", files=["src/new.py", "src/familiar.py"])
        assert tracker.should_reduce_detail(task) is True

    def test_uses_default_directory_when_empty(self, tracker: AdaptiveDetailTracker) -> None:
        """Test that empty directory defaults to '.'."""
        tracker.metrics.directory_successes["."] = 10
        task_info = TaskInfo(task_id="TASK-001", files=[], directory="")

        # Should check "." directory when task.directory is empty
        directory = task_info.directory or "."
        assert tracker.get_directory_success_rate(directory) == 1.0


class TestStatePersistence:
    """Tests for state persistence functionality."""

    @pytest.fixture
    def state_path(self, tmp_path: Path) -> Path:
        """Create a temporary state path."""
        return tmp_path / ".zerg" / "state" / "adaptive-detail.json"

    def test_save_creates_directory(self, state_path: Path) -> None:
        """Test that save creates parent directories."""
        tracker = AdaptiveDetailTracker(state_path=state_path)
        tracker.record_file_modification("test.py")

        assert state_path.exists()
        assert state_path.parent.exists()

    def test_save_writes_valid_json(self, state_path: Path) -> None:
        """Test that saved state is valid JSON."""
        tracker = AdaptiveDetailTracker(state_path=state_path)
        tracker.record_file_modification("test.py")
        # Record a task result to populate directory_successes
        task = TaskInfo(task_id="T1", files=["src/main.py"], directory="src")
        tracker.record_task_result(task, success=True)

        with open(state_path) as f:
            data = json.load(f)

        assert "file_modifications" in data
        assert data["file_modifications"]["test.py"] == 1
        assert data["directory_successes"]["src"] == 1

    def test_load_from_existing_state(self, state_path: Path) -> None:
        """Test loading from existing state file."""
        # Create initial state
        state_path.parent.mkdir(parents=True, exist_ok=True)
        initial_data = {
            "file_modifications": {"src/main.py": 10},
            "directory_successes": {"src": 20},
            "directory_failures": {},
            "last_updated": "2026-02-04T10:00:00",
        }
        with open(state_path, "w") as f:
            json.dump(initial_data, f)

        # Create tracker - should load existing state
        tracker = AdaptiveDetailTracker(state_path=state_path)

        assert tracker.get_file_modification_count("src/main.py") == 10
        assert tracker.metrics.directory_successes["src"] == 20

    def test_load_handles_corrupt_file(self, state_path: Path) -> None:
        """Test loading handles corrupt JSON gracefully."""
        state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(state_path, "w") as f:
            f.write("not valid json {{{")

        # Should not raise, should start with fresh metrics
        tracker = AdaptiveDetailTracker(state_path=state_path)
        assert tracker.metrics.file_modifications == {}

    def test_load_handles_missing_file(self, state_path: Path) -> None:
        """Test loading handles missing file."""
        # File doesn't exist
        tracker = AdaptiveDetailTracker(state_path=state_path)
        assert tracker.metrics.file_modifications == {}

    def test_persistence_roundtrip(self, state_path: Path) -> None:
        """Test full save/load roundtrip."""
        # Create tracker and add data
        tracker1 = AdaptiveDetailTracker(state_path=state_path)
        tracker1.record_file_modification("src/main.py")
        tracker1.record_file_modification("src/main.py")
        task = TaskInfo(task_id="T1", files=["src/utils.py"], directory="src")
        tracker1.record_task_result(task, success=True)

        # Create new tracker - should load saved state
        tracker2 = AdaptiveDetailTracker(state_path=state_path)

        assert tracker2.get_file_modification_count("src/main.py") == 2
        assert tracker2.get_file_modification_count("src/utils.py") == 1
        assert tracker2.metrics.directory_successes["src"] == 1

    def test_last_updated_timestamp(self, state_path: Path) -> None:
        """Test that last_updated is set on save."""
        tracker = AdaptiveDetailTracker(state_path=state_path)
        tracker.record_file_modification("test.py")

        with open(state_path) as f:
            data = json.load(f)

        assert data["last_updated"] != ""
        # Should be ISO format
        assert "T" in data["last_updated"]


class TestResetAndStats:
    """Tests for reset_metrics and get_stats methods."""

    @pytest.fixture
    def tracker(self, tmp_path: Path) -> AdaptiveDetailTracker:
        """Create tracker with some data."""
        tracker = AdaptiveDetailTracker(state_path=tmp_path / "adaptive.json")
        tracker.record_file_modification("a.py")
        tracker.record_file_modification("b.py")
        tracker.metrics.directory_successes["src"] = 5
        tracker.metrics.directory_failures["src"] = 1
        return tracker

    def test_reset_metrics(self, tracker: AdaptiveDetailTracker) -> None:
        """Test reset_metrics clears all data."""
        tracker.reset_metrics()

        assert tracker.metrics.file_modifications == {}
        assert tracker.metrics.directory_successes == {}
        assert tracker.metrics.directory_failures == {}

    def test_get_stats_basic(self, tracker: AdaptiveDetailTracker) -> None:
        """Test get_stats returns correct values."""
        stats = tracker.get_stats()

        assert stats["total_files_tracked"] == 2
        assert stats["total_modifications"] == 2
        assert stats["total_tasks"] == 6
        assert stats["overall_success_rate"] == pytest.approx(5 / 6)
        assert stats["directories_tracked"] == 1
        assert stats["familiarity_threshold"] == 3
        assert stats["success_threshold"] == 0.8

    def test_get_stats_empty(self, tmp_path: Path) -> None:
        """Test get_stats with no data."""
        tracker = AdaptiveDetailTracker(state_path=tmp_path / "adaptive.json")
        stats = tracker.get_stats()

        assert stats["total_files_tracked"] == 0
        assert stats["total_modifications"] == 0
        assert stats["total_tasks"] == 0
        assert stats["overall_success_rate"] == 0.0
        assert stats["directories_tracked"] == 0


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.fixture
    def tracker(self, tmp_path: Path) -> AdaptiveDetailTracker:
        """Create tracker for edge case testing."""
        return AdaptiveDetailTracker(
            state_path=tmp_path / "adaptive.json",
            familiarity_threshold=3,
            success_threshold=0.8,
        )

    def test_exactly_at_familiarity_threshold(self, tracker: AdaptiveDetailTracker) -> None:
        """Test behavior exactly at familiarity threshold."""
        for _ in range(3):  # Exactly threshold
            tracker.record_file_modification("src/main.py")

        task = TaskInfo(task_id="T1", files=["src/main.py"])
        assert tracker.should_reduce_detail(task) is True

    def test_one_below_familiarity_threshold(self, tracker: AdaptiveDetailTracker) -> None:
        """Test behavior one below familiarity threshold."""
        for _ in range(2):  # One below threshold
            tracker.record_file_modification("src/main.py")

        task = TaskInfo(task_id="T1", files=["src/main.py"])
        assert tracker.should_reduce_detail(task) is False

    def test_exactly_at_success_threshold(self, tracker: AdaptiveDetailTracker) -> None:
        """Test behavior exactly at success threshold (80%)."""
        tracker.metrics.directory_successes["src"] = 8
        tracker.metrics.directory_failures["src"] = 2  # 80% exactly

        task = TaskInfo(task_id="T1", files=["src/new.py"], directory="src")
        assert tracker.should_reduce_detail(task) is True

    def test_one_below_success_threshold(self, tracker: AdaptiveDetailTracker) -> None:
        """Test behavior one below success threshold."""
        tracker.metrics.directory_successes["src"] = 79
        tracker.metrics.directory_failures["src"] = 21  # 79%

        task = TaskInfo(task_id="T1", files=["src/new.py"], directory="src")
        assert tracker.should_reduce_detail(task) is False

    def test_special_characters_in_path(self, tracker: AdaptiveDetailTracker) -> None:
        """Test handling of special characters in file paths."""
        path = "src/my file (1).py"
        tracker.record_file_modification(path)
        assert tracker.get_file_modification_count(path) == 1

    def test_deep_nested_path(self, tracker: AdaptiveDetailTracker) -> None:
        """Test handling of deeply nested paths."""
        path = "src/a/b/c/d/e/f/main.py"
        tracker.record_file_modification(path)
        assert tracker.get_file_modification_count(path) == 1

    def test_task_with_no_directory_uses_dot(self, tracker: AdaptiveDetailTracker) -> None:
        """Test that task with no directory uses '.' for checking."""
        tracker.metrics.directory_successes["."] = 10

        task = TaskInfo(task_id="T1", files=[], directory="")
        rate = tracker.get_directory_success_rate(task.directory or ".")
        assert rate == 1.0
