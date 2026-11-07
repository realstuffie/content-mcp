"""Configuration settings using Pydantic Settings."""

import os
from pathlib import Path
from typing import Literal

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ContentSettings(BaseSettings):
    """Content repository settings."""

    repository: str = Field(
        default="managed",
        description="Repository location: 'managed' or absolute path",
    )
    managed_path: Path = Field(
        default=Path.home() / ".content-agent" / "content",
        description="Path for managed repository",
    )
    branch: str = Field(default="master", description="Git branch to use")
    auto_update: bool = Field(default=True, description="Auto-update managed repository")
    repo_url: str = Field(
        default="https://github.com/ComplianceAsCode/content.git",
        description="Repository URL for managed checkout",
    )

    model_config = SettingsConfigDict(env_prefix="CONTENT_AGENT_CONTENT__")


class HttpSettings(BaseSettings):
    """HTTP server settings."""

    host: str = Field(default="127.0.0.1", description="HTTP host")
    port: int = Field(default=8080, description="HTTP port")
    cors_enabled: bool = Field(default=False, description="Enable CORS")
    cors_origins: list[str] = Field(default=["*"], description="Allowed CORS origins")

    model_config = SettingsConfigDict(env_prefix="CONTENT_AGENT_SERVER__HTTP__")


class ServerSettings(BaseSettings):
    """Server settings."""

    mode: Literal["stdio", "http"] = Field(default="stdio", description="Server mode")
    http: HttpSettings = Field(default_factory=HttpSettings)

    model_config = SettingsConfigDict(env_prefix="CONTENT_AGENT_SERVER__")


class BuildSettings(BaseSettings):
    """Build settings."""

    build_dir: Path = Field(
        default=Path.home() / ".content-agent" / "builds",
        description="Build artifacts directory",
    )
    max_concurrent_builds: int = Field(
        default=2, description="Maximum concurrent builds", ge=1, le=10
    )
    timeout: int = Field(default=3600, description="Build timeout in seconds", ge=60, le=7200)
    keep_logs: bool = Field(default=True, description="Keep build logs")
    log_retention_days: int = Field(default=7, description="Log retention in days", ge=1)

    model_config = SettingsConfigDict(env_prefix="CONTENT_AGENT_BUILD__")


class TestingSettings(BaseSettings):
    """Testing settings."""

    __test__ = False  # not a pytest test class

    backend: Literal["podman", "docker"] = Field(default="podman", description="Container backend")
    max_concurrent_tests: int = Field(
        default=4, description="Maximum concurrent tests", ge=1, le=20
    )
    timeout: int = Field(default=1800, description="Test timeout in seconds", ge=60, le=3600)
    keep_logs: bool = Field(default=True, description="Keep test logs")
    image_strategy: Literal["auto", "latest"] = Field(
        default="auto", description="Container image selection"
    )

    model_config = SettingsConfigDict(env_prefix="CONTENT_AGENT_TESTING__")


class JobsSettings(BaseSettings):
    """Jobs settings."""

    database: Path = Field(
        default=Path.home() / ".content-agent" / "jobs.db",
        description="Job database file",
    )
    max_workers: int = Field(default=4, description="Thread pool size", ge=1, le=20)
    retention_days: int = Field(default=7, description="Job history retention in days", ge=1)
    poll_interval: float = Field(
        default=1.0, description="Job status polling interval", ge=0.1, le=10.0
    )

    model_config = SettingsConfigDict(env_prefix="CONTENT_AGENT_JOBS__")


class SecuritySettings(BaseSettings):
    """Security settings."""

    validate_inputs: bool = Field(default=True, description="Enable input validation")
    max_yaml_size_kb: int = Field(
        default=1024, description="Maximum YAML size in KB", ge=1, le=10240
    )
    enable_auth: bool = Field(default=False, description="Enable authentication")
    enable_audit: bool = Field(default=False, description="Enable audit logging")

    model_config = SettingsConfigDict(env_prefix="CONTENT_AGENT_SECURITY__")


class AISettings(BaseSettings):
    """AI integration settings."""

    claude_api_key: str = Field(
        default="",
        description="Claude API key for AI-powered features",
    )
    model: str = Field(
        default="claude-sonnet-5-5",
        description="Claude model to use",
    )
    max_tokens: int = Field(
        default=4096,
        description="Maximum tokens per request",
        ge=1,
        le=200000,
    )
    temperature: float = Field(
        default=0.0,
        description=(
            "Temperature for AI generation (0.0 = deterministic). Not sent with "
            "anthropic SDK 2.x, which has no temperature parameter."
        ),
        ge=0.0,
        le=1.0,
    )
    enabled: bool = Field(
        default=False,
        description="Enable AI-powered features",
    )

    model_config = SettingsConfigDict(env_prefix="CONTENT_AGENT_AI__")


class LoggingSettings(BaseSettings):
    """Logging settings."""

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO", description="Log level"
    )
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format",
    )
    file: Path | None = Field(
        default=Path.home() / ".content-agent" / "server.log",
        description="Log file path",
    )
    console: bool = Field(default=True, description="Enable console logging")

    model_config = SettingsConfigDict(env_prefix="CONTENT_AGENT_LOGGING__")


class Settings(BaseSettings):
    """Main settings container."""

    content: ContentSettings = Field(default_factory=ContentSettings)
    server: ServerSettings = Field(default_factory=ServerSettings)
    build: BuildSettings = Field(default_factory=BuildSettings)
    testing: TestingSettings = Field(default_factory=TestingSettings)
    jobs: JobsSettings = Field(default_factory=JobsSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    ai: AISettings = Field(default_factory=AISettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)

    model_config = SettingsConfigDict(env_prefix="CONTENT_AGENT_", env_nested_delimiter="__")

    @classmethod
    def from_yaml(cls, yaml_path: Path) -> "Settings":
        """Load settings from YAML file.

        Args:
            yaml_path: Path to YAML configuration file

        Returns:
            Settings instance
        """
        with open(yaml_path) as f:
            config_data = yaml.safe_load(f)

        return cls(**config_data)

    @classmethod
    def load(cls, config_file: Path | None = None) -> "Settings":
        """Load settings from defaults, config file, and environment.

        Priority (highest to lowest):
        1. Environment variables
        2. Config file (if provided)
        3. Default config file

        Args:
            config_file: Optional config file path

        Returns:
            Settings instance
        """
        # Start with defaults from defaults.yaml
        defaults_path = Path(__file__).parent / "defaults.yaml"
        with open(defaults_path) as f:
            config_data = yaml.safe_load(f)

        # Override with user config file if provided
        if config_file and config_file.exists():
            with open(config_file) as f:
                user_config = yaml.safe_load(f)
                config_data = _merge_dicts(config_data, user_config)

        # First create settings without config_data to let environment variables
        # be read by pydantic-settings, then overlay YAML defaults only where
        # environment variables are not set
        settings = cls()

        # Apply YAML config as defaults (won't override already-set env values)
        if config_data:
            # For nested settings, we need to merge carefully
            for key, value in config_data.items():
                if hasattr(settings, key):
                    attr = getattr(settings, key)
                    if isinstance(value, dict) and isinstance(attr, BaseSettings):
                        # For nested BaseSettings, rebuild with merged values
                        current_dict = attr.model_dump()
                        for nested_key, nested_value in value.items():
                            # Only set if not already customized from environment
                            if not _is_env_var_set(key, nested_key):
                                current_dict[nested_key] = nested_value
                        # Recreate the nested settings object to ensure validation
                        setattr(settings, key, type(attr)(**current_dict))
                    else:
                        # For simple fields, check if env var was set
                        if not _is_env_var_set(key):
                            setattr(settings, key, value)

        return settings

    def ensure_directories(self) -> None:
        """Ensure all configured directories exist."""
        dirs_to_create = [
            self.content.managed_path,
            self.build.build_dir,
            self.jobs.database.parent,
        ]

        if self.logging.file:
            dirs_to_create.append(self.logging.file.parent)

        for directory in dirs_to_create:
            directory = Path(directory).expanduser()
            directory.mkdir(parents=True, exist_ok=True)


def _merge_dicts(base: dict, override: dict) -> dict:
    """Recursively merge two dictionaries.

    Args:
        base: Base dictionary
        override: Dictionary with overriding values

    Returns:
        Merged dictionary
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def _is_env_var_set(*keys: str) -> bool:
    """Check if an environment variable is set for the given setting path.

    Args:
        *keys: Setting path components (e.g., 'content', 'repository')

    Returns:
        True if corresponding environment variable exists
    """
    # Build environment variable name
    # Main prefix is CONTENT_AGENT_, nested delimiter is __
    if len(keys) == 1:
        env_var = f"CONTENT_AGENT_{keys[0].upper()}"
    else:
        env_var = f"CONTENT_AGENT_{'__'.join(k.upper() for k in keys)}"

    return env_var in os.environ


# Global settings instance (initialized by main)
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get the global settings instance.

    Returns:
        Settings instance

    Raises:
        RuntimeError: If settings not initialized
    """
    if _settings is None:
        raise RuntimeError("Settings not initialized. Call initialize_settings() first.")
    return _settings


def initialize_settings(config_file: Path | None = None) -> Settings:
    """Initialize global settings.

    Args:
        config_file: Optional config file path

    Returns:
        Settings instance
    """
    global _settings
    _settings = Settings.load(config_file)
    _settings.ensure_directories()
    return _settings
