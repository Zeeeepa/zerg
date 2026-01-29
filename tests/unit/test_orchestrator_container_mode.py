"""Unit tests for Orchestrator container mode initialization."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from zerg.config import ZergConfig, WorkersConfig, LoggingConfig, PortsConfig, ResourcesConfig
from zerg.launcher import ContainerLauncher, LauncherConfig, LauncherType, SubprocessLauncher
from zerg.orchestrator import Orchestrator


class TestContainerModeInitialization:
    """Tests for Orchestrator container mode initialization."""

    @patch("zerg.orchestrator.StateManager")
    @patch("zerg.orchestrator.LevelController")
    @patch("zerg.orchestrator.TaskParser")
    @patch("zerg.orchestrator.GateRunner")
    @patch("zerg.orchestrator.WorktreeManager")
    @patch("zerg.orchestrator.ContainerManager")
    @patch("zerg.orchestrator.PortAllocator")
    @patch("zerg.orchestrator.MergeCoordinator")
    @patch("zerg.orchestrator.TaskSyncBridge")
    @patch("zerg.orchestrator.ContainerLauncher")
    def test_container_mode_initialization(
        self,
        mock_container_launcher_class: MagicMock,
        mock_task_sync: MagicMock,
        mock_merge_coordinator: MagicMock,
        mock_port_allocator: MagicMock,
        mock_container_manager: MagicMock,
        mock_worktree_manager: MagicMock,
        mock_gate_runner: MagicMock,
        mock_task_parser: MagicMock,
        mock_level_controller: MagicMock,
        mock_state_manager: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test that container mode initializes ContainerLauncher correctly."""
        mock_launcher_instance = MagicMock(spec=ContainerLauncher)
        mock_container_launcher_class.return_value = mock_launcher_instance

        config = ZergConfig()
        orchestrator = Orchestrator(
            feature="test-feature",
            config=config,
            repo_path=tmp_path,
            launcher_mode="container",
        )

        mock_container_launcher_class.assert_called_once()
        call_kwargs = mock_container_launcher_class.call_args.kwargs
        assert call_kwargs["image_name"] == "zerg-worker"
        assert isinstance(call_kwargs["config"], LauncherConfig)
        assert call_kwargs["config"].launcher_type == LauncherType.CONTAINER

        mock_launcher_instance.ensure_network.assert_called_once()
        assert orchestrator.launcher is mock_launcher_instance


class TestGetWorkerImageName:
    """Tests for _get_worker_image_name method."""

    @patch("zerg.orchestrator.StateManager")
    @patch("zerg.orchestrator.LevelController")
    @patch("zerg.orchestrator.TaskParser")
    @patch("zerg.orchestrator.GateRunner")
    @patch("zerg.orchestrator.WorktreeManager")
    @patch("zerg.orchestrator.ContainerManager")
    @patch("zerg.orchestrator.PortAllocator")
    @patch("zerg.orchestrator.MergeCoordinator")
    @patch("zerg.orchestrator.TaskSyncBridge")
    @patch("zerg.orchestrator.SubprocessLauncher")
    def test_get_worker_image_name_from_config(
        self,
        mock_subprocess_launcher_class: MagicMock,
        mock_task_sync: MagicMock,
        mock_merge_coordinator: MagicMock,
        mock_port_allocator: MagicMock,
        mock_container_manager: MagicMock,
        mock_worktree_manager: MagicMock,
        mock_gate_runner: MagicMock,
        mock_task_parser: MagicMock,
        mock_level_controller: MagicMock,
        mock_state_manager: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test _get_worker_image_name returns config value when set."""
        mock_launcher_instance = MagicMock(spec=SubprocessLauncher)
        mock_subprocess_launcher_class.return_value = mock_launcher_instance

        # Create a mock config with container_image attribute
        mock_config = MagicMock(spec=ZergConfig)
        mock_config.container_image = "custom-worker-image:v2"
        mock_config.workers = WorkersConfig()
        mock_config.logging = LoggingConfig()
        mock_config.ports = PortsConfig()
        mock_config.resources = ResourcesConfig()

        orchestrator = Orchestrator(
            feature="test-feature",
            config=mock_config,
            repo_path=tmp_path,
            launcher_mode="subprocess",
        )

        image_name = orchestrator._get_worker_image_name()
        assert image_name == "custom-worker-image:v2"

    @patch("zerg.orchestrator.StateManager")
    @patch("zerg.orchestrator.LevelController")
    @patch("zerg.orchestrator.TaskParser")
    @patch("zerg.orchestrator.GateRunner")
    @patch("zerg.orchestrator.WorktreeManager")
    @patch("zerg.orchestrator.ContainerManager")
    @patch("zerg.orchestrator.PortAllocator")
    @patch("zerg.orchestrator.MergeCoordinator")
    @patch("zerg.orchestrator.TaskSyncBridge")
    @patch("zerg.orchestrator.SubprocessLauncher")
    def test_get_worker_image_name_default(
        self,
        mock_subprocess_launcher_class: MagicMock,
        mock_task_sync: MagicMock,
        mock_merge_coordinator: MagicMock,
        mock_port_allocator: MagicMock,
        mock_container_manager: MagicMock,
        mock_worktree_manager: MagicMock,
        mock_gate_runner: MagicMock,
        mock_task_parser: MagicMock,
        mock_level_controller: MagicMock,
        mock_state_manager: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test _get_worker_image_name returns default when config not set."""
        mock_launcher_instance = MagicMock(spec=SubprocessLauncher)
        mock_subprocess_launcher_class.return_value = mock_launcher_instance

        config = ZergConfig()

        orchestrator = Orchestrator(
            feature="test-feature",
            config=config,
            repo_path=tmp_path,
            launcher_mode="subprocess",
        )

        image_name = orchestrator._get_worker_image_name()
        assert image_name == "zerg-worker"


class TestLauncherTypeSelection:
    """Tests for launcher type selection for container mode."""

    @patch("zerg.orchestrator.StateManager")
    @patch("zerg.orchestrator.LevelController")
    @patch("zerg.orchestrator.TaskParser")
    @patch("zerg.orchestrator.GateRunner")
    @patch("zerg.orchestrator.WorktreeManager")
    @patch("zerg.orchestrator.ContainerManager")
    @patch("zerg.orchestrator.PortAllocator")
    @patch("zerg.orchestrator.MergeCoordinator")
    @patch("zerg.orchestrator.TaskSyncBridge")
    @patch("zerg.orchestrator.ContainerLauncher")
    def test_launcher_type_container_mode(
        self,
        mock_container_launcher_class: MagicMock,
        mock_task_sync: MagicMock,
        mock_merge_coordinator: MagicMock,
        mock_port_allocator: MagicMock,
        mock_container_manager: MagicMock,
        mock_worktree_manager: MagicMock,
        mock_gate_runner: MagicMock,
        mock_task_parser: MagicMock,
        mock_level_controller: MagicMock,
        mock_state_manager: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test that container mode selects ContainerLauncher."""
        mock_launcher_instance = MagicMock(spec=ContainerLauncher)
        mock_container_launcher_class.return_value = mock_launcher_instance

        config = ZergConfig()
        orchestrator = Orchestrator(
            feature="test-feature",
            config=config,
            repo_path=tmp_path,
            launcher_mode="container",
        )

        mock_container_launcher_class.assert_called_once()
        call_kwargs = mock_container_launcher_class.call_args.kwargs
        assert call_kwargs["config"].launcher_type == LauncherType.CONTAINER

    @patch("zerg.orchestrator.StateManager")
    @patch("zerg.orchestrator.LevelController")
    @patch("zerg.orchestrator.TaskParser")
    @patch("zerg.orchestrator.GateRunner")
    @patch("zerg.orchestrator.WorktreeManager")
    @patch("zerg.orchestrator.ContainerManager")
    @patch("zerg.orchestrator.PortAllocator")
    @patch("zerg.orchestrator.MergeCoordinator")
    @patch("zerg.orchestrator.TaskSyncBridge")
    @patch("zerg.orchestrator.SubprocessLauncher")
    def test_launcher_type_subprocess_mode(
        self,
        mock_subprocess_launcher_class: MagicMock,
        mock_task_sync: MagicMock,
        mock_merge_coordinator: MagicMock,
        mock_port_allocator: MagicMock,
        mock_container_manager: MagicMock,
        mock_worktree_manager: MagicMock,
        mock_gate_runner: MagicMock,
        mock_task_parser: MagicMock,
        mock_level_controller: MagicMock,
        mock_state_manager: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test that subprocess mode selects SubprocessLauncher."""
        mock_launcher_instance = MagicMock(spec=SubprocessLauncher)
        mock_subprocess_launcher_class.return_value = mock_launcher_instance

        config = ZergConfig()
        orchestrator = Orchestrator(
            feature="test-feature",
            config=config,
            repo_path=tmp_path,
            launcher_mode="subprocess",
        )

        mock_subprocess_launcher_class.assert_called_once()
        call_kwargs = mock_subprocess_launcher_class.call_args
        assert call_kwargs[0][0].launcher_type == LauncherType.SUBPROCESS


class TestContainerLauncherConfiguration:
    """Tests for container launcher configuration."""

    @patch("zerg.orchestrator.StateManager")
    @patch("zerg.orchestrator.LevelController")
    @patch("zerg.orchestrator.TaskParser")
    @patch("zerg.orchestrator.GateRunner")
    @patch("zerg.orchestrator.WorktreeManager")
    @patch("zerg.orchestrator.ContainerManager")
    @patch("zerg.orchestrator.PortAllocator")
    @patch("zerg.orchestrator.MergeCoordinator")
    @patch("zerg.orchestrator.TaskSyncBridge")
    @patch("zerg.orchestrator.ContainerLauncher")
    def test_container_launcher_config_timeout(
        self,
        mock_container_launcher_class: MagicMock,
        mock_task_sync: MagicMock,
        mock_merge_coordinator: MagicMock,
        mock_port_allocator: MagicMock,
        mock_container_manager: MagicMock,
        mock_worktree_manager: MagicMock,
        mock_gate_runner: MagicMock,
        mock_task_parser: MagicMock,
        mock_level_controller: MagicMock,
        mock_state_manager: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test that container launcher is configured with correct timeout."""
        mock_launcher_instance = MagicMock(spec=ContainerLauncher)
        mock_container_launcher_class.return_value = mock_launcher_instance

        # Create mock config with timeout setting
        mock_config = MagicMock(spec=ZergConfig)
        mock_config.workers = WorkersConfig(timeout_minutes=30)
        mock_config.logging = LoggingConfig()
        mock_config.ports = PortsConfig()
        mock_config.resources = ResourcesConfig()

        orchestrator = Orchestrator(
            feature="test-feature",
            config=mock_config,
            repo_path=tmp_path,
            launcher_mode="container",
        )

        mock_container_launcher_class.assert_called_once()
        call_kwargs = mock_container_launcher_class.call_args.kwargs
        assert call_kwargs["config"].timeout_seconds == 30 * 60

    @patch("zerg.orchestrator.StateManager")
    @patch("zerg.orchestrator.LevelController")
    @patch("zerg.orchestrator.TaskParser")
    @patch("zerg.orchestrator.GateRunner")
    @patch("zerg.orchestrator.WorktreeManager")
    @patch("zerg.orchestrator.ContainerManager")
    @patch("zerg.orchestrator.PortAllocator")
    @patch("zerg.orchestrator.MergeCoordinator")
    @patch("zerg.orchestrator.TaskSyncBridge")
    @patch("zerg.orchestrator.ContainerLauncher")
    def test_container_launcher_config_log_dir(
        self,
        mock_container_launcher_class: MagicMock,
        mock_task_sync: MagicMock,
        mock_merge_coordinator: MagicMock,
        mock_port_allocator: MagicMock,
        mock_container_manager: MagicMock,
        mock_worktree_manager: MagicMock,
        mock_gate_runner: MagicMock,
        mock_task_parser: MagicMock,
        mock_level_controller: MagicMock,
        mock_state_manager: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test that container launcher is configured with correct log directory."""
        mock_launcher_instance = MagicMock(spec=ContainerLauncher)
        mock_container_launcher_class.return_value = mock_launcher_instance

        # Create mock config with custom log directory
        mock_config = MagicMock(spec=ZergConfig)
        mock_config.workers = WorkersConfig()
        mock_config.logging = LoggingConfig(directory="/custom/log/dir")
        mock_config.ports = PortsConfig()
        mock_config.resources = ResourcesConfig()

        orchestrator = Orchestrator(
            feature="test-feature",
            config=mock_config,
            repo_path=tmp_path,
            launcher_mode="container",
        )

        mock_container_launcher_class.assert_called_once()
        call_kwargs = mock_container_launcher_class.call_args.kwargs
        assert call_kwargs["config"].log_dir == Path("/custom/log/dir")

    @patch("zerg.orchestrator.StateManager")
    @patch("zerg.orchestrator.LevelController")
    @patch("zerg.orchestrator.TaskParser")
    @patch("zerg.orchestrator.GateRunner")
    @patch("zerg.orchestrator.WorktreeManager")
    @patch("zerg.orchestrator.ContainerManager")
    @patch("zerg.orchestrator.PortAllocator")
    @patch("zerg.orchestrator.MergeCoordinator")
    @patch("zerg.orchestrator.TaskSyncBridge")
    @patch("zerg.orchestrator.ContainerLauncher")
    def test_container_launcher_image_name_passed(
        self,
        mock_container_launcher_class: MagicMock,
        mock_task_sync: MagicMock,
        mock_merge_coordinator: MagicMock,
        mock_port_allocator: MagicMock,
        mock_container_manager: MagicMock,
        mock_worktree_manager: MagicMock,
        mock_gate_runner: MagicMock,
        mock_task_parser: MagicMock,
        mock_level_controller: MagicMock,
        mock_state_manager: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test that container launcher receives correct image name from config."""
        mock_launcher_instance = MagicMock(spec=ContainerLauncher)
        mock_container_launcher_class.return_value = mock_launcher_instance

        # Create mock config with container_image attribute
        mock_config = MagicMock(spec=ZergConfig)
        mock_config.container_image = "my-custom-image:latest"
        mock_config.workers = WorkersConfig()
        mock_config.logging = LoggingConfig()
        mock_config.ports = PortsConfig()
        mock_config.resources = ResourcesConfig()

        orchestrator = Orchestrator(
            feature="test-feature",
            config=mock_config,
            repo_path=tmp_path,
            launcher_mode="container",
        )

        mock_container_launcher_class.assert_called_once()
        call_kwargs = mock_container_launcher_class.call_args.kwargs
        assert call_kwargs["image_name"] == "my-custom-image:latest"

    @patch("zerg.orchestrator.StateManager")
    @patch("zerg.orchestrator.LevelController")
    @patch("zerg.orchestrator.TaskParser")
    @patch("zerg.orchestrator.GateRunner")
    @patch("zerg.orchestrator.WorktreeManager")
    @patch("zerg.orchestrator.ContainerManager")
    @patch("zerg.orchestrator.PortAllocator")
    @patch("zerg.orchestrator.MergeCoordinator")
    @patch("zerg.orchestrator.TaskSyncBridge")
    @patch("zerg.orchestrator.ContainerLauncher")
    def test_container_launcher_ensure_network_called(
        self,
        mock_container_launcher_class: MagicMock,
        mock_task_sync: MagicMock,
        mock_merge_coordinator: MagicMock,
        mock_port_allocator: MagicMock,
        mock_container_manager: MagicMock,
        mock_worktree_manager: MagicMock,
        mock_gate_runner: MagicMock,
        mock_task_parser: MagicMock,
        mock_level_controller: MagicMock,
        mock_state_manager: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test that ensure_network is called when using container mode."""
        mock_launcher_instance = MagicMock(spec=ContainerLauncher)
        mock_container_launcher_class.return_value = mock_launcher_instance

        config = ZergConfig()
        orchestrator = Orchestrator(
            feature="test-feature",
            config=config,
            repo_path=tmp_path,
            launcher_mode="container",
        )

        mock_launcher_instance.ensure_network.assert_called_once()
