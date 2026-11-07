"""Resolve the rules a profile selects, including selections made through controls.

This follows the ComplianceAsCode build (``ssg.entities.profile`` and
``ssg.controls``) closely enough to answer "which profiles select this rule":

- ``policy:all`` selects every requirement of a control file.
- ``policy:all:<level>`` selects requirements of that level and the levels it
  inherits from. A requirement without ``levels`` belongs to the control file's
  first level, or to ``default`` when the file defines none.
- ``policy:<requirement>`` selects one requirement.
- A selected requirement contributes its own rules, the rules of its nested
  requirements, and the rules of the requirements it references.
- ``extends`` adds the parent profile's rules, and ``!rule`` entries remove rules.
- Variable assignments and refinements (entries containing ``=``) select nothing.
- Only rules the product's build loads count, when the product's rules are
  known: the build drops the others from control selections.
- A profile's ``filter_rules`` expression, when a rule filter is given, keeps only
  the rules it accepts. As in the build, it applies after ``extends`` and
  unselections, to the parent's rules too, and the parent's own filter has
  already applied to them.
"""

import logging
from collections.abc import Callable
from typing import Any

from content_agent.models.control import ControlFile, ControlRequirement, flatten_requirements

logger = logging.getLogger(__name__)

DEFAULT_LEVEL = "default"


def _is_rule_entry(entry: str) -> bool:
    return "=" not in entry and not entry.startswith("!")


class ProfileRuleResolver:
    """Resolve profile selections into rule IDs, caching control files per product."""

    def __init__(
        self,
        profile_discovery: Any,
        control_discovery: Any | None = None,
        rule_filter: Callable[[str, str, str], bool] | None = None,
        product_rules: Callable[[str], set[str] | None] | None = None,
    ) -> None:
        """
        Args:
            profile_discovery: Source of profile details
            control_discovery: Source of control files, created when needed if None
            rule_filter: Called with (product, rule_id, filter_rules expression);
                returns whether the profile keeps the rule. Without it,
                filter_rules is not applied.
            product_rules: Called with a product; returns the IDs of the rules
                the build loads for it, or None when unknown.
        """
        self._profiles = profile_discovery
        self._controls = control_discovery
        self._rule_filter = rule_filter
        self._product_rules = product_rules
        self._policy_cache: dict[tuple[str, str], ControlFile | None] = {}
        self._control_rules_cache: dict[tuple[str, str, str], set[str]] = {}
        self._profile_cache: dict[tuple[str, str], set[str]] = {}

    def resolve_profile(self, product: str, profile_id: str) -> set[str]:
        """Return the rule IDs a profile selects after controls, extends and unselections."""
        return self._resolve_profile(product, profile_id, frozenset())

    def _resolve_profile(
        self, product: str, profile_id: str, visiting: frozenset[tuple[str, str]]
    ) -> set[str]:
        key = (product, profile_id)
        if key in self._profile_cache:
            return self._profile_cache[key]
        if key in visiting:
            logger.warning(f"Profile {product}/{profile_id} extends itself; ignoring the loop")
            return set()

        details = self._profiles.get_profile_details(profile_id, product)
        if details is None:
            return set()

        selected: set[str] = set()
        unselected: set[str] = set()
        for item in details.selections:
            if "=" in item:
                continue
            if item.startswith("!"):
                unselected.add(item[1:])
            elif ":" in item:
                policy_id, spec = item.split(":", 1)
                for req in self._select(product, policy_id, spec):
                    selected |= self._control_rules(product, policy_id, req, frozenset())
            else:
                selected.add(item)

        if details.extends:
            selected |= self._resolve_profile(product, details.extends, visiting | {key})

        result = selected - unselected
        known = self._product_rules(product) if self._product_rules is not None else None
        if known is not None:
            result &= known
        expression = getattr(details, "filter_rules", None)
        if expression and self._rule_filter is not None:
            rule_filter = self._rule_filter
            result = {rule for rule in result if rule_filter(product, rule, expression)}
        self._profile_cache[key] = result
        return result

    def _policy(self, product: str, policy_id: str) -> ControlFile | None:
        key = (product, policy_id)
        if key not in self._policy_cache:
            try:
                if self._controls is None:
                    from content_agent.core.discovery.controls import ControlDiscovery

                    self._controls = ControlDiscovery()
                self._policy_cache[key] = self._controls.get_control_details(
                    policy_id, product=product
                )
            except Exception as e:
                logger.debug(f"Could not load control file {policy_id} for {product}: {e}")
                self._policy_cache[key] = None
        return self._policy_cache[key]

    @staticmethod
    def _levels_with_ancestors(policy: ControlFile, level_id: str) -> set[str]:
        levels_by_id = {level.id: level for level in policy.levels or []}
        found: set[str] = set()
        pending = [level_id]
        while pending:
            current = pending.pop()
            if current in found:
                continue
            found.add(current)
            level = levels_by_id.get(current)
            if level is not None:
                pending.extend(level.inherits_from or [])
        return found

    def _select(self, product: str, policy_id: str, spec: str) -> list[ControlRequirement]:
        policy = self._policy(product, policy_id)
        if policy is None:
            logger.debug(f"Control file {policy_id} not found for {product}")
            return []

        requirements = flatten_requirements(policy.controls)
        if spec == "all":
            return requirements
        if spec.startswith("all:"):
            levels = self._levels_with_ancestors(policy, spec.split(":", 1)[1])
            default_levels = [policy.levels[0].id] if policy.levels else [DEFAULT_LEVEL]
            return [req for req in requirements if levels & set(req.levels or default_levels)]
        return [req for req in requirements if req.id == spec]

    def _control_rules(
        self,
        product: str,
        policy_id: str,
        req: ControlRequirement,
        visiting: frozenset[tuple[str, str, str]],
    ) -> set[str]:
        key = (product, policy_id, req.id)
        if key in self._control_rules_cache:
            return self._control_rules_cache[key]
        if key in visiting:
            return set()
        visiting = visiting | {key}

        rules = {rule for rule in req.rules if _is_rule_entry(rule)}
        for child in req.controls:
            rules |= self._control_rules(product, policy_id, child, visiting)
        for ref in req.referenced_controls:
            ref_policy, ref_spec = ref.split(":", 1) if ":" in ref else (policy_id, ref)
            for target in self._select(product, ref_policy, ref_spec):
                rules |= self._control_rules(product, ref_policy, target, visiting)

        self._control_rules_cache[key] = rules
        return rules
