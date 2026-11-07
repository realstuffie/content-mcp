"""Data models for control files and policy documents."""

from datetime import datetime
from pathlib import Path
from typing import Any, Literal, get_args

from pydantic import BaseModel, Field, model_validator

# The statuses ComplianceAsCode accepts (shared/schemas/control.json)
ControlStatus = Literal[
    "automated",
    "documentation",
    "does not meet",
    "inherently met",
    "manual",
    "not applicable",
    "partial",
    "pending",
    "planned",
    "supported",
]
CONTROL_STATUSES: tuple[str, ...] = get_args(ControlStatus)


class ControlRequirement(BaseModel):
    """Single control requirement extracted from a policy document."""

    id: str = Field(
        ...,
        description="Requirement ID (e.g., 'AC-2(5)', '1.1.1')",
    )
    title: str = Field(
        default="",
        description="Requirement title or short description (optional in control files)",
    )
    description: str | None = Field(
        default=None,
        description="Full requirement text (exact from source, no rewording)",
    )
    rules: list[str] = Field(
        default_factory=list,
        description="Rule IDs that implement this control",
    )
    related_rules: list[str] = Field(
        default_factory=list,
        description="Rule IDs that are related but not directly implementing",
    )
    status: ControlStatus = Field(
        default="pending",
        description="Implementation status of this control",
    )
    references: dict[str, list[str]] = Field(
        default_factory=dict,
        description="External references (NIST, CIS, etc.)",
    )
    notes: str | None = Field(
        default=None,
        description="Additional notes or comments",
    )
    levels: list[str] = Field(
        default_factory=list,
        description="Compliance levels (e.g., ['low', 'medium', 'high'])",
    )
    section: str | None = Field(
        default=None,
        description="Section identifier this requirement belongs to",
    )
    controls: list["ControlRequirement"] = Field(
        default_factory=list,
        description="Nested child requirements",
    )
    referenced_controls: list[str] = Field(
        default_factory=list,
        description="References to requirements in other control files "
        "(e.g., 'nist_800_53:ac-2', 'cis_ocp:all:level_2')",
    )

    @model_validator(mode="before")
    @classmethod
    def _split_control_references(cls, data: Any) -> Any:
        """Move string entries of `controls` into `referenced_controls`.

        In ComplianceAsCode control files a requirement's `controls` list can hold
        nested requirements or references to requirements of other control files.
        """
        if isinstance(data, dict) and isinstance(data.get("controls"), list):
            children = data["controls"]
            refs = [child for child in children if isinstance(child, str)]
            if refs:
                data = {
                    **data,
                    "controls": [child for child in children if not isinstance(child, str)],
                    "referenced_controls": [*data.get("referenced_controls", []), *refs],
                }
        return data


def flatten_requirements(controls: list[ControlRequirement]) -> list[ControlRequirement]:
    """Return every requirement in a control tree, parents before their children.

    Args:
        controls: Top-level requirements, which may contain nested requirements

    Returns:
        Flat list of all requirements at every depth
    """
    flat: list[ControlRequirement] = []
    for ctrl in controls:
        flat.append(ctrl)
        flat.extend(flatten_requirements(ctrl.controls))
    return flat


class ControlLevel(BaseModel):
    """Compliance level definition (e.g., Level 1, Level 2)."""

    id: str = Field(..., description="Level identifier (e.g., 'high', 'medium', 'low')")
    title: str | None = Field(
        default=None,
        description="Level title",
    )
    description: str | None = Field(
        default=None,
        description="Level description",
    )
    inherits_from: list[str] | None = Field(
        default=None,
        description="Parent level IDs this level inherits from",
    )


class ControlFile(BaseModel):
    """Control framework file representation.

    Supports both legacy format (with description, source_document, includes)
    and ComplianceAsCode format (with policy, source, controls_dir, version).
    """

    id: str = Field(..., description="Policy/framework ID")
    title: str = Field(..., description="Policy/framework name")

    # ComplianceAsCode format fields
    policy: str | None = Field(
        default=None,
        description="Policy name (same as title in CAC format)",
    )
    version: str | None = Field(
        default=None,
        description="Version string (e.g., 'v3r1')",
    )
    source: str | None = Field(
        default=None,
        description="Source URL (CAC format)",
    )
    controls_dir: str | None = Field(
        default=None,
        description="Directory containing individual control files (CAC format)",
    )

    # Legacy format fields (optional for backward compatibility)
    description: str | None = Field(
        default=None,
        description="Policy description",
    )
    source_document: str | None = Field(
        default=None,
        description="Source file path or URL (legacy format)",
    )
    includes: list[str] = Field(
        default_factory=list,
        description="Paths to included control files (legacy format)",
    )

    # Common fields
    controls: list[ControlRequirement] = Field(
        default_factory=list,
        description="List of control requirements",
    )
    levels: list[ControlLevel] | None = Field(
        default=None,
        description="Compliance levels if applicable",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata",
    )
    parse_errors: list[str] = Field(
        default_factory=list,
        description="Errors encountered while parsing individual requirements",
    )
    source_dir: Path | None = Field(
        default=None,
        description="Directory from which this control file was loaded",
    )


class DocumentSection(BaseModel):
    """Section extracted from a policy document."""

    id: str = Field(..., description="Section identifier")
    title: str = Field(..., description="Section title")
    level: int = Field(..., description="Heading level (1-6)")
    content: str = Field(..., description="Section content text")
    subsections: list["DocumentSection"] = Field(
        default_factory=list,
        description="Nested subsections",
    )
    parent_id: str | None = Field(
        default=None,
        description="Parent section ID if nested",
    )


class ExtractedRequirement(BaseModel):
    """Requirement extracted from document before structuring."""

    text: str = Field(..., description="Exact requirement text from document")
    section_id: str = Field(..., description="Section this requirement belongs to")
    section_title: str = Field(..., description="Section title")
    potential_id: str | None = Field(
        default=None,
        description="Potential requirement ID if detected",
    )
    context: str | None = Field(
        default=None,
        description="Surrounding context or notes",
    )


class ParsedDocument(BaseModel):
    """Parsed security policy document."""

    title: str = Field(..., description="Document title")
    sections: list[DocumentSection] = Field(
        default_factory=list,
        description="Document sections hierarchy",
    )
    requirements: list[ExtractedRequirement] = Field(
        default_factory=list,
        description="Extracted requirements",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Document metadata (author, date, version, etc.)",
    )
    source_path: str | None = Field(
        default=None,
        description="Source file path or URL",
    )
    source_type: Literal["pdf", "markdown", "text", "html"] = Field(
        ...,
        description="Source document type",
    )
    parsed_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when document was parsed",
    )


class RuleSuggestion(BaseModel):
    """AI-suggested rule mapping for a requirement."""

    rule_id: str = Field(..., description="Suggested rule ID")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0-1.0)",
    )
    reasoning: str = Field(
        ...,
        description="Explanation for why this rule was suggested",
    )
    match_type: Literal["exact_ref", "keyword", "semantic", "description"] = Field(
        ...,
        description="Type of match that led to this suggestion",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the suggestion",
    )


class ControlGenerationResult(BaseModel):
    """Result of control file generation."""

    policy_id: str = Field(..., description="Generated policy ID")
    parent_file_path: Path = Field(..., description="Path to parent control file")
    requirement_files: list[Path] = Field(
        default_factory=list,
        description="Paths to individual requirement files",
    )
    total_requirements: int = Field(..., description="Total requirements generated")
    sections: list[str] = Field(
        default_factory=list,
        description="Section identifiers created",
    )
    success: bool = Field(..., description="Whether generation was successful")
    errors: list[str] = Field(
        default_factory=list,
        description="Any errors encountered",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Any warnings generated",
    )


class ControlValidationResult(BaseModel):
    """Result of control file validation."""

    valid: bool = Field(..., description="Whether validation passed")
    errors: list[str] = Field(
        default_factory=list,
        description="Validation errors",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Validation warnings",
    )
    file_path: Path | None = Field(
        default=None,
        description="Path to validated file",
    )


class ControlReviewReport(BaseModel):
    """Report from reviewing generated control files."""

    policy_id: str = Field(..., description="Policy ID being reviewed")
    total_requirements: int = Field(..., description="Total requirements")
    requirements_with_rules: int = Field(
        ...,
        description="Requirements with at least one rule mapped",
    )
    requirements_without_rules: int = Field(
        ...,
        description="Requirements with no rules mapped",
    )
    validation_result: ControlValidationResult = Field(
        ...,
        description="Validation results",
    )
    text_comparisons: list[dict[str, str]] = Field(
        default_factory=list,
        description="Text comparison results",
    )
    rule_suggestions: dict[str, list[RuleSuggestion]] = Field(
        default_factory=dict,
        description="AI rule suggestions per requirement",
    )
    issues: list[str] = Field(
        default_factory=list,
        description="Issues found during review",
    )


class IndexedRequirement(BaseModel):
    """A requirement with its parent control context, for cross-framework indexing."""

    control_id: str = Field(..., description="Parent control framework ID (e.g., 'anssi', 'hipaa')")
    requirement_id: str = Field(
        ..., description="Requirement ID within the control (e.g., 'R1', 'AC-2(5)')"
    )
    title: str = Field(..., description="Requirement title")
    description: str = Field(
        default="", description="Requirement description (truncated for index)"
    )
    rules: list[str] = Field(default_factory=list, description="Mapped rule IDs")
    status: str = Field(default="pending", description="Implementation status")
    levels: list[str] = Field(default_factory=list, description="Compliance levels")


class ControlRuleIndex(BaseModel):
    """Complete index of all requirements and rule mappings across control frameworks."""

    total_controls: int = Field(..., description="Number of control frameworks indexed")
    total_requirements: int = Field(..., description="Total requirements across all frameworks")
    total_mapped_rules: int = Field(..., description="Total unique rule IDs mapped")
    requirements: list[IndexedRequirement] = Field(
        default_factory=list, description="All indexed requirements"
    )


class SimilarRequirement(BaseModel):
    """A requirement found via text similarity search."""

    control_id: str = Field(..., description="Parent control framework ID")
    requirement_id: str = Field(..., description="Requirement ID")
    title: str = Field(..., description="Requirement title")
    description: str = Field(..., description="Requirement description")
    rules: list[str] = Field(default_factory=list, description="Mapped rule IDs")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    matching_terms: list[str] = Field(default_factory=list, description="Overlapping keywords")


class ControlStats(BaseModel):
    """Aggregate statistics for a control file's requirements."""

    control_id: str = Field(..., description="Control framework identifier")
    title: str = Field(..., description="Control framework title")
    total: int = Field(..., description="Total number of requirements")
    by_status: dict[str, int] = Field(
        default_factory=dict,
        description="Requirement counts keyed by status",
    )
    mapped: int = Field(..., description="Requirements with at least one rule")
    unmapped: int = Field(..., description="Requirements with no rules")


class RequirementFilePath(BaseModel):
    """Resolved file path for a control requirement."""

    control_id: str = Field(..., description="Control framework ID")
    requirement_id: str = Field(..., description="Requirement ID")
    file_path: Path = Field(
        ..., description="Absolute path to the file containing this requirement"
    )
    format: Literal["inline", "directory"] = Field(
        ...,
        description="Whether requirement is in a monolithic file (inline) or its own file (directory)",
    )
    exists: bool = Field(..., description="Whether the resolved file exists on disk")


class ControlUpdateResult(BaseModel):
    """Result of updating an existing control file."""

    file_path: Path = Field(..., description="Path to updated control file")
    requirements_added: int = Field(
        ...,
        description="Number of requirements added",
    )
    requirements_updated: int = Field(
        ...,
        description="Number of requirements updated",
    )
    requirements_unchanged: int = Field(
        ...,
        description="Number of requirements unchanged",
    )
    success: bool = Field(..., description="Whether update was successful")
    errors: list[str] = Field(
        default_factory=list,
        description="Errors encountered",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Problems that did not stop the update",
    )
