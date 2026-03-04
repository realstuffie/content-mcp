"""Main entry point for content-agent."""

import asyncio
import logging
import sys
from pathlib import Path

import click

from content_agent.config import initialize_settings
from content_agent.core.integration import (
    initialize_content_repository,
    initialize_ssg_modules,
)
from content_agent.server import run_stdio_server


def setup_logging(level: str, log_file: Path | None = None) -> None:
    """Set up logging configuration.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional log file path
    """
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(numeric_level)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    root_logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        log_file = Path(log_file).expanduser()
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(numeric_level)
        root_logger.addHandler(file_handler)


@click.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file",
)
@click.option(
    "--content-repo",
    type=str,
    help="Path to content repository or 'managed' for auto-checkout",
)
@click.option(
    "--mode",
    type=click.Choice(["stdio", "http"]),
    default="stdio",
    help="Server mode (default: stdio)",
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]),
    default="INFO",
    help="Log level (default: INFO)",
)
@click.option(
    "--log-file",
    type=click.Path(path_type=Path),
    help="Log file path",
)
@click.version_option(version="0.1.0", prog_name="content-agent")
def main(
    config: Path | None,
    content_repo: str | None,
    mode: str,
    log_level: str,
    log_file: Path | None,
) -> None:
    """ComplianceAsCode/content MCP server.

    Provides AI assistant access to security compliance automation workflows.

    Examples:

      # Run with managed repository (auto-clone)
      $ content-agent

      # Run with existing repository
      $ content-agent --content-repo /path/to/content

      # Run with custom config
      $ content-agent --config config.yaml

      # Debug mode
      $ content-agent --log-level DEBUG
    """
    try:
        # Initialize settings
        settings = initialize_settings(config)

        # Override settings from CLI args
        if content_repo:
            settings.content.repository = content_repo
        if log_file:
            settings.logging.file = log_file
        settings.logging.level = log_level  # type: ignore[assignment]
        settings.server.mode = mode  # type: ignore[assignment]

        # Set up logging
        setup_logging(settings.logging.level, settings.logging.file)

        logger = logging.getLogger(__name__)
        logger.info("Starting content-agent v0.1.0")
        logger.info(f"Mode: {settings.server.mode}")
        logger.info(f"Content repository: {settings.content.repository}")

        # Initialize content repository
        logger.info("Initializing content repository...")
        repo_path = None
        if settings.content.repository != "managed":
            repo_path = Path(settings.content.repository).expanduser()

        repo = initialize_content_repository(repo_path)
        logger.info(f"Content repository initialized at: {repo.path}")

        # Show repository info
        commit_info = repo.get_commit_info()
        if commit_info:
            logger.info(f"Repository commit: {commit_info['sha']} - {commit_info['message']}")

        ssg_version = repo.get_ssg_version()
        if ssg_version:
            logger.info(f"SSG version: {ssg_version}")

        # Initialize SSG modules
        logger.info("Loading SSG Python modules...")
        initialize_ssg_modules()
        logger.info("SSG modules loaded successfully")

        # Run server based on mode
        if settings.server.mode == "stdio":
            logger.info("Starting stdio server...")
            asyncio.run(run_stdio_server())
        else:
            logger.error("HTTP mode not yet implemented (Phase 4)")
            sys.exit(1)

    except KeyboardInterrupt:
        logger = logging.getLogger(__name__)
        logger.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Server failed to start: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
