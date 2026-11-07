"""Control framework discovery implementation."""

import logging
import re
from pathlib import Path
from typing import Any, Literal

import yaml

from content_agent.core.integration import get_content_repository
from content_agent.core.integration.product_variables import load_product_variables
from content_agent.core.integration.ssg_modules import get_ssg_modules
from content_agent.models.control import (
    ControlFile,
    ControlRequirement,
    ControlRuleIndex,
    ControlStats,
    IndexedRequirement,
    RequirementFilePath,
    SimilarRequirement,
    flatten_requirements,
)

logger = logging.getLogger(__name__)

# Jinja2 variables for expanding requirement files without a product
GENERIC_SUBSTITUTIONS: dict[str, Any] = {
    "product": "",
    "families": [],
    "full_name": "The operating system",
}


def requirements_directory(control_file: Path, data: Any) -> Path | None:
    """Return the directory holding a policy's requirement files, if it has one.

    Like ComplianceAsCode, this is the `controls_dir` the control file names, and
    otherwise the directory named after the control file, such as controls/cis_ocp/
    next to controls/cis_ocp.yml.
    """
    subdir = data.get("controls_dir") if isinstance(data, dict) else None
    directory = control_file.parent / str(subdir) if subdir else control_file.with_suffix("")
    return directory if directory.is_dir() else None


def requirement_files(directory: Path) -> list[Path]:
    """Return the requirement files ComplianceAsCode reads from a policy's directory."""
    return sorted(path for path in directory.glob("*.yml") if not path.name.startswith("."))


def find_requirement_file(
    control_file: Path, data: Any, requirement_id: str
) -> tuple[Path, Literal["inline", "directory"]] | None:
    """Find the file that defines a requirement, and whether it's the control file.

    A policy's requirements can be in its control file and in any file of its
    requirement directory: NIST 800-53 keeps a family per file, so ac-2 is in
    ac.yml. The file named after the requirement is tried first, then the control
    file, then the other files. Files are searched as text, so Jinja2 doesn't get
    in the way and IDs like 1.10 aren't read as numbers.
    """
    # `- id: X`, or an indented `id: X` in a list item whose first key is another;
    # a policy's own top-level `id:` is never indented
    id_line = re.compile(
        rf"^(?:\s*-\s+|\s+)id:\s*['\"]?{re.escape(requirement_id)}['\"]?\s*(?:#.*)?$",
        re.MULTILINE,
    )
    directory = requirements_directory(control_file, data)
    named = directory / f"{requirement_id}.yml" if directory else None
    if named is not None and named.is_file():
        return named, "directory"

    candidates: list[tuple[Path, Literal["inline", "directory"]]] = [(control_file, "inline")]
    if directory is not None:
        candidates.extend((path, "directory") for path in requirement_files(directory))
    for path, file_format in candidates:
        try:
            text = path.read_text()
        except OSError as e:
            logger.debug(f"Could not read {path}: {e}")
            continue
        if id_line.search(text):
            return path, file_format
    return None


def load_control_yaml(file_path: Path, substitutions: dict[str, Any]) -> Any:
    """Load a control or requirement file, expanding Jinja2 with ``substitutions``.

    If expansion fails or yields no mapping, the file is loaded as plain YAML,
    which raises ``yaml.YAMLError`` when it does not parse.
    """
    try:
        ssg_yaml = get_ssg_modules().yaml
        data = ssg_yaml.open_and_expand(str(file_path), substitutions)
        if isinstance(data, dict):
            return data
        logger.debug(f"Jinja2 expansion of {file_path} returned no mapping")
    except Exception as e:
        logger.debug(f"Jinja2 expansion failed for {file_path}: {e}")
    with open(file_path) as f:
        return yaml.safe_load(f)


class ControlDiscovery:
    """Control framework discovery."""

    def __init__(self) -> None:
        """Initialize control discovery."""
        self.content_repo = get_content_repository()
        self._product_env_cache: dict[str, dict[str, Any] | None] = {}

    def _get_controls_dirs(self, product: str | None = None) -> list[Path]:
        """Return ordered list of control directories to scan.

        Global controls directory is always first. Product-specific directories
        come after, so they can override global controls with the same policy ID.

        Args:
            product: Optional product ID to scope to. If None, all product
                     control directories are included.

        Returns:
            Ordered list of control directory paths (existing only).

        Raises:
            ValueError: If product is specified but not a known product.
        """
        dirs: list[Path] = []

        global_dir = self.content_repo.path / "controls"
        if global_dir.exists():
            dirs.append(global_dir)

        if product is not None:
            # Validate product exists via ProductDiscovery
            from content_agent.core.discovery.products import ProductDiscovery

            product_discovery = ProductDiscovery()
            known_products = [p.product_id for p in product_discovery.list_products().items]
            if product not in known_products:
                raise ValueError(
                    f"Unknown product '{product}'. "
                    f"Known products: {', '.join(sorted(known_products))}"
                )
            product_controls = self.content_repo.path / "products" / product / "controls"
            if product_controls.exists():
                dirs.append(product_controls)
        else:
            # Discover all product control directories
            from content_agent.core.discovery.products import ProductDiscovery

            product_discovery = ProductDiscovery()
            known_products = [p.product_id for p in product_discovery.list_products().items]
            for pid in sorted(known_products):
                product_controls = self.content_repo.path / "products" / pid / "controls"
                if product_controls.exists():
                    dirs.append(product_controls)

        return dirs

    def list_controls(self, product: str | None = None) -> list[str]:
        """List available control frameworks.

        Args:
            product: Optional product ID to scope discovery

        Returns:
            List of control framework names
        """
        logger.debug(f"Listing control frameworks (product={product})")

        # Build map of policy_id -> file_path; later dirs override earlier
        controls_map: dict[str, Path] = {}

        for controls_dir in self._get_controls_dirs(product):
            for control_file in controls_dir.glob("*.yml"):
                policy_id = control_file.stem
                if policy_id in controls_map:
                    logger.warning(
                        f"Control '{policy_id}' in {control_file} overrides "
                        f"previously found {controls_map[policy_id]}"
                    )
                controls_map[policy_id] = control_file

        controls = sorted(controls_map.keys())
        logger.info(f"Found {len(controls)} control frameworks")
        return controls

    def _resolve_control_file(self, control_id: str, product: str | None = None) -> Path | None:
        """Resolve the file path for a control ID using override semantics.

        Later directories override earlier ones.

        Args:
            control_id: Control framework identifier
            product: Optional product ID to scope resolution

        Returns:
            Path to the control file, or None if not found
        """
        resolved: Path | None = None

        for controls_dir in self._get_controls_dirs(product):
            candidate = controls_dir / f"{control_id}.yml"
            if candidate.exists():
                if resolved is not None:
                    logger.warning(
                        f"Control '{control_id}' in {candidate} overrides "
                        f"previously found {resolved}"
                    )
                resolved = candidate

        return resolved

    def get_control_details(
        self, control_id: str, product: str | None = None
    ) -> ControlFile | None:
        """Parse and return complete control file details.

        Args:
            control_id: Control framework identifier
            product: Optional product ID to scope discovery

        Returns:
            ControlFile with parsed details, or None if not found
        """
        logger.debug(f"Getting details for control: {control_id} (product={product})")

        control_file = self._resolve_control_file(control_id, product)
        if control_file is None:
            logger.warning(f"Control file not found: {control_id}")
            return None

        return self.parse_control_file(
            control_file, source_dir=control_file.parent, product=product
        )

    def parse_control_file(
        self, file_path: Path, source_dir: Path | None = None, product: str | None = None
    ) -> ControlFile | None:
        """Parse control YAML into structured model.

        Args:
            file_path: Path to control file
            source_dir: Directory from which this file was loaded
            product: Optional product ID for expanding Jinja2 in requirement files

        Returns:
            ControlFile object, or None if parsing fails
        """
        try:
            with open(file_path) as f:
                data = yaml.safe_load(f)

            parse_errors: list[str] = []

            # Parse included files if present
            if "includes" in data and data["includes"]:
                # Load included requirement files
                controls = []
                base_dir = file_path.parent / file_path.stem

                for include_path in data["includes"]:
                    full_path = base_dir / include_path
                    if full_path.exists():
                        try:
                            controls.extend(self._parse_requirement_file(full_path, product))
                        except Exception as e:
                            error_msg = f"Failed to parse requirement file {full_path}: {e}"
                            logger.warning(error_msg)
                            parse_errors.append(error_msg)
                    else:
                        logger.warning(f"Included file not found: {full_path}")

                data["controls"] = controls

            # Requirement files in the policy's directory, added to its own controls list
            else:
                directory = requirements_directory(file_path, data)
                if directory is not None:
                    controls = []
                    for ctrl_file in requirement_files(directory):
                        try:
                            controls.extend(self._parse_requirement_file(ctrl_file, product))
                        except Exception as e:
                            error_msg = f"Failed to parse requirement file {ctrl_file}: {e}"
                            logger.warning(error_msg)
                            parse_errors.append(error_msg)
                    data["controls"] = list(data.get("controls") or []) + controls
                elif data.get("controls_dir"):
                    missing = file_path.parent / data["controls_dir"]
                    logger.warning(f"Controls directory not found: {missing}")

            data["parse_errors"] = parse_errors

            # Set source_dir
            if source_dir is not None:
                data["source_dir"] = source_dir

            # Parse control file
            return ControlFile(**data)

        except Exception as e:
            logger.error(f"Failed to parse control file {file_path}: {e}")
            return None

    def search_controls(
        self,
        query: str,
        control_id: str | None = None,
        product: str | None = None,
    ) -> list[ControlRequirement]:
        """Search within control files for requirements.

        Args:
            query: Search query (matches title, description)
            control_id: Optional control framework to search within
            product: Optional product ID to scope discovery

        Returns:
            List of matching control requirements
        """
        logger.debug(
            f"Searching controls: query='{query}', control_id={control_id}, product={product}"
        )

        results = []

        # Determine which controls to search
        if control_id:
            control = self.get_control_details(control_id, product=product)
            controls_to_search = [control] if control else []
        else:
            control_ids = self.list_controls(product=product)
            controls_to_search = [
                c
                for cid in control_ids
                if (c := self.get_control_details(cid, product=product)) is not None
            ]

        # Search through controls
        query_lower = query.lower()

        for control in controls_to_search:
            for req in flatten_requirements(control.controls):
                # Search in title and description
                if (
                    query_lower in req.title.lower()
                    or query_lower in (req.description or "").lower()
                    or query_lower in req.id.lower()
                ):
                    results.append(req)

        logger.info(f"Found {len(results)} matching requirements")
        return results

    def _flatten_controls(self, controls: list[ControlRequirement]) -> list[ControlRequirement]:
        """Recursively flatten nested control structures.

        Args:
            controls: List of control requirements (may contain nested controls)

        Returns:
            Flat list of all requirements at every depth, parents before children
        """
        return flatten_requirements(controls)

    def get_control_rule_index(
        self,
        include_unmapped: bool = True,
        control_ids: list[str] | None = None,
        product: str | None = None,
    ) -> ControlRuleIndex:
        """Build complete index of all requirements with rule mappings.

        Args:
            include_unmapped: Whether to include requirements without rule mappings
            control_ids: Optional list of control framework IDs to index
            product: Optional product ID to scope discovery

        Returns:
            ControlRuleIndex with all indexed requirements
        """
        logger.debug(
            f"Building control rule index: include_unmapped={include_unmapped}, "
            f"control_ids={control_ids}, product={product}"
        )

        if control_ids is not None:
            ids_to_process = control_ids
        else:
            ids_to_process = self.list_controls(product=product)

        all_requirements: list[IndexedRequirement] = []
        all_rule_ids: set[str] = set()
        controls_indexed = 0

        for control_id in ids_to_process:
            control_file = self.get_control_details(control_id, product=product)
            if control_file is None:
                continue

            controls_indexed += 1
            flat_controls = self._flatten_controls(control_file.controls)

            for req in flat_controls:
                if not include_unmapped and not req.rules:
                    continue

                description = req.description[:300] if req.description else ""

                indexed = IndexedRequirement(
                    control_id=control_id,
                    requirement_id=req.id,
                    title=req.title,
                    description=description,
                    rules=req.rules,
                    status=req.status,
                    levels=req.levels,
                )
                all_requirements.append(indexed)
                all_rule_ids.update(req.rules)

        index = ControlRuleIndex(
            total_controls=controls_indexed,
            total_requirements=len(all_requirements),
            total_mapped_rules=len(all_rule_ids),
            requirements=all_requirements,
        )

        logger.info(
            f"Built control rule index: {index.total_controls} controls, "
            f"{index.total_requirements} requirements, "
            f"{index.total_mapped_rules} mapped rules"
        )
        return index

    def get_control_stats(self, control_id: str, product: str | None = None) -> ControlStats | None:
        """Compute aggregate requirement statistics for a control file.

        Args:
            control_id: Control framework identifier
            product: Optional product ID to scope discovery

        Returns:
            ControlStats with counts, or None if control not found
        """
        logger.debug(f"Computing stats for control: {control_id} (product={product})")

        control = self.get_control_details(control_id, product=product)
        if control is None:
            return None

        flat = self._flatten_controls(control.controls)

        by_status: dict[str, int] = {}
        mapped = 0
        unmapped = 0

        for req in flat:
            status = req.status
            by_status[status] = by_status.get(status, 0) + 1
            if req.rules:
                mapped += 1
            else:
                unmapped += 1

        return ControlStats(
            control_id=control.id,
            title=control.title,
            total=len(flat),
            by_status=by_status,
            mapped=mapped,
            unmapped=unmapped,
        )

    # Stopwords for compliance document similarity
    _STOPWORDS = frozenset(
        {
            "a",
            "an",
            "the",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "shall",
            "may",
            "might",
            "must",
            "can",
            "need",
            "to",
            "of",
            "in",
            "for",
            "on",
            "with",
            "at",
            "by",
            "from",
            "as",
            "into",
            "through",
            "during",
            "before",
            "after",
            "above",
            "below",
            "between",
            "and",
            "but",
            "or",
            "nor",
            "not",
            "no",
            "so",
            "if",
            "then",
            "than",
            "that",
            "this",
            "these",
            "those",
            "it",
            "its",
            "all",
            "each",
            "every",
            "any",
            "both",
            "such",
            "when",
            "where",
            "which",
            "who",
            "whom",
            "how",
            "what",
            "ensure",
            "operating",
            "system",
            "information",
        }
    )

    def _tokenize(self, text: str) -> set[str]:
        """Tokenize and normalize text for similarity comparison.

        Args:
            text: Text to tokenize

        Returns:
            Set of normalized tokens
        """
        import re

        text = re.sub(r"[^a-z0-9\s]", " ", text.lower())
        tokens = text.split()
        return {t for t in tokens if t not in self._STOPWORDS and len(t) > 2}

    def _jaccard_similarity(self, set_a: set[str], set_b: set[str]) -> float:
        """Compute Jaccard similarity between two token sets.

        Args:
            set_a: First token set
            set_b: Second token set

        Returns:
            Jaccard similarity coefficient (0.0 to 1.0)
        """
        if not set_a or not set_b:
            return 0.0
        intersection = set_a & set_b
        union = set_a | set_b
        return len(intersection) / len(union)

    def find_similar_requirements(
        self,
        requirement_text: str,
        min_similarity: float = 0.2,
        max_results: int = 20,
        exclude_control_id: str | None = None,
        product: str | None = None,
    ) -> list[SimilarRequirement]:
        """Find requirements with similar text across all control files.

        Args:
            requirement_text: Text to search for similar requirements
            min_similarity: Minimum Jaccard similarity threshold
            max_results: Maximum number of results to return
            exclude_control_id: Optional control framework to exclude
            product: Optional product ID to scope discovery

        Returns:
            List of SimilarRequirement objects sorted by similarity descending
        """
        logger.debug(
            f"Finding similar requirements: min_similarity={min_similarity}, "
            f"max_results={max_results}, exclude={exclude_control_id}, product={product}"
        )

        query_tokens = self._tokenize(requirement_text)
        if not query_tokens:
            return []

        index = self.get_control_rule_index(include_unmapped=True, product=product)
        results: list[SimilarRequirement] = []

        for req in index.requirements:
            if exclude_control_id and req.control_id == exclude_control_id:
                continue

            req_tokens = self._tokenize(req.title + " " + (req.description or ""))
            similarity = self._jaccard_similarity(query_tokens, req_tokens)

            if similarity >= min_similarity:
                matching = sorted(query_tokens & req_tokens)
                results.append(
                    SimilarRequirement(
                        control_id=req.control_id,
                        requirement_id=req.requirement_id,
                        title=req.title,
                        description=req.description,
                        rules=req.rules,
                        similarity_score=round(similarity, 4),
                        matching_terms=matching,
                    )
                )

        results.sort(key=lambda r: r.similarity_score, reverse=True)
        logger.info(f"Found {len(results)} similar requirements (returning top {max_results})")
        return results[:max_results]

    def get_requirement_file_path(
        self,
        control_id: str,
        requirement_id: str,
        product: str | None = None,
    ) -> RequirementFilePath | None:
        """Resolve the filesystem path for a specific requirement.

        Handles both inline (monolithic YAML) and directory-based (controls_dir) formats.

        Args:
            control_id: Control framework identifier
            requirement_id: Requirement identifier
            product: Optional product ID to scope discovery

        Returns:
            RequirementFilePath with resolved path, or None if not found
        """
        logger.debug(f"Resolving path for {control_id}/{requirement_id} (product={product})")

        control_file_path = self._resolve_control_file(control_id, product)
        if control_file_path is None:
            logger.warning(f"Control file not found: {control_id}")
            return None

        substitutions = (self._product_substitutions(product) if product else None) or {
            **GENERIC_SUBSTITUTIONS,
            "product": product or "",
        }
        try:
            data = load_control_yaml(control_file_path, substitutions)
        except Exception as e:
            logger.warning(f"Could not parse {control_file_path}: {e}")
            data = {}

        found = find_requirement_file(control_file_path, data, requirement_id)
        if found is not None:
            path, file_format = found
            return RequirementFilePath(
                control_id=control_id,
                requirement_id=requirement_id,
                file_path=path.resolve(),
                format=file_format,
                exists=True,
            )

        # In a directory-based policy, say where a new requirement's file would go
        directory = requirements_directory(control_file_path, data)
        subdir = data.get("controls_dir") if isinstance(data, dict) else None
        if directory is None and subdir:
            directory = control_file_path.parent / str(subdir)
        if directory is not None:
            return RequirementFilePath(
                control_id=control_id,
                requirement_id=requirement_id,
                file_path=(directory / f"{requirement_id}.yml").resolve(),
                format="directory",
                exists=False,
            )

        logger.debug(f"Requirement {requirement_id} not found in {control_id}")
        return None

    def list_unmapped_requirements(
        self,
        control_id: str,
        status_filter: list[str] | None = None,
        product: str | None = None,
    ) -> list[IndexedRequirement] | None:
        """List requirements that need rule mappings.

        Args:
            control_id: Control framework identifier
            status_filter: Status values to include (default: ["pending"])
            product: Optional product ID to scope discovery

        Returns:
            List of unmapped IndexedRequirement objects, or None if control not found
        """
        logger.debug(f"Listing unmapped requirements for control: {control_id} (product={product})")

        control = self.get_control_details(control_id, product=product)
        if control is None:
            return None

        if status_filter is None:
            status_filter = ["pending"]

        flat = self._flatten_controls(control.controls)
        results: list[IndexedRequirement] = []

        for req in flat:
            if req.status in status_filter or not req.rules:
                description = req.description[:300] if req.description else ""
                results.append(
                    IndexedRequirement(
                        control_id=control_id,
                        requirement_id=req.id,
                        title=req.title,
                        description=description,
                        rules=req.rules,
                        status=req.status,
                        levels=req.levels,
                    )
                )

        logger.info(f"Found {len(results)} unmapped requirements in '{control_id}'")
        return results

    def _product_substitutions(self, product: str) -> dict[str, Any] | None:
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

    def _load_requirement_yaml(self, file_path: Path, product: str | None) -> Any:
        """Load a requirement file, expanding Jinja2 like the build does.

        Requirement files use Jinja2 such as ``{{{ full_name }}}`` in titles. With a
        product, the product's variables are used. Without one, product conditionals
        are false and full_name is "The operating system", the wording SRGs use where
        ComplianceAsCode substitutes the product name. If expansion fails, the file
        is loaded as plain YAML.
        """
        substitutions = (self._product_substitutions(product) if product else None) or {
            **GENERIC_SUBSTITUTIONS,
            "product": product or "",
        }
        return load_control_yaml(file_path, substitutions)

    def _parse_requirement_file(
        self, file_path: Path, product: str | None = None
    ) -> list[ControlRequirement]:
        """Parse a requirement file from a control file's subdirectory or includes.

        ComplianceAsCode puts the requirements of each file in a ``controls`` list,
        and a file can hold several, like the NIST 800-53 family files. A file with
        a single requirement at the top level is accepted too.

        Args:
            file_path: Path to requirement file
            product: Optional product ID for Jinja2 expansion

        Returns:
            The requirements defined in the file

        Raises:
            Exception: If YAML parsing or model construction fails
        """
        data = self._load_requirement_yaml(file_path, product)

        if isinstance(data, dict) and "id" not in data and isinstance(data.get("controls"), list):
            return [ControlRequirement(**item) for item in data["controls"]]
        return [ControlRequirement(**data)]


def list_controls(product: str | None = None) -> list[str]:
    """List available control frameworks.

    Args:
        product: Optional product ID to scope discovery

    Returns:
        List of control framework names
    """
    discovery = ControlDiscovery()
    return discovery.list_controls(product=product)


def get_control_details(control_id: str, product: str | None = None) -> ControlFile | None:
    """Get control framework details.

    Args:
        control_id: Control framework identifier
        product: Optional product ID to scope discovery

    Returns:
        ControlFile with details, or None if not found
    """
    discovery = ControlDiscovery()
    return discovery.get_control_details(control_id, product=product)


def search_controls(
    query: str, control_id: str | None = None, product: str | None = None
) -> list[ControlRequirement]:
    """Search control requirements.

    Args:
        query: Search query
        control_id: Optional control framework to search within
        product: Optional product ID to scope discovery

    Returns:
        List of matching requirements
    """
    discovery = ControlDiscovery()
    return discovery.search_controls(query, control_id, product=product)


def get_control_rule_index(
    include_unmapped: bool = True,
    control_ids: list[str] | None = None,
    product: str | None = None,
) -> ControlRuleIndex:
    """Build complete index of all requirements with rule mappings.

    Args:
        include_unmapped: Whether to include requirements without rule mappings
        control_ids: Optional list of control framework IDs to index
        product: Optional product ID to scope discovery

    Returns:
        ControlRuleIndex with all indexed requirements
    """
    discovery = ControlDiscovery()
    return discovery.get_control_rule_index(include_unmapped, control_ids, product=product)


def get_control_stats(control_id: str, product: str | None = None) -> ControlStats | None:
    """Compute aggregate requirement statistics for a control file.

    Args:
        control_id: Control framework identifier
        product: Optional product ID to scope discovery

    Returns:
        ControlStats with counts, or None if not found
    """
    discovery = ControlDiscovery()
    return discovery.get_control_stats(control_id, product=product)


def get_requirement_file_path(
    control_id: str, requirement_id: str, product: str | None = None
) -> RequirementFilePath | None:
    """Resolve the filesystem path for a specific requirement.

    Args:
        control_id: Control framework identifier
        requirement_id: Requirement identifier
        product: Optional product ID to scope discovery

    Returns:
        RequirementFilePath with resolved path, or None if not found
    """
    discovery = ControlDiscovery()
    return discovery.get_requirement_file_path(control_id, requirement_id, product=product)


def find_similar_requirements(
    requirement_text: str,
    min_similarity: float = 0.2,
    max_results: int = 20,
    exclude_control_id: str | None = None,
    product: str | None = None,
) -> list[SimilarRequirement]:
    """Find requirements with similar text across all control files.

    Args:
        requirement_text: Text to search for similar requirements
        min_similarity: Minimum Jaccard similarity threshold
        max_results: Maximum number of results to return
        exclude_control_id: Optional control framework to exclude
        product: Optional product ID to scope discovery

    Returns:
        List of SimilarRequirement objects sorted by similarity descending
    """
    discovery = ControlDiscovery()
    return discovery.find_similar_requirements(
        requirement_text, min_similarity, max_results, exclude_control_id, product=product
    )


def list_unmapped_requirements(
    control_id: str,
    status_filter: list[str] | None = None,
    product: str | None = None,
) -> list[IndexedRequirement] | None:
    """List requirements that need rule mappings.

    Args:
        control_id: Control framework identifier
        status_filter: Status values to include (default: ["pending"])
        product: Optional product ID to scope discovery

    Returns:
        List of unmapped IndexedRequirement objects, or None if control not found
    """
    discovery = ControlDiscovery()
    return discovery.list_unmapped_requirements(control_id, status_filter, product=product)
