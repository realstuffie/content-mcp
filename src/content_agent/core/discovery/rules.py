"""Rule discovery implementation.

Note: ComplianceAsCode uses custom Jinja2 delimiters in YAML files:
- {{{ variable }}} for variable expansion (instead of {{ variable }})
- {{% if condition %}} for control structures (instead of {% if condition %})
- {{# comment #}} for comments (instead of {# comment #})

These are used throughout rule.yml files and are expanded at build time.
See docs/COMPLIANCEASCODE_REFERENCE.md for more details.
"""

import logging
from collections.abc import Callable, Iterator
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from content_agent.core.discovery.content_state import ContentState, take_content_state
from content_agent.core.discovery.rule_paths import (
    configured_rule_roots,
    product_rule_ids,
    rule_files,
)
from content_agent.core.integration import get_content_repository
from content_agent.core.integration.product_variables import load_product_variables
from content_agent.core.integration.ssg_modules import get_ssg_modules
from content_agent.models import (
    DiscoveryResult,
    RuleDetails,
    RuleIdentifiers,
    RuleProductAvailability,
    RuleReferences,
    RuleRenderedContent,
    RuleSearchResult,
)

logger = logging.getLogger(__name__)

# Jinja2 variables for expanding a rule without a product: product conditionals
# are false. If that fails, a second try keeps {{{ full_name }}} as literal text,
# because an empty full_name at the start of a line breaks YAML indentation.
GENERIC_SUBSTITUTIONS: dict[str, Any] = {"product": ""}
FULL_NAME_PLACEHOLDER: dict[str, Any] = {"product": "", "full_name": "{{{ full_name }}}"}

ProfileRuleIndex = dict[str, list[tuple[str, str]]]
HiddenProfileRules = dict[str, set[str]]

# Every MCP tool call creates a new RuleDiscovery, and building the profile index
# reads every profile and control file, so the index is shared between instances.
# It is rebuilt when any file it is built from changes.
_shared_profile_indexes: dict[str, tuple[ContentState, ProfileRuleIndex, HiddenProfileRules]] = {}

# The files the profile index is built from, besides the rule.yml files: products
# and their variables, profiles, and control files
PROFILE_INDEX_PATTERNS = (
    "products/*/product.yml",
    "product_properties/*.yml",
    "products/*/profiles/*.profile",
    "controls/**/*.yml",
    "products/*/controls/**/*.yml",
)


def _profile_index_state(repo_path: Path) -> ContentState | None:
    """Return the state of the files the profile index is built from.

    Besides profiles and control files, the index depends on each rule.yml
    (documentation_complete, and the attributes filter_rules tests), and on
    product.yml and product_properties, which set the rule directories and the
    Jinja2 variables rules are expanded with.
    """
    try:
        return take_content_state(
            repo_path, PROFILE_INDEX_PATTERNS, configured_rule_roots(repo_path)
        )
    except Exception as e:
        logger.debug(f"Could not record the profile index inputs: {e}")
        return None


class RuleDiscovery:
    """Rule discovery and information retrieval."""

    def __init__(self) -> None:
        """Initialize rule discovery."""
        self.content_repo = get_content_repository()
        self._rule_cache: dict[str, Path] | None = None
        self._profile_rule_index: dict[str, list[tuple[str, str]]] | None = None
        self._hidden_profile_rules: HiddenProfileRules = {}
        self._product_env_cache: dict[str, dict[str, Any] | None] = {}

    def _product_substitutions(self, product: str) -> dict[str, Any] | None:
        """Return the Jinja2 variables the build uses for a product.

        Like ssg.environment.open_environment(), this is the product's product.yml
        plus the product_properties directory, which together define variables
        such as full_name, auid and audisp_conf_path. Returns None when the product
        can't be loaded.
        """
        if product not in self._product_env_cache:
            try:
                ssg_products = get_ssg_modules().products
            except Exception as e:
                logger.debug(f"SSG modules unavailable for product {product}: {e}")
                self._product_env_cache[product] = None
            else:
                self._product_env_cache[product] = load_product_variables(
                    ssg_products, self.content_repo.path, product
                )
        cached = self._product_env_cache[product]
        return dict(cached) if cached is not None else None

    def _all_product_ids(self) -> list[str]:
        products_dir = self.content_repo.path / "products"
        if not products_dir.is_dir():
            return []
        return sorted(p.name for p in products_dir.iterdir() if (p / "product.yml").is_file())

    def _load_rule_yaml(self, rule_path: Path, product: str | None = None) -> dict:
        """Load and parse a rule.yml file, expanding Jinja2 templates.

        Uses ssg.yaml.open_and_expand() to handle Jinja2 control structures
        that would otherwise break standard YAML parsing.

        Args:
            rule_path: Path to rule.yml
            product: Optional product ID for product-specific expansion.
                When provided, the rule is expanded with that product's variables,
                as in the build. When None, the rule is expanded with an empty
                product name, so product conditionals are false.

        When expansion fails, the file is loaded as plain YAML. Without a product,
        two more expansions are tried before giving up: one that keeps
        ``{{{ full_name }}}`` as literal text, and then the variables of the first
        product that works.
        """
        if product:
            substitutions = self._product_substitutions(product) or {"product": product}
        else:
            substitutions = dict(GENERIC_SUBSTITUTIONS)
        try:
            ssg_yaml = get_ssg_modules().yaml
            return ssg_yaml.open_and_expand(str(rule_path), substitutions)  # type: ignore[no-any-return]
        except Exception as e:
            expansion_error = e

        # Fallback to direct YAML loading if ssg expansion fails
        logger.warning(
            f"SSG Jinja2 expansion failed for {rule_path}, "
            f"falling back to direct YAML loading: {expansion_error}"
        )
        try:
            with open(rule_path) as f:
                return yaml.load(f.read(), Loader=yaml.FullLoader)  # type: ignore[no-any-return]
        except yaml.YAMLError:
            if product:
                raise

        # Without a product, the remaining failures are rules whose Jinja needs
        # product variables, such as full_name at the start of a line, or auid
        def attempts() -> Iterator[dict[str, Any]]:
            yield dict(FULL_NAME_PLACEHOLDER)
            for fallback in self._all_product_ids():
                fallback_substitutions = self._product_substitutions(fallback)
                if fallback_substitutions is not None:
                    yield fallback_substitutions

        for attempt in attempts():
            try:
                data = get_ssg_modules().yaml.open_and_expand(str(rule_path), attempt)
            except Exception:
                continue
            logger.debug(f"Expanded {rule_path} with product {attempt.get('product')!r}")
            return data  # type: ignore[no-any-return]

        with open(rule_path) as f:
            return yaml.load(f.read(), Loader=yaml.FullLoader)  # type: ignore[no-any-return]

    def search_rules(
        self,
        query: str | None = None,
        product: str | None = None,
        severity: str | None = None,
        limit: int = 50,
    ) -> DiscoveryResult[RuleSearchResult]:
        """Search for rules matching criteria.

        Args:
            query: Search query (matches rule_id, title, description)
            product: Filter by product
            severity: Filter by severity
            limit: Maximum results to return

        Returns:
            DiscoveryResult with RuleSearchResult items and any parse errors
        """
        logger.debug(
            f"Searching rules: query={query}, product={product}, "
            f"severity={severity}, limit={limit}"
        )

        # Build rule index if not cached
        if self._rule_cache is None:
            self._build_rule_index()

        discovery_result: DiscoveryResult[RuleSearchResult] = DiscoveryResult()
        query_lower = query.lower() if query else None
        product_rules = self._rules_selected_by_product(product) if product else set()

        assert self._rule_cache is not None
        for rule_id, rule_path in self._rule_cache.items():
            try:
                # Quick ID match
                if query_lower and query_lower in rule_id.lower():
                    result = self._load_search_result(rule_id, rule_path, product=product)
                    if self._matches_filters(result, product, severity, product_rules):
                        discovery_result.items.append(result)
                        if len(discovery_result.items) >= limit:
                            break
                    continue

                # Load rule for full-text search
                if query_lower:
                    result = self._load_search_result(rule_id, rule_path, product=product)
                    if self._matches_query(result, query_lower):
                        if self._matches_filters(result, product, severity, product_rules):
                            discovery_result.items.append(result)
                            if len(discovery_result.items) >= limit:
                                break
                else:
                    # No query, just filter
                    result = self._load_search_result(rule_id, rule_path, product=product)
                    if self._matches_filters(result, product, severity, product_rules):
                        discovery_result.items.append(result)
                        if len(discovery_result.items) >= limit:
                            break
            except Exception as e:
                error_msg = f"Failed to load rule {rule_id}: {e}"
                logger.warning(error_msg)
                discovery_result.errors.append(error_msg)

        logger.info(f"Found {len(discovery_result.items)} rules matching search criteria")
        return discovery_result

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

        assert self._rule_cache is not None
        rule_path = self._rule_cache.get(rule_id)
        if not rule_path:
            logger.warning(f"Rule not found: {rule_id}")
            return None

        # Load YAML with Jinja2 template expansion
        data = self._load_rule_yaml(rule_path, product=product)

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

        # Handle platforms - can be a string or list. A platforms block whose Jinja2
        # expands to nothing, such as rule_notapplicable_when_ovirt_installed() on most
        # products, loads as None.
        platforms = data.get("platform") or data.get("platforms") or []
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

    def _build_profile_rule_index(self) -> None:
        """Build reverse index mapping rule IDs to (product, profile_id) tuples.

        Profile selections are resolved like the build does: control references such
        as ``cis_rhel9:all:l2_server`` expand to the rules of the selected requirements,
        ``extends`` adds the parent profile's rules, and ``!rule`` entries remove rules.
        """
        from content_agent.core.discovery.profile_resolution import ProfileRuleResolver
        from content_agent.core.discovery.profiles import ProfileDiscovery

        logger.info("Building profile-to-rule reverse index")
        self._profile_rule_index = {}
        self._hidden_profile_rules = {}

        profile_discovery = ProfileDiscovery()
        product_rules: dict[str, set[str] | None] = {}
        directory_rules: dict[Path, set[str]] = {}

        def known_rules(product: str) -> set[str] | None:
            if product not in product_rules:
                product_rules[product] = product_rule_ids(
                    self.content_repo.path, product, directory_rules
                )
            return product_rules[product]

        resolver = ProfileRuleResolver(
            profile_discovery,
            rule_filter=self._profile_rule_filter(),
            product_rules=known_rules,
        )
        profiles_result = profile_discovery.list_profiles(include_hidden=True)

        for profile_summary in profiles_result.items:
            product = profile_summary.product
            profile_id = profile_summary.profile_id

            selected = resolver.resolve_profile(product, profile_id)
            if profile_summary.hidden:
                self._hidden_profile_rules.setdefault(product, set()).update(selected)
                continue
            for rule_id in sorted(selected):
                self._profile_rule_index.setdefault(rule_id, []).append((product, profile_id))

        logger.info(
            f"Profile rule index built: {len(self._profile_rule_index)} rules across profiles"
        )

    def _profile_rule_filter(self) -> Callable[[str, str, str], bool] | None:
        """Return a filter that applies profiles' filter_rules the way the build does.

        The build evaluates the expression with ssg.utils.safe_eval_filter against
        the rule's attributes: `platform` is the rule's platform text, or empty,
        and `platforms` is a set that includes it. Rules are expanded with the
        product's variables, since platforms like `{{{ product }}}-node` use Jinja2.
        A rule that can't be loaded or evaluated is kept.
        """
        try:
            get_ssg_modules()
            import ssg.utils

            evaluate = ssg.utils.safe_eval_filter
        except Exception as e:
            logger.info(f"Profile filter_rules not applied, ssg.utils unavailable: {e}")
            return None

        contexts: dict[tuple[str, str], dict[str, Any] | None] = {}

        def context(product: str, rule_id: str) -> dict[str, Any] | None:
            key = (product, rule_id)
            if key not in contexts:
                contexts[key] = self._filter_context(product, rule_id)
            return contexts[key]

        def keep(product: str, rule_id: str, expression: str) -> bool:
            attributes = context(product, rule_id)
            if attributes is None:
                return True
            try:
                return bool(evaluate(expression, attributes))
            except Exception as e:
                logger.debug(f"filter_rules {expression!r} failed for {rule_id}: {e}")
                return True

        return keep

    def _filter_context(self, product: str, rule_id: str) -> dict[str, Any] | None:
        if self._rule_cache is None:
            self._build_rule_index()
        assert self._rule_cache is not None
        rule_path = self._rule_cache.get(rule_id)
        if rule_path is None:
            return None
        try:
            data = self._load_rule_yaml(rule_path, product)
        except Exception as e:
            logger.debug(f"Could not load {rule_id} for {product}: {e}")
            return None
        if not isinstance(data, dict):
            return None
        platform = data.get("platform") or ""
        platforms = set(data.get("platforms") or [])
        if platform:
            platforms.add(platform)
        return {**data, "id_": rule_id, "platform": platform, "platforms": platforms}

    def _ensure_profile_rule_index(self) -> ProfileRuleIndex:
        """Return the profile index, reusing the shared one when its inputs are unchanged."""
        if self._profile_rule_index is None:
            repo_key = str(self.content_repo.path)
            shared = _shared_profile_indexes.get(repo_key)
            if shared is not None and shared[0].is_current():
                self._profile_rule_index = shared[1]
                self._hidden_profile_rules = shared[2]
            else:
                # Taken before the build, so a file that changes during it is
                # noticed on the next call
                state = _profile_index_state(self.content_repo.path)
                self._build_profile_rule_index()
                assert self._profile_rule_index is not None  # for mypy
                if state is None:
                    _shared_profile_indexes.pop(repo_key, None)
                else:
                    _shared_profile_indexes[repo_key] = (
                        state,
                        self._profile_rule_index,
                        self._hidden_profile_rules,
                    )
        return self._profile_rule_index

    def _rules_selected_by_product(self, product: str) -> set[str]:
        """Return rules from selectable and build-only profiles of the product."""
        index = self._ensure_profile_rule_index()
        return {
            rule_id
            for rule_id, entries in index.items()
            if any(entry_product == product for entry_product, _ in entries)
        } | self._hidden_profile_rules.get(product, set())

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

        # Get products from profiles
        products_in_profiles: dict[str, list[str]] = {}
        profile_entries = self._ensure_profile_rule_index().get(rule_id, [])
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

        # The directories the build reads rules from, as product.yml files name them
        for rule_yml in rule_files(self.content_repo.path):
            self._rule_cache[rule_yml.parent.name] = rule_yml

        logger.info(f"Indexed {len(self._rule_cache)} rules")

    def _load_search_result(
        self, rule_id: str, rule_path: Path, product: str | None = None
    ) -> RuleSearchResult:
        """Load rule as search result.

        Args:
            rule_id: Rule identifier
            rule_path: Path to rule.yml
            product: Optional product ID for Jinja2 template expansion

        Returns:
            RuleSearchResult

        Raises:
            Exception: If YAML parsing or model construction fails
        """
        data = self._load_rule_yaml(rule_path, product=product)

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
        self,
        result: RuleSearchResult,
        product: str | None,
        severity: str | None,
        product_rules: set[str] | None = None,
    ) -> bool:
        """Check if result matches filters.

        Args:
            result: Search result
            product: Product filter. A rule matches when the product's profiles
                select it or it has identifiers for the product.
            severity: Severity filter
            product_rules: Rules the product's profiles select

        Returns:
            True if matches all filters
        """
        if (
            product
            and product not in result.products
            and result.rule_id not in (product_rules or set())
        ):
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

        def ensure_list(val: Any) -> list[str]:
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
) -> DiscoveryResult[RuleSearchResult]:
    """Search for rules matching criteria.

    Args:
        query: Search query
        product: Filter by product
        severity: Filter by severity
        limit: Maximum results

    Returns:
        DiscoveryResult with RuleSearchResult items and any parse errors
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
