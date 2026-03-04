"""Tests for control file generator."""

import yaml

from content_agent.core.scaffolding.control_generator import ControlGenerator
from content_agent.models.control import (
    ControlRequirement,
    ExtractedRequirement,
)


def _make_generator():
    """Create a ControlGenerator without requiring a content repo."""
    return ControlGenerator.__new__(ControlGenerator)


def _sample_requirements():
    """Return a list of ExtractedRequirements for testing."""
    return [
        ExtractedRequirement(
            text="The system must enforce password complexity.",
            section_id="password_policy",
            section_title="Password Policy",
            potential_id="PWD-001",
        ),
        ExtractedRequirement(
            text="Accounts must be locked after failed attempts.",
            section_id="account_lockout",
            section_title="Account Lockout",
            potential_id="LOCK-001",
        ),
        ExtractedRequirement(
            text="Sessions must time out after inactivity.",
            section_id="session_mgmt",
            section_title="Session Management",
            potential_id="SESS-001",
        ),
    ]


def test_control_generator_init():
    """Test ControlGenerator initialization."""
    # Don't need real repo for this test - just create generator
    # ControlGenerator.__init__ will fail if it can't get repo, but that's OK for basic test
    pass  # Skipping init test as it requires full content repo setup


def test_generate_requirement_file(tmp_path):
    """Test generating individual requirement file."""
    # Create generator with mock content_repo

    generator = ControlGenerator.__new__(ControlGenerator)  # Skip __init__

    req = ControlRequirement(
        id="AC-2",
        title="Account Management",
        description="The organization manages information system accounts.",
        rules=["accounts_password_minlen_login_defs"],
        status="automated",
    )

    file_path = tmp_path / "test_req.yml"
    success = generator.generate_requirement_file(req, file_path)

    assert success is True
    assert file_path.exists()

    # Check file content
    import yaml

    with open(file_path) as f:
        data = yaml.safe_load(f)

    # New format has controls: wrapper
    assert "controls" in data
    assert len(data["controls"]) == 1

    control = data["controls"][0]
    assert control["id"] == "AC-2"
    assert control["title"] == "The organization manages information system accounts."
    assert len(control["rules"]) == 1
    assert control["status"] == "automated"


def test_generate_parent_control_file(tmp_path):
    """Test generating parent control file."""

    generator = ControlGenerator.__new__(ControlGenerator)  # Skip __init__

    file_path = tmp_path / "test_policy.yml"
    success = generator.generate_parent_control_file(
        policy_id="test_policy",
        policy_title="Test Policy",
        requirement_files=["req1.yml", "req2.yml"],
        output_path=file_path,
        version="v1.0",
        levels=["high", "medium", "low"],
    )

    assert success is True
    assert file_path.exists()

    # Check file content
    import yaml

    with open(file_path) as f:
        data = yaml.safe_load(f)

    # New format checks
    assert data["id"] == "test_policy"
    assert data["policy"] == "Test Policy"
    assert data["title"] == "Test Policy"
    assert data["version"] == "v1.0"
    assert data["controls_dir"] == "test_policy"
    assert len(data["levels"]) == 3
    assert data["levels"][0]["id"] == "high"


def test_convert_to_control_requirements():
    """Test converting ExtractedRequirement to ControlRequirement."""

    generator = ControlGenerator.__new__(ControlGenerator)  # Skip __init__

    extracted = [
        ExtractedRequirement(
            text="The system must enforce password complexity.",
            section_id="password_policy",
            section_title="Password Policy",
            potential_id="PWD-001",
        ),
        ExtractedRequirement(
            text="Accounts must be locked after failed attempts.",
            section_id="account_lockout",
            section_title="Account Lockout",
        ),
    ]

    requirements = generator._convert_to_control_requirements(extracted)

    assert len(requirements) == 2
    assert requirements[0].id == "PWD-001"
    assert requirements[1].id == "REQ-002"  # Auto-generated


def test_generate_filename():
    """Test filename generation."""

    generator = ControlGenerator.__new__(ControlGenerator)  # Skip __init__

    # Test with clear requirement ID
    req = ControlRequirement(
        id="AC-2(5)",
        title="Account Management",
        description="Test",
    )
    filename = generator._generate_filename(req, 1)
    assert filename.endswith(".yml")
    assert "ac" in filename.lower()

    # Test with auto-generated ID
    req = ControlRequirement(
        id="REQ-001",
        title="Requirement 1",
        description="Test",
    )
    filename = generator._generate_filename(req, 1)
    assert filename == "req_001.yml"


def test_inline_generation_creates_single_file(tmp_path):
    """Test inline format creates a single file with controls list, no subdirectory."""
    generator = _make_generator()
    requirements = _sample_requirements()
    output_dir = tmp_path / "controls"

    result = generator.generate_control_structure(
        policy_id="test_policy",
        policy_title="Test Policy",
        requirements=requirements,
        format="inline",
        output_dir=output_dir,
        version="v1.0",
        levels=["high", "medium", "low"],
    )

    assert result.success is True

    # Single file exists
    assert result.parent_file_path.exists()
    assert result.parent_file_path == output_dir / "test_policy.yml"

    # No subdirectory created
    assert not (output_dir / "test_policy").exists()

    # Check file content
    with open(result.parent_file_path) as f:
        data = yaml.safe_load(f)

    assert "controls" in data
    assert len(data["controls"]) == 3
    assert "controls_dir" not in data
    assert data["id"] == "test_policy"
    assert data["policy"] == "Test Policy"
    assert data["title"] == "Test Policy"
    assert data["version"] == "v1.0"
    assert len(data["levels"]) == 3


def test_inline_result_shape(tmp_path):
    """Test inline result has empty requirement_files and correct total."""
    generator = _make_generator()
    requirements = _sample_requirements()
    output_dir = tmp_path / "controls"

    result = generator.generate_control_structure(
        policy_id="test_policy",
        policy_title="Test Policy",
        requirements=requirements,
        format="inline",
        output_dir=output_dir,
    )

    assert result.success is True
    assert result.requirement_files == []
    assert result.total_requirements == 3


def test_inline_conflict_detection(tmp_path):
    """Test inline format fails when file already exists."""
    generator = _make_generator()
    requirements = _sample_requirements()
    output_dir = tmp_path / "controls"
    output_dir.mkdir(parents=True)
    (output_dir / "test_policy.yml").write_text("existing content")

    result = generator.generate_control_structure(
        policy_id="test_policy",
        policy_title="Test Policy",
        requirements=requirements,
        format="inline",
        output_dir=output_dir,
    )

    assert result.success is False
    assert len(result.errors) > 0
    assert "already exists" in result.errors[0]


def test_directory_generation_still_works(tmp_path):
    """Regression test: directory format produces parent file + requirement directory."""
    generator = _make_generator()
    requirements = _sample_requirements()
    output_dir = tmp_path / "controls"

    result = generator.generate_control_structure(
        policy_id="test_policy",
        policy_title="Test Policy",
        requirements=requirements,
        format="directory",
        output_dir=output_dir,
        version="v1.0",
    )

    assert result.success is True

    # Parent file exists with controls_dir
    assert result.parent_file_path.exists()
    with open(result.parent_file_path) as f:
        parent_data = yaml.safe_load(f)
    assert parent_data["controls_dir"] == "test_policy"
    assert "controls" not in parent_data

    # Subdirectory with individual files
    policy_dir = output_dir / "test_policy"
    assert policy_dir.is_dir()
    assert len(result.requirement_files) == 3
    assert result.total_requirements == 3
    for req_file in result.requirement_files:
        assert req_file.exists()
