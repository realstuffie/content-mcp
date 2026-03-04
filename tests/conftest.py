"""Pytest configuration and fixtures."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from content_agent.config import initialize_settings
from content_agent.core.integration import initialize_content_repository


def _find_content_repo() -> Path | None:
    """Find a ComplianceAsCode/content repository for integration tests.

    Checks (in order):
    1. CONTENT_REPO env var (explicit path)
    2. Default managed path (~/.content-agent/content)

    Returns:
        Path to content repo, or None if not found.
    """
    env_path = os.environ.get("CONTENT_REPO")
    if env_path:
        p = Path(env_path).expanduser()
        if p.exists() and (p / "products").is_dir() and (p / "ssg").is_dir():
            return p

    managed = Path.home() / ".content-agent" / "content"
    if managed.exists() and (managed / "products").is_dir() and (managed / "ssg").is_dir():
        return managed

    return None


CONTENT_REPO_PATH = _find_content_repo()
HAS_CONTENT_REPO = CONTENT_REPO_PATH is not None

requires_content_repo = pytest.mark.skipif(
    not HAS_CONTENT_REPO,
    reason="Requires ComplianceAsCode/content repository "
    "(set CONTENT_REPO env var or clone to ~/.content-agent/content)",
)


@pytest.fixture
def real_content_repo():
    """Initialize the real content repository.

    Only available when a real ComplianceAsCode/content repo is found.
    Re-initializes global state if it was cleared by another fixture.
    """
    import content_agent.config.settings as settings_module
    import content_agent.core.integration.content_manager as cm
    import content_agent.core.integration.ssg_modules as sm

    assert CONTENT_REPO_PATH is not None

    # Re-initialize if global state was cleared by another fixture
    if settings_module._settings is None:
        initialize_settings()
    if cm._content_repo is None:
        repo = initialize_content_repository(CONTENT_REPO_PATH)
    else:
        repo = cm._content_repo
    if sm._ssg_modules is None:
        from content_agent.core.integration import initialize_ssg_modules

        initialize_ssg_modules()

    yield repo


@pytest.fixture
def temp_dir():
    """Provide a temporary directory that's cleaned up after test."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_rule_yaml():
    """Provide sample rule YAML content."""
    return """
documentation_complete: true
title: Configure SSH Idle Timeout
description: |
    SSH allows administrators to set an idle timeout interval.
    After this interval has passed, the idle user will be automatically logged out.
rationale: |
    Terminating an idle session within a short time period reduces the window of
    opportunity for unauthorized personnel to take control of a management session.
severity: medium
identifiers:
    cce: CCE-80906-3
references:
    nist:
        - AC-2(5)
        - SC-10
    disa:
        - RHEL-09-255030
platform: machine
products:
    - rhel9
    - rhel8
"""


@pytest.fixture
def sample_product_yaml():
    """Provide sample product YAML content."""
    return """
product: rhel9
full_name: Red Hat Enterprise Linux 9
product_type: rhel
product_version: 9
cpe: cpe:/o:redhat:enterprise_linux:9
description: |
    Security compliance content for Red Hat Enterprise Linux 9
"""


@pytest.fixture
def sample_profile_content():
    """Provide sample profile content."""
    return """
documentation_complete: true

title: Protection Profile for General Purpose Operating Systems

description: |
    This profile reflects mandatory configuration controls identified in the
    NIAP Configuration Annex to the Protection Profile for General Purpose
    Operating Systems (Protection Profile Version 4.2.1).

selections:
    - sshd_set_idle_timeout
    - accounts_password_minlen_login_defs
    - audit_rules_login_events
"""


@pytest.fixture
def mock_content_repo(temp_dir):
    """Create a mock content repository structure."""
    repo = temp_dir / "content"
    repo.mkdir()

    # Create basic structure
    (repo / "ssg").mkdir()
    (repo / "linux_os").mkdir()
    (repo / "products").mkdir()
    (repo / "shared" / "templates").mkdir(parents=True)
    (repo / "controls").mkdir()

    # Create a sample product
    rhel9_dir = repo / "products" / "rhel9"
    rhel9_dir.mkdir()

    product_yml = rhel9_dir / "product.yml"
    product_yml.write_text("""
product: rhel9
full_name: Red Hat Enterprise Linux 9
product_type: rhel
""")

    # Create profiles directory
    profiles_dir = rhel9_dir / "profiles"
    profiles_dir.mkdir()

    # Create CMakeLists.txt
    cmake_file = repo / "CMakeLists.txt"
    cmake_file.write_text("project(scap_security_guide VERSION 0.1.70)\n")

    return repo


@pytest.fixture
def initialized_content_repo(mock_content_repo, monkeypatch):
    """Initialize the content repository with mock data."""
    # Initialize settings first
    initialize_settings()

    # Initialize the content repository with the mock repo path
    repo = initialize_content_repository(mock_content_repo)

    # Mock SSG modules since they won't be available in the test environment
    import content_agent.core.integration.ssg_modules as sm

    mock_ssg = MagicMock()
    sm._ssg_modules = mock_ssg

    yield repo

    # Cleanup: Reset the global instances
    import content_agent.config.settings as settings_module
    import content_agent.core.integration.content_manager as cm

    settings_module._settings = None
    cm._content_repo = None
    sm._ssg_modules = None
