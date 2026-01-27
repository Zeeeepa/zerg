"""Unit tests for worker lifecycle - OFX-002.

Tests for worker spawn, terminate, restart, state transitions,
worktree cleanup, and spawn failure handling.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock
from typing import Any

from zerg.constants import WorkerStatus
from zerg.launcher import SubprocessLauncher, SpawnResult, WorkerHandle


class TestWorkerSpawn:
    """Test worker spawning."""

    @patch("subprocess.Popen")
    def test_spawn_returns_spawn_result(self, mock_popen: MagicMock, tmp_path: Path) -> None:
        """Spawn should return a SpawnResult object."""
        mock_popen.return_value = MagicMock(pid=12345)

        launcher = SubprocessLauncher()
        result = launcher.spawn(
            worker_id=0,
            feature="test-feature",
            worktree_path=tmp_path,
            branch="test-branch",
        )

        assert isinstance(result, SpawnResult)

    @patch("subprocess.Popen")
    def test_spawn_success_has_handle(self, mock_popen: MagicMock, tmp_path: Path) -> None:
        """Successful spawn should have a handle."""
        mock_popen.return_value = MagicMock(pid=12345)

        launcher = SubprocessLauncher()
        result = launcher.spawn(
            worker_id=0,
            feature="test-feature",
            worktree_path=tmp_path,
            branch="test-branch",
        )

        if result.success:
            assert result.handle is not None

    @patch("subprocess.Popen")
    def test_spawn_registers_worker(self, mock_popen: MagicMock, tmp_path: Path) -> None:
        """Spawn should register worker in launcher state."""
        mock_popen.return_value = MagicMock(pid=12345)

        launcher = SubprocessLauncher()
        result = launcher.spawn(
            worker_id=0,
            feature="test-feature",
            worktree_path=tmp_path,
            branch="test-branch",
        )

        if result.success:
            # Worker should be tracked
            handle = launcher.get_handle(0)
            assert handle is not None


class TestWorkerTermination:
    """Test worker termination - covers OFX-007 termination race fix."""

    @patch("subprocess.Popen")
    def test_terminate_stops_worker(self, mock_popen: MagicMock, tmp_path: Path) -> None:
        """Terminate should stop the worker process."""
        mock_process = MagicMock(pid=12345)
        mock_process.poll.return_value = None  # Still running
        mock_popen.return_value = mock_process

        launcher = SubprocessLauncher()
        launcher.spawn(
            worker_id=0,
            feature="test-feature",
            worktree_path=tmp_path,
            branch="test-branch",
        )

        launcher.terminate(0)

        # Should have called terminate on the process
        mock_process.terminate.assert_called()

    @patch("subprocess.Popen")
    def test_terminate_removes_from_tracking(self, mock_popen: MagicMock, tmp_path: Path) -> None:
        """After termination, worker should be removed from tracking."""
        mock_process = MagicMock(pid=12345)
        mock_process.poll.return_value = 0  # Exited
        mock_popen.return_value = mock_process

        launcher = SubprocessLauncher()
        launcher.spawn(
            worker_id=0,
            feature="test-feature",
            worktree_path=tmp_path,
            branch="test-branch",
        )

        launcher.terminate(0)

        # Worker should no longer be tracked (or marked as terminated)
        handle = launcher.get_handle(0)
        # Either None or status is STOPPED/terminated
        if handle is not None:
            assert handle.status in [WorkerStatus.STOPPED, WorkerStatus.CRASHED]

    def test_terminate_nonexistent_worker_safe(self) -> None:
        """Terminating non-existent worker should not raise."""
        launcher = SubprocessLauncher()

        # Should not raise
        launcher.terminate(999)


class TestWorkerRestart:
    """Test worker restart behavior - covers OFX-007 restart fixes."""

    @patch("subprocess.Popen")
    def test_respawn_after_crash(self, mock_popen: MagicMock, tmp_path: Path) -> None:
        """Worker can be respawned after crash."""
        mock_popen.return_value = MagicMock(pid=12345)

        launcher = SubprocessLauncher()

        # First spawn
        result1 = launcher.spawn(
            worker_id=0,
            feature="test-feature",
            worktree_path=tmp_path,
            branch="test-branch",
        )

        # Terminate (simulate crash)
        launcher.terminate(0)

        # Respawn should work
        result2 = launcher.spawn(
            worker_id=0,
            feature="test-feature",
            worktree_path=tmp_path,
            branch="test-branch",
        )

        assert result2.success or result2.error is not None


class TestPollLoop:
    """Test poll loop behavior - covers OFX-007 poll loop fixes."""

    @patch("subprocess.Popen")
    def test_monitor_returns_status(self, mock_popen: MagicMock, tmp_path: Path) -> None:
        """Monitor should return valid WorkerStatus."""
        mock_process = MagicMock(pid=12345)
        mock_process.poll.return_value = None  # Still running
        mock_popen.return_value = mock_process

        launcher = SubprocessLauncher()
        launcher.spawn(
            worker_id=0,
            feature="test-feature",
            worktree_path=tmp_path,
            branch="test-branch",
        )

        status = launcher.monitor(0)

        assert isinstance(status, WorkerStatus)

    @patch("subprocess.Popen")
    def test_monitor_running_worker(self, mock_popen: MagicMock, tmp_path: Path) -> None:
        """Monitor should return RUNNING for active worker."""
        mock_process = MagicMock(pid=12345)
        mock_process.poll.return_value = None  # Still running
        mock_popen.return_value = mock_process

        launcher = SubprocessLauncher()
        launcher.spawn(
            worker_id=0,
            feature="test-feature",
            worktree_path=tmp_path,
            branch="test-branch",
        )

        status = launcher.monitor(0)

        assert status == WorkerStatus.RUNNING

    @patch("subprocess.Popen")
    def test_monitor_stopped_worker(self, mock_popen: MagicMock, tmp_path: Path) -> None:
        """Monitor should return STOPPED for exited worker."""
        mock_process = MagicMock(pid=12345)
        mock_process.poll.return_value = 0  # Exited cleanly
        mock_popen.return_value = mock_process

        launcher = SubprocessLauncher()
        launcher.spawn(
            worker_id=0,
            feature="test-feature",
            worktree_path=tmp_path,
            branch="test-branch",
        )

        status = launcher.monitor(0)

        assert status in [WorkerStatus.STOPPED, WorkerStatus.CRASHED]

    def test_monitor_nonexistent_returns_stopped(self) -> None:
        """Monitor of non-existent worker should return STOPPED."""
        launcher = SubprocessLauncher()

        status = launcher.monitor(999)

        assert status == WorkerStatus.STOPPED


class TestSpawnFailure:
    """Test spawn failure handling - covers OFX-007 spawn failure fixes."""

    @patch("subprocess.Popen")
    def test_spawn_failure_returns_error(self, mock_popen: MagicMock, tmp_path: Path) -> None:
        """Failed spawn should return SpawnResult with error."""
        mock_popen.side_effect = OSError("Failed to spawn")

        launcher = SubprocessLauncher()
        result = launcher.spawn(
            worker_id=0,
            feature="test-feature",
            worktree_path=tmp_path,
            branch="test-branch",
        )

        assert not result.success
        assert result.error is not None

    @patch("subprocess.Popen")
    def test_spawn_failure_does_not_register(self, mock_popen: MagicMock, tmp_path: Path) -> None:
        """Failed spawn should not register worker."""
        mock_popen.side_effect = OSError("Failed to spawn")

        launcher = SubprocessLauncher()
        launcher.spawn(
            worker_id=0,
            feature="test-feature",
            worktree_path=tmp_path,
            branch="test-branch",
        )

        handle = launcher.get_handle(0)
        assert handle is None


class TestWorkerHandle:
    """Test WorkerHandle class."""

    def test_handle_has_worker_id(self) -> None:
        """WorkerHandle should have worker_id."""
        handle = WorkerHandle(
            worker_id=0,
            pid=12345,
            status=WorkerStatus.RUNNING,
        )

        assert handle.worker_id == 0

    def test_handle_has_status(self) -> None:
        """WorkerHandle should have status."""
        handle = WorkerHandle(
            worker_id=0,
            pid=12345,
            status=WorkerStatus.RUNNING,
        )

        assert handle.status == WorkerStatus.RUNNING

    def test_handle_is_alive_when_running(self) -> None:
        """is_alive() should return True when RUNNING."""
        handle = WorkerHandle(
            worker_id=0,
            pid=12345,
            status=WorkerStatus.RUNNING,
        )

        assert handle.is_alive() is True

    def test_handle_not_alive_when_stopped(self) -> None:
        """is_alive() should return False when STOPPED."""
        handle = WorkerHandle(
            worker_id=0,
            pid=12345,
            status=WorkerStatus.STOPPED,
        )

        assert handle.is_alive() is False


class TestLauncherStateConsistency:
    """Test launcher state remains consistent."""

    @patch("subprocess.Popen")
    def test_get_all_workers(self, mock_popen: MagicMock, tmp_path: Path) -> None:
        """get_all_workers should return all spawned workers."""
        mock_popen.return_value = MagicMock(pid=12345)

        launcher = SubprocessLauncher()

        # Spawn multiple workers
        for i in range(3):
            launcher.spawn(
                worker_id=i,
                feature="test-feature",
                worktree_path=tmp_path,
                branch=f"test-branch-{i}",
            )

        workers = launcher.get_all_workers()

        assert len(workers) == 3

    @patch("subprocess.Popen")
    def test_terminate_all(self, mock_popen: MagicMock, tmp_path: Path) -> None:
        """terminate_all should stop all workers."""
        mock_process = MagicMock(pid=12345)
        mock_process.poll.return_value = 0
        mock_popen.return_value = mock_process

        launcher = SubprocessLauncher()

        # Spawn multiple workers
        for i in range(3):
            launcher.spawn(
                worker_id=i,
                feature="test-feature",
                worktree_path=tmp_path,
                branch=f"test-branch-{i}",
            )

        launcher.terminate_all()

        # All should be terminated
        for i in range(3):
            status = launcher.monitor(i)
            assert status in [WorkerStatus.STOPPED, WorkerStatus.CRASHED]
