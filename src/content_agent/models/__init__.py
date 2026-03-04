"""Data models for content-agent."""

from content_agent.models.build import (
    BuildArtifact,
    BuildJobId,
    BuildJobStatus,
    BuildJobType,
    BuildStatus,
    DatastreamInfo,
    RenderedRule,
    RenderSearchResult,
)
from content_agent.models.control import (
    ControlFile,
    ControlGenerationResult,
    ControlLevel,
    ControlRequirement,
    ControlReviewReport,
    ControlRuleIndex,
    ControlStats,
    ControlUpdateResult,
    ControlValidationResult,
    DocumentSection,
    ExtractedRequirement,
    IndexedRequirement,
    ParsedDocument,
    RuleSuggestion,
    SimilarRequirement,
)
from content_agent.models.product import ProductDetails, ProductStats, ProductSummary
from content_agent.models.profile import (
    ProfileDetails,
    ProfileSummary,
    ScaffoldingResult,
    TemplateParameter,
    TemplateSchema,
    TemplateSummary,
)
from content_agent.models.rule import (
    RuleDetails,
    RuleIdentifiers,
    RuleProductAvailability,
    RuleReferences,
    RuleRenderedContent,
    RuleSearchResult,
    ValidationError,
    ValidationResult,
)
from content_agent.models.test import (
    TestJobId,
    TestJobStatus,
    TestResults,
    TestScenarioResult,
    TestScenarioStatus,
)

__all__ = [
    # Build models
    "BuildArtifact",
    "BuildJobId",
    "BuildJobStatus",
    "BuildJobType",
    "BuildStatus",
    "DatastreamInfo",
    "RenderedRule",
    "RenderSearchResult",
    # Control models
    "ControlFile",
    "ControlGenerationResult",
    "ControlLevel",
    "ControlRequirement",
    "ControlReviewReport",
    "ControlRuleIndex",
    "ControlStats",
    "ControlUpdateResult",
    "ControlValidationResult",
    "DocumentSection",
    "ExtractedRequirement",
    "IndexedRequirement",
    "ParsedDocument",
    "RuleSuggestion",
    "SimilarRequirement",
    # Product models
    "ProductDetails",
    "ProductStats",
    "ProductSummary",
    # Profile models
    "ProfileDetails",
    "ProfileSummary",
    "ScaffoldingResult",
    "TemplateParameter",
    "TemplateSchema",
    "TemplateSummary",
    # Rule models
    "RuleDetails",
    "RuleIdentifiers",
    "RuleProductAvailability",
    "RuleReferences",
    "RuleRenderedContent",
    "RuleSearchResult",
    "ValidationError",
    "ValidationResult",
    # Test models
    "TestJobId",
    "TestJobStatus",
    "TestResults",
    "TestScenarioResult",
    "TestScenarioStatus",
]
