"""Rule data models."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RuleSearchResult(BaseModel):
    """Search result for a rule."""

    rule_id: str = Field(..., description="Rule identifier")
    title: str = Field(..., description="Rule title")
    severity: str = Field(..., description="Rule severity (low, medium, high, unknown)")
    description: str | None = Field(None, description="Short description")
    products: list[str] = Field(default_factory=list, description="Products this rule applies to")
    file_path: str = Field(..., description="Path to rule.yml file")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "rule_id": "sshd_set_idle_timeout",
                "title": "Set SSH Idle Timeout Interval",
                "severity": "medium",
                "description": "Configure SSH to automatically terminate idle sessions",
                "products": ["rhel7", "rhel8", "rhel9", "fedora"],
                "file_path": "linux_os/guide/services/ssh/ssh_server/sshd_set_idle_timeout/rule.yml",
            }
        },
    )


class RuleIdentifiers(BaseModel):
    """Rule identifiers."""

    cce: str | None = Field(None, description="CCE identifier")
    cis: list[str] | None = Field(None, description="CIS benchmark references")
    nist: list[str] | None = Field(None, description="NIST control references")
    stigid: str | None = Field(None, description="STIG identifier")

    model_config = ConfigDict(
        extra="allow",  # Allow additional identifiers
    )


class RuleReferences(BaseModel):
    """Rule references to compliance frameworks."""

    nist: list[str] = Field(default_factory=list, description="NIST SP 800-53 references")
    cis: list[str] = Field(default_factory=list, description="CIS Benchmark references")
    cui: list[str] = Field(default_factory=list, description="CUI references")
    disa: list[str] = Field(default_factory=list, description="DISA STIG references")
    isa62443: list[str] = Field(default_factory=list, description="ISA-62443 references")
    pcidss: list[str] = Field(default_factory=list, description="PCI-DSS references")
    hipaa: list[str] = Field(default_factory=list, description="HIPAA references")

    model_config = ConfigDict(
        extra="allow",  # Allow additional reference frameworks
    )


class RuleRenderedContent(BaseModel):
    """Rendered content for a rule (from build artifacts)."""

    product: str = Field(..., description="Product this was rendered for")
    rendered_yaml: str | None = Field(None, description="Fully rendered YAML (variables expanded)")
    rendered_oval: str | None = Field(None, description="Rendered OVAL check content")
    rendered_remediations: dict[str, str] = Field(
        default_factory=dict, description="Rendered remediation scripts by type"
    )
    build_path: str = Field(..., description="Path to build artifact")
    build_time: datetime | None = Field(None, description="When this was built")

    # Metadata (always included, even in summary mode)
    yaml_size: int = Field(default=0, description="Size of rendered YAML in bytes")
    oval_size: int = Field(default=0, description="Size of rendered OVAL in bytes")
    remediation_sizes: dict[str, int] = Field(
        default_factory=dict, description="Sizes of remediations by type"
    )
    has_yaml: bool = Field(default=False, description="Whether YAML is available")
    has_oval: bool = Field(default=False, description="Whether OVAL is available")
    available_remediations: list[str] = Field(
        default_factory=list, description="Available remediation types"
    )


class RuleDetails(BaseModel):
    """Detailed information about a rule."""

    rule_id: str = Field(..., description="Rule identifier")
    title: str = Field(..., description="Rule title")
    description: str = Field(..., description="Full description")
    rationale: str | None = Field(None, description="Rationale for the rule")
    severity: str = Field(..., description="Severity level")
    identifiers: RuleIdentifiers = Field(
        default_factory=RuleIdentifiers, description="Rule identifiers"
    )
    references: RuleReferences = Field(
        default_factory=RuleReferences, description="Compliance framework references"
    )
    products: list[str] = Field(default_factory=list, description="Applicable products")
    platforms: list[str] = Field(default_factory=list, description="Applicable platforms")
    remediations: dict[str, bool] = Field(
        default_factory=dict,
        description="Available remediations (bash, ansible, anaconda, etc.)",
    )
    checks: dict[str, bool] = Field(
        default_factory=dict, description="Available checks (oval, etc.)"
    )
    test_scenarios: list[str] = Field(default_factory=list, description="Available test scenarios")
    file_path: str = Field(..., description="Path to rule.yml file")
    rule_dir: str = Field(..., description="Path to rule directory")
    last_modified: datetime | None = Field(None, description="Last modification timestamp")
    template: dict[str, Any] | None = Field(
        None, description="Template information if rule uses a template"
    )
    rendered: dict[str, RuleRenderedContent] | None = Field(
        None,
        description="Rendered content from build artifacts, keyed by product. "
        "Only populated if include_rendered=True and builds exist.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "rule_id": "sshd_set_idle_timeout",
                "title": "Set SSH Idle Timeout Interval",
                "description": "SSH allows administrators to set an idle timeout...",
                "rationale": "Terminating an idle session...",
                "severity": "medium",
                "identifiers": {"cce": "CCE-80906-3", "stigid": "RHEL-09-255030"},
                "references": {
                    "nist": ["AC-2(5)", "SC-10"],
                    "disa": ["RHEL-09-255030"],
                },
                "products": ["rhel7", "rhel8", "rhel9"],
                "platforms": ["machine"],
                "remediations": {"bash": True, "ansible": True, "anaconda": True},
                "checks": {"oval": True},
                "test_scenarios": ["correct_value.pass.sh", "wrong_value.fail.sh"],
                "file_path": "linux_os/guide/services/ssh/ssh_server/sshd_set_idle_timeout/rule.yml",
                "rule_dir": "linux_os/guide/services/ssh/ssh_server/sshd_set_idle_timeout",
            }
        },
    )


class RuleProductAvailability(BaseModel):
    """Cross-product availability information for a rule."""

    rule_id: str = Field(..., description="Rule identifier")
    products_with_identifiers: list[str] = Field(
        default_factory=list,
        description="Products from cce@/stigid@ keys in rule.yml",
    )
    products_in_profiles: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Product -> selectable profile names that select this rule; hidden profiles are omitted",
    )
    platforms: list[str] = Field(
        default_factory=list, description="Platform constraints from rule.yml"
    )
    template: dict[str, Any] | None = Field(
        default=None, description="Template info if rule is templated"
    )
    has_build_artifacts: dict[str, bool] = Field(
        default_factory=dict,
        description=(
            "Checked built product -> whether build/<product>/rules/<rule_id>.json "
            "can be loaded. OVAL or remediation files alone do not make this true. "
            "Omitted products have no reported result; false means no rendered rule JSON."
        ),
    )


class ValidationError(BaseModel):
    """Validation error details."""

    field: str = Field(..., description="Field or location of error")
    error: str = Field(..., description="Error message")
    line: int | None = Field(None, description="Line number if applicable")
    suggestion: str | None = Field(None, description="Suggested fix")


class ValidationResult(BaseModel):
    """Result of rule validation."""

    valid: bool = Field(..., description="Whether validation passed")
    errors: list[ValidationError] = Field(default_factory=list, description="Validation errors")
    warnings: list[ValidationError] = Field(default_factory=list, description="Validation warnings")
    fixes_applied: list[str] = Field(
        default_factory=list, description="Auto-fixes that were applied"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "valid": False,
                "errors": [
                    {
                        "field": "severity",
                        "error": "Invalid severity value 'critical'",
                        "line": 5,
                        "suggestion": "Use one of: low, medium, high, unknown",
                    }
                ],
                "warnings": [
                    {
                        "field": "references.nist",
                        "error": "NIST reference format may be incorrect",
                        "line": 12,
                    }
                ],
                "fixes_applied": [],
            }
        },
    )
