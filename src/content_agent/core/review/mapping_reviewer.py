"""Rule mapping review tools."""

import logging
from pathlib import Path

from content_agent.core.ai.rule_mapper import RuleMapper
from content_agent.core.discovery.controls import ControlDiscovery
from content_agent.core.scaffolding.control_validators import ControlValidator
from content_agent.models.control import (
    ControlReviewReport,
    ControlValidationResult,
    RuleSuggestion,
    flatten_requirements,
)

logger = logging.getLogger(__name__)


class MappingReviewer:
    """Review AI-suggested rule mappings."""

    def __init__(
        self,
        rule_mapper: RuleMapper | None = None,
    ):
        """Initialize mapping reviewer.

        Args:
            rule_mapper: Optional RuleMapper instance
        """
        self.rule_mapper = rule_mapper
        self.control_discovery = ControlDiscovery()
        self.validator = ControlValidator()

    def review_control_file(
        self,
        control_file_path: Path,
        generate_suggestions: bool = True,
    ) -> ControlReviewReport:
        """Review a generated control file.

        Args:
            control_file_path: Path to control file to review
            generate_suggestions: Whether to generate AI rule suggestions

        Returns:
            ControlReviewReport with review results
        """
        logger.info(f"Reviewing control file: {control_file_path}")

        try:
            # Parse control file
            control = self.control_discovery.parse_control_file(control_file_path)
            if not control:
                return ControlReviewReport(
                    policy_id="unknown",
                    total_requirements=0,
                    requirements_with_rules=0,
                    requirements_without_rules=0,
                    validation_result=ControlValidationResult(
                        valid=False,
                        errors=[f"Failed to parse control file: {control_file_path}"],
                        warnings=[],
                        file_path=control_file_path,
                    ),
                    text_comparisons=[],
                    rule_suggestions={},
                    issues=[],
                )

            # Validate control file
            validation_result = self.validator.validate_control_file(control_file_path)

            # Count requirements with/without rules
            all_requirements = flatten_requirements(control.controls)
            requirements_with_rules = sum(1 for req in all_requirements if req.rules)
            requirements_without_rules = len(all_requirements) - requirements_with_rules

            # Generate AI suggestions if requested and mapper available
            rule_suggestions = {}
            if generate_suggestions and self.rule_mapper:
                for req in all_requirements:
                    if not req.rules:  # Only suggest for unmapped requirements
                        try:
                            suggestions = self.rule_mapper.suggest_rules(req)
                            if suggestions:
                                rule_suggestions[req.id] = suggestions
                        except Exception as e:
                            logger.warning(f"Failed to generate suggestions for {req.id}: {e}")

            # Identify issues
            issues = []

            # Check for requirements without rules
            if requirements_without_rules > 0:
                issues.append(f"{requirements_without_rules} requirements have no mapped rules")

            # Check for low-confidence suggestions
            for req_id, suggestions in rule_suggestions.items():
                if suggestions and all(s.confidence < 0.5 for s in suggestions):
                    issues.append(f"Requirement {req_id} has only low-confidence rule suggestions")

            # Add validation errors as issues
            issues.extend(validation_result.errors)

            return ControlReviewReport(
                policy_id=control.id,
                total_requirements=len(all_requirements),
                requirements_with_rules=requirements_with_rules,
                requirements_without_rules=requirements_without_rules,
                validation_result=validation_result,
                text_comparisons=[],  # Can be populated separately
                rule_suggestions=rule_suggestions,
                issues=issues,
            )

        except Exception as e:
            logger.error(f"Review failed: {e}")
            return ControlReviewReport(
                policy_id="unknown",
                total_requirements=0,
                requirements_with_rules=0,
                requirements_without_rules=0,
                validation_result=ControlValidationResult(
                    valid=False,
                    errors=[f"Review failed: {e}"],
                    warnings=[],
                ),
                text_comparisons=[],
                rule_suggestions={},
                issues=[str(e)],
            )

    def format_suggestions_report(
        self,
        suggestions: dict[str, list[RuleSuggestion]],
    ) -> str:
        """Format rule suggestions as human-readable report.

        Args:
            suggestions: Dictionary mapping requirement ID to suggestions

        Returns:
            Formatted report text
        """
        report_lines = [
            "# Rule Mapping Suggestions",
            "",
            f"Total requirements with suggestions: {len(suggestions)}",
            "",
        ]

        for req_id, req_suggestions in suggestions.items():
            report_lines.extend(
                [
                    f"## Requirement: {req_id}",
                    "",
                    f"Suggested rules: {len(req_suggestions)}",
                    "",
                ]
            )

            for idx, suggestion in enumerate(req_suggestions, 1):
                confidence_pct = suggestion.confidence * 100
                report_lines.extend(
                    [
                        f"### {idx}. {suggestion.rule_id}",
                        f"- **Confidence**: {confidence_pct:.1f}%",
                        f"- **Match Type**: {suggestion.match_type}",
                        f"- **Reasoning**: {suggestion.reasoning}",
                        "",
                    ]
                )

        return "\n".join(report_lines)

    def format_review_report(self, report: ControlReviewReport) -> str:
        """Format review report as human-readable text.

        Args:
            report: ControlReviewReport to format

        Returns:
            Formatted report text
        """
        lines = [
            f"# Control Review Report: {report.policy_id}",
            "",
            "## Summary",
            f"- Total requirements: {report.total_requirements}",
            f"- Requirements with rules: {report.requirements_with_rules}",
            f"- Requirements without rules: {report.requirements_without_rules}",
            (
                f"- Coverage: {report.requirements_with_rules / report.total_requirements * 100:.1f}%"
                if report.total_requirements > 0
                else "- Coverage: 0%"
            ),
            "",
        ]

        # Validation results
        lines.extend(
            [
                "## Validation",
                f"- Status: {'PASSED' if report.validation_result.valid else 'FAILED'}",
                "",
            ]
        )

        if report.validation_result.errors:
            lines.append("### Errors")
            for error in report.validation_result.errors:
                lines.append(f"- {error}")
            lines.append("")

        if report.validation_result.warnings:
            lines.append("### Warnings")
            for warning in report.validation_result.warnings:
                lines.append(f"- {warning}")
            lines.append("")

        # Issues
        if report.issues:
            lines.append("## Issues")
            for issue in report.issues:
                lines.append(f"- {issue}")
            lines.append("")

        # Rule suggestions summary
        if report.rule_suggestions:
            lines.extend(
                [
                    "## Rule Suggestions",
                    f"- Requirements with suggestions: {len(report.rule_suggestions)}",
                    "",
                ]
            )

            # Show top suggestions
            for req_id, suggestions in list(report.rule_suggestions.items())[:5]:
                if suggestions:
                    top_suggestion = suggestions[0]
                    lines.append(
                        f"- **{req_id}**: {top_suggestion.rule_id} ({top_suggestion.confidence*100:.0f}% confidence)"
                    )

            if len(report.rule_suggestions) > 5:
                lines.append(f"- ... and {len(report.rule_suggestions) - 5} more")

        return "\n".join(lines)
