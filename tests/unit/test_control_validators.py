"""Tests for control validators."""

from pathlib import Path

import pytest
import yaml

from content_agent.core.scaffolding.control_validators import ControlValidator
from content_agent.models.control import ControlFile, ControlRequirement


@pytest.fixture
def validator():
    """Create ControlValidator instance."""
    # Create validator without requiring full content repo
    validator = ControlValidator.__new__(ControlValidator)
    validator.rule_discovery = None  # Mock for tests that don't need it
    return validator


def test_validate_control_structure_valid(validator):
    """Test validation of valid control structure."""
    control_data = {
        "id": "test_policy",
        "title": "Test Policy",
        "description": "Test description",
    }

    result = validator.validate_control_structure(control_data)
    assert result.valid is True
    assert len(result.errors) == 0


def test_validate_control_structure_missing_fields(validator):
    """Test validation with missing required fields."""
    control_data = {
        "description": "Test description",
    }

    result = validator.validate_control_structure(control_data)
    assert result.valid is False
    assert len(result.errors) > 0
    assert any("id" in err.lower() for err in result.errors)


def test_validate_control_structure_invalid_controls(validator):
    """Test validation with invalid controls list."""
    control_data = {
        "id": "test_policy",
        "title": "Test Policy",
        "controls": "not a list",  # Should be list
    }

    result = validator.validate_control_structure(control_data)
    assert result.valid is False
    assert any("list" in err.lower() for err in result.errors)


def test_validate_control_file_valid(validator, tmp_path):
    """Test validation of valid control file."""
    control_file = tmp_path / "test_policy.yml"

    data = {
        "id": "test_policy",
        "title": "Test Policy",
        "description": "Test description",
        "source_document": "test.pdf",
    }

    with open(control_file, "w") as f:
        yaml.dump(data, f)

    result = validator.validate_control_file(control_file)
    assert result.valid is True


def test_validate_control_file_invalid_yaml(validator, tmp_path):
    """Test validation of invalid YAML."""
    control_file = tmp_path / "bad.yml"
    control_file.write_text("invalid: yaml: content:")

    result = validator.validate_control_file(control_file)
    assert result.valid is False
    assert any("yaml" in err.lower() for err in result.errors)


def test_validate_control_file_nonexistent(validator):
    """Test validation of nonexistent file."""
    result = validator.validate_control_file(Path("/nonexistent/file.yml"))
    assert result.valid is False
    assert any("not found" in err.lower() for err in result.errors)


def test_validate_rule_references(validator, monkeypatch):
    """Test rule reference validation."""
    # Mock available rules
    available_rules = [
        "accounts_password_minlen_login_defs",
        "account_disable_post_pw_expiration",
    ]

    control = ControlFile(
        id="test_policy",
        title="Test Policy",
        description="Test",
        source_document="test.pdf",
        controls=[
            ControlRequirement(
                id="REQ-1",
                title="Password Policy",
                description="Test",
                rules=["accounts_password_minlen_login_defs"],  # Valid
            ),
            ControlRequirement(
                id="REQ-2",
                title="Account Policy",
                description="Test",
                rules=["nonexistent_rule"],  # Invalid
            ),
        ],
    )

    result = validator.validate_rule_references(control, available_rules)
    assert result.valid is False
    assert len(result.errors) == 1
    assert "nonexistent_rule" in result.errors[0]


def test_validate_control_directory(validator, tmp_path):
    """Test validation of control directory."""
    # Create some control files
    controls_dir = tmp_path / "controls"
    controls_dir.mkdir()

    # Valid file
    valid_file = controls_dir / "valid.yml"
    with open(valid_file, "w") as f:
        yaml.dump({"id": "valid", "title": "Valid"}, f)

    # Invalid file
    invalid_file = controls_dir / "invalid.yml"
    invalid_file.write_text("invalid yaml:")

    result = validator.validate_control_directory(controls_dir)
    assert result.valid is False  # Because one file is invalid
    assert len(result.errors) > 0


def test_validate_control_directory_nonexistent(validator):
    """Test validation of nonexistent directory."""
    result = validator.validate_control_directory(Path("/nonexistent/dir"))
    assert result.valid is False


def test_validate_rule_references_skips_variables_and_unselections(validator):
    """Variables, refinements and unselections are not rule references."""
    control = ControlFile(
        id="test_policy",
        title="Test Policy",
        controls=[
            ControlRequirement(
                id="5.4.3.3",
                rules=[
                    "accounts_umask_etc_bashrc",
                    "var_accounts_user_umask=027",
                    "accounts_umask_etc_bashrc.severity=high",
                    "!removed_rule",
                ],
                related_rules=["var_related=1"],
            ),
        ],
    )

    result = validator.validate_rule_references(control, ["accounts_umask_etc_bashrc"])
    assert result.valid is True
    assert result.errors == []
    assert result.warnings == []


def test_validate_rule_references_without_rule_list_skips_checks(validator):
    """When the rule list can't be loaded, rules are not reported as missing."""

    class BrokenDiscovery:
        def search_rules(self, limit):
            raise RuntimeError("content repository not initialized")

    validator.rule_discovery = BrokenDiscovery()
    control = ControlFile(
        id="test_policy",
        title="Test Policy",
        controls=[ControlRequirement(id="REQ-1", rules=["some_rule"])],
    )

    result = validator.validate_rule_references(control)
    assert result.valid is True
    assert result.errors == []
    assert "skipping rule checks" in result.warnings[0]


def test_validate_control_structure_requirement_without_description(validator):
    """Requirements without a description produce no warning."""
    result = validator.validate_control_structure(
        {"id": "policy", "title": "Policy", "controls": [{"id": "1.1", "title": "T"}]}
    )
    assert result.valid is True
    assert result.warnings == []
