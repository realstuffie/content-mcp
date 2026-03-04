"""Rule discovery implementation.

Note: ComplianceAsCode uses custom Jinja2 delimiters in YAML files:
- {{{ variable }}} for variable expansion (instead of {{ variable }})
- {{% if condition %}} for control structures (instead of {% if condition %})
- {{# comment #}} for comments (instead of {# comment #})

These are used throughout rule.yml files and are expanded at build time.
See docs/COMPLIANCEASCODE_REFERENCE.md for more details.
"""

import logging
from datetime import datetime
from pathlib import Path

import yaml

from content_agent.core.integration import get_content_repository
from content_agent.models import (
    RuleDetails,
    RuleIdentifiers,
    RuleProductAvailability,
    RuleReferences,
    RuleRenderedContent,
    RuleSearchResult,
)

logger = logging.getLogger(__name__)


class RuleDiscovery:
    """Rule discovery and information retrieval."""

    def __init__(self) -> None:
        """Initialize rule discovery."""
        self.content_repo = get_content_repository()
        self._rule_cache: dict[str, Path] | None = None
        self._profile_rule_index: dict[str, list[tuple[str, str]]] | None = None

    def search_rules(
        self,
        query: str | None = None,
        product: str | None = None,
        severity: str | None = None,
        limit: int = 50,
    ) -> list[RuleSearchResult]:
        """Search for rules matching criteria.

        Args:
            query: Search query (matches rule_id, title, description)
            product: Filter by product
            severity: Filter by severity
            limit: Maximum results to return

        Returns:
            List of RuleSearchResult objects
        """
        logger.debug(
            f"Searching rules: query={query}, product={product}, "
            f"severity={severity}, limit={limit}"
        )

        # Build rule index if not cached
        if self._rule_cache is None:
            self._build_rule_index()

        results = []
        query_lower = query.lower() if query else None

        for rule_id, rule_path in self._rule_cache.items():
            # Quick ID match
            if query_lower and query_lower in rule_id.lower():
                result = self._load_search_result(rule_id, rule_path)
                if result and self._matches_filters(result, product, severity):
                    results.append(result)
                    if len(results) >= limit:
                        break
                continue

            # Load rule for full-text search
            if query_lower:
                result = self._load_search_result(rule_id, rule_path)
                if result and self._matches_query(result, query_lower):
                    if self._matches_filters(result, product, severity):
                        results.append(result)
                        if len(results) >= limit:
                            break
            else:
                # No query, just filter
                result = self._load_search_result(rule_id, rule_path)
                if result and self._matches_filters(result, product, severity):
                    results.append(result)
                    if len(results) >= limit:
                        break

        logger.info(f"Found {len(results)} rules matching search criteria")
        return results

    def get_rule_details(
        self,
        rule_id: str,
        include_rendered: bool = True,
        product: str | None = None,
        rendered_detail: str = "metadata",
    ) -> RuleDetails | None:
        """Get detailed information about a rule.

        Args:
            rule_id: Rule identifier
            include_rendered: Whether to include rendered content from builds (default: True)
            product: Optional product filter for rendered content. If None, includes all built products.
            rendered_detail: Level of detail for rendered content:
                - "metadata": Include only metadata (sizes, availability) - default, low token usage
                - "full": Include full rendered YAML, OVAL, and remediations - high token usage

        Returns:
            RuleDetails or None if not found
        """
        logger.debug(
            f"Getting details for rule: {rule_id} "
            f"(include_rendered={include_rendered}, product={product}, detail={rendered_detail})"
        )

        # Build index if needed
        if self._rule_cache is None:
            self._build_rule_index()

        rule_path = self._rule_cache.get(rule_id)
        if not rule_path:
            logger.warning(f"Rule not found: {rule_id}")
            return None

        try:
            # Load YAML with Jinja2 templates
            with open(rule_path) as f:
                content = f.read()
                data = yaml.load(content, Loader=yaml.FullLoader)

            rule_dir = rule_path.parent

            # Load identifiers
            identifiers = self._load_identifiers(data)

            # Load references
            references = self._load_references(data)

            # Extract products from identifiers
            products = self._extract_products_from_identifiers(data)

            # Detect available remediations
            remediations = self._detect_remediations(rule_dir)

            # Detect available checks
            checks = self._detect_checks(rule_dir)

            # Find test scenarios
            test_scenarios = self._find_test_scenarios(rule_dir)

            # Get template info if applicable
            template_info = None
            if "template" in data:
                template_info = data["template"]

            # Get file modification time
            last_modified = datetime.fromtimestamp(rule_path.stat().st_mtime)

            # Handle platforms - can be a string or list
            platforms = data.get("platform", data.get("platforms", []))
            if isinstance(platforms, str):
                platforms = [platforms]

            # Create base details
            details = RuleDetails(
                rule_id=rule_id,
                title=data.get("title", rule_id),
                description=data.get("description", ""),
                rationale=data.get("rationale"),
                severity=data.get("severity", "unknown"),
                identifiers=identifiers,
                references=references,
                products=products,
                platforms=platforms,
                remediations=remediations,
                checks=checks,
                test_scenarios=test_scenarios,
                file_path=str(rule_path.relative_to(self.content_repo.path)),
                rule_dir=str(rule_dir.relative_to(self.content_repo.path)),
                last_modified=last_modified,
                template=template_info,
            )

            # Include rendered content if requested
            if include_rendered:
                rendered_content = self._get_rendered_content(rule_id, product, rendered_detail)
                if rendered_content:
                    details.rendered = rendered_content

            logger.debug(f"Loaded details for rule {rule_id}")
            return details

        except Exception as e:
            logger.error(f"Failed to load rule {rule_id}: {e}")
            return None

    def _build_profile_rule_index(self) -> None:
        """Build reverse index mapping rule IDs to (product, profile_id) tuples."""
        from content_agent.core.discovery.profiles import ProfileDiscovery

        logger.info("Building profile-to-rule reverse index")
        self._profile_rule_index = {}

        profile_discovery = ProfileDiscovery()
        profiles = profile_discovery.list_profiles()

        for profile_summary in profiles:
            product = profile_summary.product
            profile_id = profile_summary.profile_id

            profile = profile_discovery.get_profile_details(profile_id, product)
            if not profile:
                continue

            for selection in profile.selections:
                # Only match direct rule IDs, not control references like "anssi:all:minimal"
                if ":" in selection:
                    continue
                # Skip unselection directives
                if selection.startswith("!"):
                    continue

                if selection not in self._profile_rule_index:
                    self._profile_rule_index[selection] = []
                self._profile_rule_index[selection].append((product, profile_id))

        logger.info(
            f"Profile rule index built: {len(self._profile_rule_index)} rules across profiles"
        )

    def get_rule_product_availability(self, rule_id: str) -> RuleProductAvailability | None:
        """Determine which products include a rule and in which profiles.

        Args:
            rule_id: Rule identifier

        Returns:
            RuleProductAvailability or None if rule not found
        """
        logger.debug(f"Getting product availability for rule: {rule_id}")

        # Get rule details (without rendered content for speed)
        rule = self.get_rule_details(rule_id, include_rendered=False)
        if not rule:
            return None

        # Build profile index if not cached
        if self._profile_rule_index is None:
            self._build_profile_rule_index()

        assert self._profile_rule_index is not None  # for mypy

        # Get products from profiles
        products_in_profiles: dict[str, list[str]] = {}
        profile_entries = self._profile_rule_index.get(rule_id, [])
        for product, profile_id in profile_entries:
            if product not in products_in_profiles:
                products_in_profiles[product] = []
            if profile_id not in products_in_profiles[product]:
                products_in_profiles[product].append(profile_id)

        # Check build artifacts
        has_build_artifacts: dict[str, bool] = {}
        try:
            from content_agent.core.discovery import build_artifacts

            built_products = build_artifacts.list_built_products()
            for product in built_products:
                rendered = build_artifacts.get_rendered_rule(product, rule_id)
                has_build_artifacts[product] = rendered is not None
        except Exception as e:
            logger.debug(f"Failed to check build artifacts for {rule_id}: {e}")

        return RuleProductAvailability(
            rule_id=rule_id,
            products_with_identifiers=rule.products,
            products_in_profiles=products_in_profiles,
            platforms=rule.platforms,
            template=rule.template,
            has_build_artifacts=has_build_artifacts,
        )

    def _build_rule_index(self) -> None:
        """Build index of all rules in the repository."""
        logger.info("Building rule index")
        self._rule_cache = {}

        # Search common rule locations
        search_paths = [
            self.content_repo.path / "linux_os",
            self.content_repo.path / "applications",
            self.content_repo.path / "shared",
        ]

        for search_path in search_paths:
            if not search_path.exists():
                continue

            for rule_yml in search_path.rglob("rule.yml"):
                rule_dir = rule_yml.parent
                rule_id = rule_dir.name
                self._rule_cache[rule_id] = rule_yml

        logger.info(f"Indexed {len(self._rule_cache)} rules")

    def _load_search_result(self, rule_id: str, rule_path: Path) -> RuleSearchResult | None:
        """Load rule as search result.

        Args:
            rule_id: Rule identifier
            rule_path: Path to rule.yml

        Returns:
            RuleSearchResult or None
        """
        try:
            # Load YAML with Jinja2 templates - use FullLoader to be more lenient
            # This will leave Jinja2 templates as strings in the YAML
            with open(rule_path) as f:
                content = f.read()
                # Try to load YAML - if it has Jinja2 templates, they'll be treated as strings
                data = yaml.load(content, Loader=yaml.FullLoader)

            # Extract products from identifiers (e.g., cce@rhel8, stigid@rhel9)
            products = self._extract_products_from_identifiers(data)

            return RuleSearchResult(
                rule_id=rule_id,
                title=data.get("title", rule_id),
                severity=data.get("severity", "unknown"),
                description=data.get("description", "")[:200],  # Truncate for search
                products=products,
                file_path=str(rule_path.relative_to(self.content_repo.path)),
            )
        except Exception as e:
            logger.debug(f"Failed to load search result for {rule_id}: {e}")
            return None

    def _extract_products_from_identifiers(self, data: dict) -> list[str]:
        """Extract product list from identifiers and references.

        Args:
            data: Rule YAML data

        Returns:
            List of product IDs
        """
        products = set()

        # Extract from identifiers (e.g., cce@rhel8)
        identifiers = data.get("identifiers", {})
        for key in identifiers.keys():
            if "@" in key:
                product = key.split("@")[1]
                products.add(product)

        # Extract from references (e.g., stigid@rhel9)
        references = data.get("references", {})
        for key in references.keys():
            if "@" in key:
                product = key.split("@")[1]
                products.add(product)

        return sorted(products)

    def _matches_query(self, result: RuleSearchResult, query: str) -> bool:
        """Check if result matches search query.

        Args:
            result: Search result
            query: Query string (lowercase)

        Returns:
            True if matches
        """
        # Search in title and description
        searchable = f"{result.title} {result.description}".lower()
        return query in searchable

    def _matches_filters(
        self, result: RuleSearchResult, product: str | None, severity: str | None
    ) -> bool:
        """Check if result matches filters.

        Args:
            result: Search result
            product: Product filter
            severity: Severity filter

        Returns:
            True if matches all filters
        """
        if product and product not in result.products:
            return False

        if severity and result.severity != severity:
            return False

        return True

    def _load_identifiers(self, data: dict) -> RuleIdentifiers:
        """Load rule identifiers from YAML data.

        Args:
            data: Rule YAML data

        Returns:
            RuleIdentifiers
        """
        identifiers_data = data.get("identifiers", {})

        # Extract common identifiers
        cce = identifiers_data.get("cce")
        if isinstance(cce, list):
            cce = cce[0] if cce else None

        return RuleIdentifiers(
            cce=cce,
            cis=identifiers_data.get("cis"),
            nist=identifiers_data.get("nist"),
            stigid=identifiers_data.get("stigid"),
            **{
                k: v
                for k, v in identifiers_data.items()
                if k not in ["cce", "cis", "nist", "stigid"]
            },
        )

    def _load_references(self, data: dict) -> RuleReferences:
        """Load rule references from YAML data.

        Args:
            data: Rule YAML data

        Returns:
            RuleReferences
        """
        references_data = data.get("references", {})

        def ensure_list(val):
            if isinstance(val, list):
                return val
            elif isinstance(val, str):
                return [val]
            else:
                return []

        return RuleReferences(
            nist=ensure_list(references_data.get("nist")),
            cis=ensure_list(references_data.get("cis")),
            cui=ensure_list(references_data.get("cui")),
            disa=ensure_list(references_data.get("disa")),
            isa62443=ensure_list(references_data.get("isa-62443")),
            pcidss=ensure_list(references_data.get("pcidss")),
            hipaa=ensure_list(references_data.get("hipaa")),
            **{
                k: ensure_list(v)
                for k, v in references_data.items()
                if k not in ["nist", "cis", "cui", "disa", "isa-62443", "pcidss", "hipaa"]
            },
        )

    def _detect_remediations(self, rule_dir: Path) -> dict[str, bool]:
        """Detect available remediations for a rule.

        Args:
            rule_dir: Rule directory path

        Returns:
            Dict mapping remediation type to availability
        """
        remediation_types = ["bash", "ansible", "anaconda", "puppet", "ignition"]
        remediations = {}

        for rem_type in remediation_types:
            rem_dir = rule_dir / rem_type
            # Check for directory with files, or .sh/.yml files
            has_remediation = False
            if rem_dir.exists() and rem_dir.is_dir():
                has_remediation = len(list(rem_dir.iterdir())) > 0
            elif (rule_dir / f"{rem_type}.sh").exists():
                has_remediation = True
            elif (rule_dir / f"{rem_type}.yml").exists():
                has_remediation = True

            remediations[rem_type] = has_remediation

        return remediations

    def _detect_checks(self, rule_dir: Path) -> dict[str, bool]:
        """Detect available checks for a rule.

        Args:
            rule_dir: Rule directory path

        Returns:
            Dict mapping check type to availability
        """
        checks = {}

        # OVAL checks
        oval_dir = rule_dir / "oval"
        checks["oval"] = oval_dir.exists() and oval_dir.is_dir()

        # Other check types can be added here

        return checks

    def _find_test_scenarios(self, rule_dir: Path) -> list[str]:
        """Find test scenarios for a rule.

        Args:
            rule_dir: Rule directory path

        Returns:
            List of test scenario names
        """
        tests_dir = rule_dir / "tests"
        if not tests_dir.exists():
            return []

        scenarios = []
        for test_file in tests_dir.glob("*.sh"):
            scenarios.append(test_file.name)

        return sorted(scenarios)

    def _get_rendered_content(
        self,
        rule_id: str,
        product_filter: str | None = None,
        detail_level: str = "metadata",
    ) -> dict[str, RuleRenderedContent] | None:
        """Get rendered content for a rule from build artifacts.

        Args:
            rule_id: Rule identifier
            product_filter: Optional product to filter by
            detail_level: "metadata" for sizes/availability only, "full" for complete content

        Returns:
            Dict of RuleRenderedContent by product, or None if no builds found
        """
        try:
            # Import here to avoid circular dependencies
            from content_agent.core.discovery import build_artifacts

            # Get list of built products
            built_products = build_artifacts.list_built_products()
            if not built_products:
                return None

            # Filter by product if specified
            if product_filter:
                built_products = [p for p in built_products if p == product_filter]
                if not built_products:
                    return None

            # Try to get rendered content for each product
            rendered_dict = {}
            for prod in built_products:
                rendered = build_artifacts.get_rendered_rule(prod, rule_id)
                if rendered:
                    # Get datastream info for build time
                    datastream_info = build_artifacts.get_datastream_info(prod)
                    build_time = datastream_info.build_time if datastream_info else None

                    # Calculate sizes and availability
                    yaml_size = len(rendered.rendered_yaml) if rendered.rendered_yaml else 0
                    oval_size = len(rendered.rendered_oval) if rendered.rendered_oval else 0
                    remediation_sizes = {
                        k: len(v) for k, v in rendered.rendered_remediations.items()
                    }
                    available_rems = list(rendered.rendered_remediations.keys())

                    # For metadata mode, don't include the full content (save tokens!)
                    if detail_level == "metadata":
                        rendered_dict[prod] = RuleRenderedContent(
                            product=prod,
                            rendered_yaml=None,  # Exclude full content
                            rendered_oval=None,  # Exclude full content
                            rendered_remediations={},  # Exclude full content
                            build_path=rendered.build_path,
                            build_time=build_time,
                            # Include metadata
                            yaml_size=yaml_size,
                            oval_size=oval_size,
                            remediation_sizes=remediation_sizes,
                            has_yaml=rendered.rendered_yaml is not None,
                            has_oval=rendered.rendered_oval is not None,
                            available_remediations=available_rems,
                        )
                    else:  # "full" mode
                        rendered_dict[prod] = RuleRenderedContent(
                            product=prod,
                            rendered_yaml=rendered.rendered_yaml,
                            rendered_oval=rendered.rendered_oval,
                            rendered_remediations=rendered.rendered_remediations,
                            build_path=rendered.build_path,
                            build_time=build_time,
                            # Also include metadata
                            yaml_size=yaml_size,
                            oval_size=oval_size,
                            remediation_sizes=remediation_sizes,
                            has_yaml=rendered.rendered_yaml is not None,
                            has_oval=rendered.rendered_oval is not None,
                            available_remediations=available_rems,
                        )

            return rendered_dict if rendered_dict else None

        except Exception as e:
            logger.debug(f"Failed to get rendered content for {rule_id}: {e}")
            return None


def search_rules(
    query: str | None = None,
    product: str | None = None,
    severity: str | None = None,
    limit: int = 50,
) -> list[RuleSearchResult]:
    """Search for rules matching criteria.

    Args:
        query: Search query
        product: Filter by product
        severity: Filter by severity
        limit: Maximum results

    Returns:
        List of RuleSearchResult objects
    """
    discovery = RuleDiscovery()
    return discovery.search_rules(query, product, severity, limit)


def get_rule_details(
    rule_id: str,
    include_rendered: bool = True,
    product: str | None = None,
    rendered_detail: str = "metadata",
) -> RuleDetails | None:
    """Get detailed information about a rule.

    Args:
        rule_id: Rule identifier
        include_rendered: Whether to include rendered content from builds (default: True)
        product: Optional product filter for rendered content
        rendered_detail: Detail level - "metadata" (default, low tokens) or "full" (high tokens)

    Returns:
        RuleDetails or None if not found
    """
    discovery = RuleDiscovery()
    return discovery.get_rule_details(rule_id, include_rendered, product, rendered_detail)


def get_rule_product_availability(rule_id: str) -> RuleProductAvailability | None:
    """Determine which products include a rule and in which profiles.

    Args:
        rule_id: Rule identifier

    Returns:
        RuleProductAvailability or None if rule not found
    """
    discovery = RuleDiscovery()
    return discovery.get_rule_product_availability(rule_id)
