"""Profile data models."""

from typing import Optional

from pydantic import BaseModel, Field


class ProfileSummary(BaseModel):
    """Summary information about a profile."""

    profile_id: str = Field(..., description="Profile identifier")
    title: str = Field(..., description="Profile title")
    description: str | None = Field(None, description="Profile description")
    product: str = Field(..., description="Product this profile belongs to")
    rule_count: int | None = Field(None, description="Number of rules in profile")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "profile_id": "ospp",
                "title": "Protection Profile for General Purpose Operating Systems",
                "description": "This profile reflects mandatory configuration...",
                "product": "rhel9",
                "rule_count": 156,
            }
        }


class ProfileDetails(BaseModel):
    """Detailed information about a profile."""

    profile_id: str = Field(..., description="Profile identifier")
    title: str = Field(..., description="Profile title")
    description: str = Field(..., description="Full description")
    product: str = Field(..., description="Product identifier")
    extends: str | None = Field(None, description="Parent profile if this extends another")
    selections: list[str] = Field(default_factory=list, description="Selected rule IDs")
    variables: dict[str, str] = Field(
        default_factory=dict, description="Profile-specific variable values"
    )
    file_path: str = Field(..., description="Path to profile file")
    rule_count: int = Field(..., description="Total number of rules")
    control_file: str | None = Field(
        None, description="Control file if profile is based on controls"
    )

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "profile_id": "ospp",
                "title": "Protection Profile for General Purpose Operating Systems",
                "description": "This profile reflects mandatory configuration...",
                "product": "rhel9",
                "extends": None,
                "selections": ["sshd_set_idle_timeout", "accounts_password_minlen"],
                "variables": {"var_sshd_idle_timeout_value": "300"},
                "file_path": "products/rhel9/profiles/ospp.profile",
                "rule_count": 156,
                "control_file": "controls/ospp.yml",
            }
        }


class TemplateSummary(BaseModel):
    """Summary information about a template."""

    name: str = Field(..., description="Template name")
    description: str | None = Field(None, description="Template description")
    language: str = Field(..., description="Template language (jinja2, etc.)")
    category: str | None = Field(None, description="Template category")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "name": "sshd_lineinfile",
                "description": "Template for SSH daemon configuration options",
                "language": "jinja2",
                "category": "ssh",
            }
        }


class TemplateParameter(BaseModel):
    """Template parameter definition."""

    name: str = Field(..., description="Parameter name")
    type: str = Field(..., description="Parameter type")
    required: bool = Field(..., description="Whether parameter is required")
    description: str | None = Field(None, description="Parameter description")
    default: str | None = Field(None, description="Default value")
    options: list[str] | None = Field(
        None, description="Valid options if parameter has enumerated values"
    )


class TemplateSchema(BaseModel):
    """Schema definition for a template."""

    name: str = Field(..., description="Template name")
    description: str | None = Field(None, description="Template description")
    parameters: list[TemplateParameter] = Field(
        default_factory=list, description="Template parameters"
    )
    example_usage: dict[str, str] | None = Field(None, description="Example parameter values")
    documentation: str | None = Field(
        None, description="Template reference documentation from template_reference.md"
    )

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "name": "sshd_lineinfile",
                "description": "Template for SSH daemon configuration options",
                "parameters": [
                    {
                        "name": "parameter",
                        "type": "string",
                        "required": True,
                        "description": "SSH configuration parameter name",
                    },
                    {
                        "name": "value",
                        "type": "string",
                        "required": True,
                        "description": "Expected value for the parameter",
                    },
                ],
                "example_usage": {
                    "parameter": "ClientAliveInterval",
                    "value": "300",
                },
            }
        }


class ScaffoldingResult(BaseModel):
    """Result of scaffolding operation."""

    success: bool = Field(..., description="Whether operation succeeded")
    rule_id: str = Field(..., description="Rule identifier")
    files_created: list[str] = Field(default_factory=list, description="Files that were created")
    rule_dir: str = Field(..., description="Path to rule directory")
    message: str = Field(..., description="Success or error message")
    validation: Optional["ValidationResult"] = Field(  # Forward reference
        None, description="Validation result if validation was performed"
    )

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "success": True,
                "rule_id": "sshd_max_auth_tries",
                "files_created": [
                    "linux_os/guide/services/ssh/ssh_server/sshd_max_auth_tries/rule.yml",
                    "linux_os/guide/services/ssh/ssh_server/sshd_max_auth_tries/bash/",
                    "linux_os/guide/services/ssh/ssh_server/sshd_max_auth_tries/ansible/",
                ],
                "rule_dir": "linux_os/guide/services/ssh/ssh_server/sshd_max_auth_tries",
                "message": "Rule scaffolding created successfully",
            }
        }


# Import at end to avoid circular import
from content_agent.models.rule import ValidationResult

ScaffoldingResult.model_rebuild()
