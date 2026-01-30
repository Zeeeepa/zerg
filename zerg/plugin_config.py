"""Plugin configuration Pydantic models."""

from pydantic import BaseModel, Field


class HookConfig(BaseModel):
    """Configuration for a lifecycle hook plugin.

    Attributes:
        event: Event name to trigger on (e.g., 'task_started', 'merge_complete')
        command: Shell command to execute when event fires
        timeout: Maximum execution time in seconds (default: 60)
    """

    event: str
    command: str
    timeout: int = Field(default=60, ge=1, le=3600)


class PluginGateConfig(BaseModel):
    """Configuration for a quality gate plugin.

    Attributes:
        name: Gate name (for identification in logs)
        command: Shell command to execute for validation
        required: Whether gate failure blocks merge (default: False)
        timeout: Maximum execution time in seconds (default: 300)
    """

    name: str
    command: str
    required: bool = False
    timeout: int = Field(default=300, ge=1, le=3600)


class LauncherPluginConfig(BaseModel):
    """Configuration for a launcher plugin.

    Attributes:
        name: Plugin name (for identification)
        entry_point: Python entry point string (e.g., 'my_package.my_module:K8sLauncher')
    """

    name: str
    entry_point: str


class PluginsConfig(BaseModel):
    """Complete plugins configuration.

    Attributes:
        enabled: Whether plugin system is enabled (default: True)
        hooks: List of lifecycle hook configurations
        quality_gates: List of quality gate plugin configurations
        launchers: List of launcher plugin configurations
    """

    enabled: bool = True
    hooks: list[HookConfig] = Field(default_factory=list)
    quality_gates: list[PluginGateConfig] = Field(default_factory=list)
    launchers: list[LauncherPluginConfig] = Field(default_factory=list)
