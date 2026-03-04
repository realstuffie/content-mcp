"""Control framework discovery implementation."""

import logging
from pathlib import Path

import yaml

from content_agent.core.integration import get_content_repository
from content_agent.models.control import (
    ControlFile,
    ControlRequirement,
    ControlRuleIndex,
    ControlStats,
    IndexedRequirement,
    RequirementFilePath,
    SimilarRequirement,
)

logger = logging.getLogger(__name__)


class ControlDiscovery:
    """Control framework discovery."""

    def __init__(self) -> None:
        """Initialize control discovery."""
        self.content_repo = get_content_repository()

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
            known_products = [p.product_id for p in product_discovery.list_products()]
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
            known_products = [p.product_id for p in product_discovery.list_products()]
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

        return self.parse_control_file(control_file, source_dir=control_file.parent)

    def parse_control_file(
        self, file_path: Path, source_dir: Path | None = None
    ) -> ControlFile | None:
        """Parse control YAML into structured model.

        Args:
            file_path: Path to control file
            source_dir: Directory from which this file was loaded

        Returns:
            ControlFile object, or None if parsing fails
        """
        try:
            with open(file_path) as f:
                data = yaml.safe_load(f)

            # Parse included files if present
            if "includes" in data and data["includes"]:
                # Load included requirement files
                controls = []
                base_dir = file_path.parent / file_path.stem

                for include_path in data["includes"]:
                    full_path = base_dir / include_path
                    if full_path.exists():
                        req = self._parse_requirement_file(full_path)
                        if req:
                            controls.append(req)
                    else:
                        logger.warning(f"Included file not found: {full_path}")

                data["controls"] = controls

            # Handle controls_dir pattern (subdirectory of individual control YAML files)
            elif "controls_dir" in data and data["controls_dir"]:
                controls = []
                controls_subdir = file_path.parent / data["controls_dir"]
                if controls_subdir.exists() and controls_subdir.is_dir():
                    for ctrl_file in sorted(controls_subdir.glob("*.yml")):
                        req = self._parse_requirement_file(ctrl_file)
                        if req:
                            controls.append(req)
                else:
                    logger.warning(f"Controls directory not found: {controls_subdir}")

                if "controls" not in data:
                    data["controls"] = []
                data["controls"].extend(controls)

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
            for req in control.controls:
                # Search in title and description
                if (
                    query_lower in req.title.lower()
                    or query_lower in req.description.lower()
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
            Flat list of all leaf-level requirements
        """
        flat: list[ControlRequirement] = []
        for ctrl in controls:
            flat.append(ctrl)
        return flat

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

            req_tokens = self._tokenize(req.title + " " + req.description)
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

        with open(control_file_path) as f:
            data = yaml.safe_load(f)

        # Directory-based format: controls_dir field points to subdirectory
        if data.get("controls_dir"):
            req_file = control_file_path.parent / data["controls_dir"] / f"{requirement_id}.yml"
            return RequirementFilePath(
                control_id=control_id,
                requirement_id=requirement_id,
                file_path=req_file.resolve(),
                format="directory",
                exists=req_file.exists(),
            )

        # Inline format: requirement must exist in the controls list
        for req in data.get("controls", []):
            if isinstance(req, dict) and req.get("id") == requirement_id:
                return RequirementFilePath(
                    control_id=control_id,
                    requirement_id=requirement_id,
                    file_path=control_file_path.resolve(),
                    format="inline",
                    exists=True,
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

    def _parse_requirement_file(self, file_path: Path) -> ControlRequirement | None:
        """Parse individual requirement file.

        Args:
            file_path: Path to requirement file

        Returns:
            ControlRequirement object, or None if parsing fails
        """
        try:
            with open(file_path) as f:
                data = yaml.safe_load(f)

            return ControlRequirement(**data)

        except Exception as e:
            logger.error(f"Failed to parse requirement file {file_path}: {e}")
            return None


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
