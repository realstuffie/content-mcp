"""Product data models."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProductSummary(BaseModel):
    """Summary information about a product."""

    product_id: str = Field(..., description="Product identifier (e.g., rhel9, fedora, ocp4)")
    name: str = Field(..., description="Human-readable product name")
    product_type: str = Field(..., description="Product type (e.g., rhel, fedora, ocp)")
    version: str | None = Field(None, description="Product version if applicable")
    description: str | None = Field(None, description="Product description")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "product_id": "rhel9",
                "name": "Red Hat Enterprise Linux 9",
                "product_type": "rhel",
                "version": "9",
                "description": "Security compliance content for RHEL 9",
            }
        },
    )


class ProductStats(BaseModel):
    """Statistics about a product's content."""

    rule_count: int = Field(..., description="Total number of rules")
    profile_count: int = Field(..., description="Total number of profiles")
    remediation_count: int = Field(..., description="Total number of remediations")
    test_count: int = Field(..., description="Total number of test scenarios")


class ProductDetails(BaseModel):
    """Detailed information about a product."""

    product_id: str = Field(..., description="Product identifier")
    name: str = Field(..., description="Human-readable product name")
    product_type: str = Field(..., description="Product type")
    version: str | None = Field(None, description="Product version")
    description: str | None = Field(None, description="Product description")
    profiles: list[str] = Field(default_factory=list, description="List of available profile IDs")
    benchmark_root: str = Field(..., description="Path to product benchmark directory")
    product_dir: str = Field(..., description="Path to product directory")
    cpe: str | None = Field(None, description="CPE identifier")
    stats: ProductStats | None = Field(None, description="Product statistics")
    last_modified: datetime | None = Field(None, description="Last modification timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "product_id": "rhel9",
                "name": "Red Hat Enterprise Linux 9",
                "product_type": "rhel",
                "version": "9",
                "description": "Security compliance content for RHEL 9",
                "profiles": ["ospp", "stig", "cis", "pci-dss"],
                "benchmark_root": "linux_os/guide",
                "product_dir": "products/rhel9",
                "cpe": "cpe:/o:redhat:enterprise_linux:9",
                "stats": {
                    "rule_count": 450,
                    "profile_count": 12,
                    "remediation_count": 800,
                    "test_count": 1200,
                },
            }
        },
    )
