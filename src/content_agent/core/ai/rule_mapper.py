"""AI-powered rule mapping for control requirements."""

from pathlib import Path

from content_agent.core.ai.claude_client import ClaudeClient
from content_agent.core.discovery.rules import RuleDiscovery
from content_agent.models.control import ControlRequirement, RuleSuggestion


class RuleMapper:
    """Map control requirements to ComplianceAsCode rules using AI."""

    SYSTEM_PROMPT = """You are a security compliance expert. Your task is to suggest ComplianceAsCode rules that implement specific security control requirements.

You will be given:
1. A control requirement description
2. A list of available rules with their descriptions and references

Your task:
- Identify rules that implement or relate to the requirement
- Assign confidence scores (0.0-1.0) based on relevance
- Provide clear reasoning for each suggestion
- Classify match type: "exact_ref", "keyword", "semantic", or "description"

Match types:
- exact_ref: Rule explicitly references the requirement ID (e.g., NIST AC-2)
- keyword: Rule matches key technical terms from requirement
- semantic: Rule implements the control intent even if wording differs
- description: Rule description closely matches requirement

Confidence guidelines:
- 0.9-1.0: Direct implementation of the exact requirement
- 0.7-0.9: Implements major aspects of the requirement
- 0.5-0.7: Partially implements or addresses related concerns
- 0.3-0.5: Tangentially related
- 0.0-0.3: Weak or questionable relationship

Output Format:
Return a JSON array of suggestions:
[
  {
    "rule_id": "accounts_password_minlen_login_defs",
    "confidence": 0.85,
    "reasoning": "This rule enforces minimum password length which directly implements the password complexity requirement",
    "match_type": "semantic",
    "metadata": {}
  }
]

Be conservative - only suggest rules with confidence >= 0.3. Limit to top 10 most relevant rules."""

    def __init__(self, claude_client: ClaudeClient, content_path: Path | None = None):
        """Initialize rule mapper.

        Args:
            claude_client: Configured Claude client
            content_path: Path to ComplianceAsCode content repository
        """
        self.client = claude_client
        self.rule_discovery = RuleDiscovery()
        if content_path:
            self.rule_discovery.content_repo.content_path = content_path  # type: ignore[attr-defined]

    def suggest_rules(
        self,
        requirement: ControlRequirement,
        max_suggestions: int = 10,
        min_confidence: float = 0.3,
        cross_reference: bool = False,
        target_product: str | None = None,
    ) -> list[RuleSuggestion]:
        """Suggest rules for a control requirement.

        Args:
            requirement: Control requirement to map
            max_suggestions: Maximum number of suggestions
            min_confidence: Minimum confidence score
            cross_reference: Include rules from similar requirements in other frameworks
            target_product: Prioritize rules with identifiers for this product

        Returns:
            List of rule suggestions sorted by confidence (descending)
        """
        # Build context about available rules
        rules_context = self._build_rules_context(target_product=target_product)

        # Build prompt
        user_prompt = self._build_mapping_prompt(requirement, rules_context)

        # Append cross-framework evidence if requested
        if cross_reference and requirement.description:
            cross_ref_section = self._build_cross_reference_context(requirement.description)
            if cross_ref_section:
                user_prompt += "\n\n" + cross_ref_section

        # Get suggestions from Claude
        response = self.client.create_message(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        # Parse response
        suggestions_data = self.client.extract_json_response(response)

        # Convert to RuleSuggestion objects
        suggestions = []
        if isinstance(suggestions_data, list):
            for sug_data in suggestions_data:
                suggestion = RuleSuggestion(**sug_data)
                if suggestion.confidence >= min_confidence:
                    suggestions.append(suggestion)
        elif isinstance(suggestions_data, dict) and "suggestions" in suggestions_data:
            for sug_data in suggestions_data["suggestions"]:
                suggestion = RuleSuggestion(**sug_data)
                if suggestion.confidence >= min_confidence:
                    suggestions.append(suggestion)

        # Sort by confidence (descending) and limit
        suggestions.sort(key=lambda s: s.confidence, reverse=True)
        return suggestions[:max_suggestions]

    def suggest_rules_for_text(
        self,
        requirement_text: str,
        max_suggestions: int = 10,
        min_confidence: float = 0.3,
        cross_reference: bool = False,
        target_product: str | None = None,
    ) -> list[RuleSuggestion]:
        """Suggest rules for requirement text.

        Args:
            requirement_text: Requirement text
            max_suggestions: Maximum number of suggestions
            min_confidence: Minimum confidence score
            cross_reference: Include rules from similar requirements in other frameworks
            target_product: Prioritize rules with identifiers for this product

        Returns:
            List of rule suggestions
        """
        # Create temporary requirement object
        temp_requirement = ControlRequirement(
            id="temp",
            title="Temporary",
            description=requirement_text,
        )

        return self.suggest_rules(
            temp_requirement, max_suggestions, min_confidence, cross_reference, target_product
        )

    def _build_rules_context(self, limit: int = 100, target_product: str | None = None) -> str:
        """Build context string with available rules.

        Args:
            limit: Maximum number of rules to include
            target_product: If set, prioritize rules with identifiers for this product

        Returns:
            Formatted rules context
        """
        # Get all rules (or search for relevant ones)
        rules_result = self.rule_discovery.search_rules(limit=limit)
        rules = rules_result.items

        if not rules:
            return "No rules available in the content repository."

        if target_product:
            # Sort rules: those matching target_product first
            target_rules = [r for r in rules if target_product in r.products]
            other_rules = [r for r in rules if target_product not in r.products]

            context_parts = [
                f"Available rules for {target_product} ({len(target_rules)} matching, "
                f"{len(other_rules)} from other products):",
                "",
            ]

            for rule in target_rules:
                context_parts.append(f"- {rule.rule_id} [TARGET PRODUCT]:")
                if rule.title:
                    context_parts.append(f"  Title: {rule.title}")
                if rule.description:
                    desc = (
                        rule.description[:200] + "..."
                        if len(rule.description) > 200
                        else rule.description
                    )
                    context_parts.append(f"  Description: {desc}")
                context_parts.append("")

            if other_rules:
                context_parts.append("Rules available in other products (may need porting):")
                context_parts.append("")
                for rule in other_rules:
                    context_parts.append(
                        f"- {rule.rule_id} (products: {', '.join(rule.products)}):"
                    )
                    if rule.title:
                        context_parts.append(f"  Title: {rule.title}")
                    context_parts.append("")
        else:
            context_parts = [f"Available rules (showing {len(rules)}):", ""]

            for rule in rules:
                context_parts.append(f"- {rule.rule_id}:")
                if rule.title:
                    context_parts.append(f"  Title: {rule.title}")
                if rule.description:
                    desc = (
                        rule.description[:200] + "..."
                        if len(rule.description) > 200
                        else rule.description
                    )
                    context_parts.append(f"  Description: {desc}")
                context_parts.append("")

        return "\n".join(context_parts)

    def _build_cross_reference_context(self, requirement_text: str, max_similar: int = 10) -> str:
        """Build cross-framework evidence section from similar requirements.

        Args:
            requirement_text: The requirement text to find similarities for
            max_similar: Maximum number of similar requirements to include

        Returns:
            Formatted cross-reference context string, or empty string if none found
        """
        try:
            from content_agent.core.discovery.controls import ControlDiscovery

            discovery = ControlDiscovery()
            similar = discovery.find_similar_requirements(
                requirement_text=requirement_text,
                max_results=max_similar,
                min_similarity=0.15,
            )

            if not similar:
                return ""

            parts = [
                "Cross-framework evidence — rules mapped to similar requirements in other "
                "control frameworks:",
                "",
            ]

            for req in similar:
                if not req.rules:
                    continue
                parts.append(
                    f"- [{req.control_id}] {req.requirement_id}: {req.title} "
                    f"(similarity: {req.similarity_score:.2f})"
                )
                parts.append(f"  Mapped rules: {', '.join(req.rules)}")
                parts.append("")

            if len(parts) <= 2:
                return ""

            return "\n".join(parts)
        except Exception:
            return ""

    def _build_mapping_prompt(self, requirement: ControlRequirement, rules_context: str) -> str:
        """Build prompt for rule mapping.

        Args:
            requirement: Requirement to map
            rules_context: Context about available rules

        Returns:
            Formatted prompt
        """
        prompt_parts = [
            "Control Requirement:",
            f"ID: {requirement.id}",
            f"Title: {requirement.title}",
            f"Description: {requirement.description}",
            "",
        ]

        if requirement.references:
            prompt_parts.append("References:")
            for ref_type, ref_ids in requirement.references.items():
                prompt_parts.append(f"  {ref_type}: {', '.join(ref_ids)}")
            prompt_parts.append("")

        prompt_parts.extend(
            [
                rules_context,
                "",
                f"Suggest the top {10} most relevant rules for this requirement.",
                "Return suggestions as a JSON array with confidence scores and reasoning.",
            ]
        )

        return "\n".join(prompt_parts)
