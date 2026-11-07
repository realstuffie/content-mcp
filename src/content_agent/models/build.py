"""Build job data models."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class BuildJobStatus(StrEnum):
    """Build job status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    ERROR = "error"


class BuildJobType(StrEnum):
    """Type of build job."""

    PRODUCT = "product"
    RULE = "rule"


class BuildJobId(BaseModel):
    """Build job identifier returned when starting a build."""

    job_id: str = Field(..., description="Unique job identifier")
    job_type: BuildJobType = Field(..., description="Type of build job")
    product: str = Field(..., description="Product being built")
    rule_id: str | None = Field(None, description="Rule ID if building single rule")
    message: str = Field(..., description="Informational message")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_id": "build_1234567890",
                "job_type": "rule",
                "product": "rhel9",
                "rule_id": "sshd_set_idle_timeout",
                "message": "Build job submitted successfully",
            }
        },
    )


class BuildArtifact(BaseModel):
    """Build artifact information."""

    name: str = Field(..., description="Artifact filename")
    path: str = Field(..., description="Full path to artifact")
    type: str = Field(..., description="Artifact type (datastream, playbook, guide, etc.)")
    size: int | None = Field(None, description="File size in bytes")


class BuildStatus(BaseModel):
    """Status of a build job."""

    job_id: str = Field(..., description="Job identifier")
    status: BuildJobStatus = Field(..., description="Current job status")
    job_type: BuildJobType = Field(..., description="Type of build job")
    product: str = Field(..., description="Product being built")
    rule_id: str | None = Field(None, description="Rule ID if building single rule")
    started_at: datetime = Field(..., description="When job started")
    completed_at: datetime | None = Field(None, description="When job completed")
    duration_seconds: float | None = Field(None, description="Job duration in seconds")
    exit_code: int | None = Field(None, description="Process exit code")
    stdout: str = Field(default="", description="Standard output")
    stderr: str = Field(default="", description="Standard error")
    artifacts: list[BuildArtifact] = Field(default_factory=list, description="Generated artifacts")
    error_message: str | None = Field(None, description="Error message if failed")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_id": "build_1234567890",
                "status": "completed",
                "job_type": "rule",
                "product": "rhel9",
                "rule_id": "sshd_set_idle_timeout",
                "started_at": "2026-01-28T10:30:00Z",
                "completed_at": "2026-01-28T10:32:15Z",
                "duration_seconds": 135.5,
                "exit_code": 0,
                "stdout": "Building RHEL 9...\nBuild completed successfully",
                "stderr": "",
                "artifacts": [
                    {
                        "name": "ssg-rhel9-ds.xml",
                        "path": "/path/to/build/ssg-rhel9-ds.xml",
                        "type": "datastream",
                        "size": 1048576,
                    }
                ],
            }
        },
    )


class RenderedRule(BaseModel):
    """Rendered rule content from build directory (after Jinja processing)."""

    rule_id: str = Field(..., description="Rule identifier")
    product: str = Field(..., description="Product this rule was built for")
    rendered_yaml: str | None = Field(None, description="Fully rendered YAML content")
    rendered_oval: str | None = Field(None, description="Rendered OVAL check content")
    rendered_remediations: dict[str, str] = Field(
        default_factory=dict,
        description="Rendered remediation scripts by type (bash, ansible, etc.)",
    )
    build_path: str = Field(..., description="Path to build artifact directory")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "rule_id": "sshd_set_idle_timeout",
                "product": "rhel9",
                "rendered_yaml": "title: Set SSH Idle Timeout...",
                "rendered_oval": "<def-group>...</def-group>",
                "rendered_remediations": {
                    "bash": "#!/bin/bash\necho 'ClientAliveInterval 300' >> /etc/ssh/sshd_config",
                },
                "build_path": "build/rhel9/rules/sshd_set_idle_timeout",
            }
        },
    )


class DatastreamInfo(BaseModel):
    """Information about a built datastream."""

    product: str = Field(..., description="Product identifier")
    datastream_path: str = Field(..., description="Path to datastream file")
    file_size: int = Field(..., description="Datastream file size in bytes")
    build_time: datetime | None = Field(None, description="When the datastream was built")
    profiles_count: int = Field(default=0, description="Number of profiles in the datastream")
    rules_count: int = Field(default=0, description="Number of rules in the datastream")
    exists: bool = Field(..., description="Whether the datastream file exists")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "product": "rhel9",
                "datastream_path": "build/ssg-rhel9-ds.xml",
                "file_size": 10485760,
                "build_time": "2026-01-28T10:32:15Z",
                "profiles_count": 15,
                "rules_count": 450,
                "exists": True,
            }
        },
    )


class RenderSearchResult(BaseModel):
    """Search result from rendered content."""

    rule_id: str = Field(..., description="Rule identifier")
    product: str = Field(..., description="Product")
    match_type: str = Field(..., description="Type of match (yaml, oval, remediation)")
    match_snippet: str = Field(..., description="Snippet showing the match")
    file_path: str = Field(..., description="Path to the matching file")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "rule_id": "sshd_set_idle_timeout",
                "product": "rhel9",
                "match_type": "remediation_bash",
                "match_snippet": "...ClientAliveInterval 300...",
                "file_path": "build/rhel9/rules/sshd_set_idle_timeout/bash.sh",
            }
        },
    )
