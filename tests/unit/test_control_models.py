"""Tests for control data models."""

import pytest
from pydantic import ValidationError

from content_agent.models.control import (
    ControlFile,
    ControlGenerationResult,
    ControlRequirement,
    ControlValidationResult,
    DocumentSection,
    ExtractedRequirement,
    ParsedDocument,
    RuleSuggestion,
)


def test_control_requirement_basic():
    """Test basic ControlRequirement creation."""
    req = ControlRequirement(
        id="AC-2",
        title="Account Management",
        description="The organization manages information system accounts.",
    )

    assert req.id == "AC-2"
    assert req.title == "Account Management"
    assert req.status == "pending"
    assert len(req.rules) == 0


def test_control_requirement_with_rules():
    """Test ControlRequirement with rules."""
    req = ControlRequirement(
        id="AC-2(1)",
        title="Automated System Account Management",
        description="Support the management of information system accounts.",
        rules=["accounts_password_minlen_login_defs", "account_disable_post_pw_expiration"],
        status="automated",
    )

    assert len(req.rules) == 2
    assert req.status == "automated"


def test_control_requirement_without_description():
    """Test ControlRequirement without description (upstream CIS format)."""
    req = ControlRequirement(
        id="1.1.1.1",
        title="Ensure mounting of cramfs filesystems is disabled",
        status="automated",
        rules=["kernel_module_cramfs_disabled"],
        levels=["l1_server", "l1_workstation"],
    )

    assert req.id == "1.1.1.1"
    assert req.description is None
    assert req.status == "automated"
    assert len(req.rules) == 1


def test_control_file_basic():
    """Test basic ControlFile creation."""
    control = ControlFile(
        id="nist_800_53",
        title="NIST 800-53",
        description="NIST Special Publication 800-53",
        source_document="/path/to/nist_800_53.pdf",
    )

    assert control.id == "nist_800_53"
    assert len(control.controls) == 0


def test_control_file_with_controls():
    """Test ControlFile with requirements."""
    req1 = ControlRequirement(
        id="AC-1",
        title="Access Control Policy",
        description="Policy and procedures for access control.",
    )

    req2 = ControlRequirement(
        id="AC-2",
        title="Account Management",
        description="Account management policy.",
    )

    control = ControlFile(
        id="test_policy",
        title="Test Policy",
        description="Test control framework",
        source_document="test.pdf",
        controls=[req1, req2],
    )

    assert len(control.controls) == 2
    assert control.controls[0].id == "AC-1"


def test_parsed_document():
    """Test ParsedDocument creation."""
    section = DocumentSection(
        id="section_1",
        title="Introduction",
        level=1,
        content="This is the introduction.",
    )

    doc = ParsedDocument(
        title="Test Document",
        sections=[section],
        source_type="pdf",
    )

    assert doc.title == "Test Document"
    assert len(doc.sections) == 1
    assert doc.source_type == "pdf"


def test_extracted_requirement():
    """Test ExtractedRequirement creation."""
    req = ExtractedRequirement(
        text="The system must enforce password complexity.",
        section_id="password_policy",
        section_title="Password Policy",
        potential_id="PWD-001",
    )

    assert req.text == "The system must enforce password complexity."
    assert req.section_id == "password_policy"
    assert req.potential_id == "PWD-001"


def test_rule_suggestion():
    """Test RuleSuggestion creation."""
    suggestion = RuleSuggestion(
        rule_id="accounts_password_minlen_login_defs",
        confidence=0.85,
        reasoning="This rule enforces minimum password length.",
        match_type="semantic",
    )

    assert suggestion.rule_id == "accounts_password_minlen_login_defs"
    assert suggestion.confidence == 0.85
    assert suggestion.match_type == "semantic"


def test_rule_suggestion_confidence_validation():
    """Test RuleSuggestion confidence validation."""
    # Valid confidence
    suggestion = RuleSuggestion(
        rule_id="test_rule",
        confidence=0.5,
        reasoning="Test",
        match_type="keyword",
    )
    assert suggestion.confidence == 0.5

    # Invalid confidence should raise validation error
    with pytest.raises(ValidationError):
        RuleSuggestion(
            rule_id="test_rule",
            confidence=1.5,  # > 1.0
            reasoning="Test",
            match_type="keyword",
        )


def test_control_generation_result():
    """Test ControlGenerationResult creation."""
    from pathlib import Path

    result = ControlGenerationResult(
        policy_id="test_policy",
        parent_file_path=Path("/path/to/test_policy.yml"),
        requirement_files=[Path("/path/to/req1.yml"), Path("/path/to/req2.yml")],
        total_requirements=2,
        sections=["section1"],
        success=True,
    )

    assert result.success is True
    assert result.total_requirements == 2
    assert len(result.requirement_files) == 2


def test_control_validation_result():
    """Test ControlValidationResult creation."""
    from pathlib import Path

    result = ControlValidationResult(
        valid=False,
        errors=["Missing required field: id"],
        warnings=["Description is very short"],
        file_path=Path("/path/to/control.yml"),
    )

    assert result.valid is False
    assert len(result.errors) == 1
    assert len(result.warnings) == 1
