"""Task retry management for ZERG orchestrator."""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from pathlib import Path

from zerg.config import ZergConfig
from zerg.constants import LogEvent, TaskStatus
from zerg.levels import LevelController
from zerg.log_writer import StructuredLogWriter
from zerg.logging import get_logger
from zerg.retry_backoff import RetryBackoffCalculator
from zerg.state import StateManager

logger = get_logger("task_retry_manager")


class TaskRetryManager:
    """Manage task retry logic including backoff, requeueing, and verification retries.

    Extracted from Orchestrator to encapsulate all retry-related behavior.
    """

    def __init__(
        self,
        config: ZergConfig,
        state: StateManager,
        levels: LevelController,
        repo_path: Path,
        structured_writer: StructuredLogWriter | None = None,
    ) -> None:
        """Initialize TaskRetryManager.

        Args:
            config: ZERG configuration
            state: State manager for task state operations
            levels: Level controller for marking task failures
            repo_path: Path to the repository root
            structured_writer: Optional structured log writer
        """
        self._config = config
        self._state = state
        self._levels = levels
        self._repo_path = repo_path
        self._structured_writer = structured_writer
        self._max_retry_attempts = config.workers.retry_attempts

    def check_retry_ready_tasks(self) -> None:
        """Check for tasks whose backoff period has elapsed and requeue them."""
        ready_tasks = self._state.get_tasks_ready_for_retry()
        for task_id in ready_tasks:
            logger.info(f"Task {task_id} backoff elapsed, requeueing for retry")
            self._state.set_task_status(task_id, TaskStatus.PENDING)
            self._state.set_task_retry_schedule(task_id, "")
            self._state.append_event("task_retry_ready", {"task_id": task_id})

    def handle_task_failure(self, task_id: str, worker_id: int, error: str) -> bool:
        """Handle task failure with retry logic and backoff.

        Args:
            task_id: ID of the failed task
            worker_id: ID of the worker that was running the task
            error: Error message describing the failure

        Returns:
            True if the task was scheduled for retry, False if permanently failed
        """
        retry_count = self._state.get_task_retry_count(task_id)
        if retry_count < self._max_retry_attempts:
            delay = RetryBackoffCalculator.calculate_delay(
                attempt=retry_count + 1,
                strategy=self._config.workers.backoff_strategy,
                base_seconds=self._config.workers.backoff_base_seconds,
                max_seconds=self._config.workers.backoff_max_seconds,
            )
            next_retry_at = (datetime.now() + timedelta(seconds=delay)).isoformat()
            new_count = self._state.increment_task_retry(task_id, next_retry_at=next_retry_at)
            self._state.set_task_retry_schedule(task_id, next_retry_at)
            logger.warning(f"Task {task_id} failed (attempt {new_count}/{self._max_retry_attempts}), will retry in {delay:.0f}s: {error}")
            self._state.set_task_status(task_id, "waiting_retry")
            self._state.append_event("task_retry_scheduled", {
                "task_id": task_id, "worker_id": worker_id, "retry_count": new_count,
                "backoff_seconds": round(delay), "next_retry_at": next_retry_at, "error": error,
            })
            if self._structured_writer:
                self._structured_writer.emit("warn", f"Task {task_id} retry {new_count} scheduled in {delay:.0f}s",
                    event=LogEvent.TASK_FAILED, data={"task_id": task_id, "backoff_seconds": round(delay)})
            return True
        else:
            logger.error(f"Task {task_id} failed after {retry_count} retries: {error}")
            self._levels.mark_task_failed(task_id, error)
            self._state.set_task_status(task_id, TaskStatus.FAILED, worker_id=worker_id,
                error=f"Failed after {retry_count} retries: {error}")
            self._state.append_event("task_failed_permanent", {
                "task_id": task_id, "worker_id": worker_id, "retry_count": retry_count, "error": error})
            return False

    def retry_task(self, task_id: str) -> bool:
        """Manually retry a failed task.

        Args:
            task_id: ID of the task to retry

        Returns:
            True if the task was successfully queued for retry
        """
        current_status = self._state.get_task_status(task_id)
        if current_status not in (TaskStatus.FAILED.value, "failed"):
            logger.warning(f"Task {task_id} is not in failed state: {current_status}")
            return False
        self._state.reset_task_retry(task_id)
        self._state.set_task_status(task_id, TaskStatus.PENDING)
        self._state.append_event("task_manual_retry", {"task_id": task_id})
        logger.info(f"Task {task_id} queued for retry")
        return True

    def retry_all_failed(self) -> list[str]:
        """Retry all failed tasks.

        Returns:
            List of task IDs that were queued for retry
        """
        failed = self._state.get_failed_tasks()
        retried = []
        for task_info in failed:
            task_id = task_info["task_id"]
            if self.retry_task(task_id):
                retried.append(task_id)
        logger.info(f"Queued {len(retried)} tasks for retry")
        return retried

    def verify_with_retry(self, task_id: str, command: str, timeout: int = 60, max_retries: int | None = None) -> bool:
        """Verify a task with retry logic.

        Args:
            task_id: ID of the task to verify
            command: Verification command to run
            timeout: Timeout for each verification attempt in seconds
            max_retries: Maximum number of retry attempts (defaults to config value)

        Returns:
            True if verification passed, False if all attempts failed
        """
        from zerg.verify import VerificationExecutor
        verifier = VerificationExecutor()
        max_attempts = max_retries if max_retries is not None else self._max_retry_attempts
        for attempt in range(max_attempts + 1):
            result = verifier.verify(command, task_id, timeout=timeout, cwd=self._repo_path)
            if result.success:
                return True
            if attempt < max_attempts:
                logger.warning(f"Verification failed for {task_id} (attempt {attempt + 1}/{max_attempts + 1}), retrying...")
                time.sleep(1)
        return False
