"""Build artifacts discovery implementation.

This module provides access to rendered content from the build/<product> directories.
These files contain the final content after Jinja template processing and variable expansion.
"""

import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

from content_agent.core.integration import get_content_repository
from content_agent.models import DatastreamInfo, RenderedRule, RenderSearchResult

logger = logging.getLogger(__name__)


class BuildArtifactsDiscovery:
    """Discovery and access for build artifacts."""

    def __init__(self) -> None:
        """Initialize build artifacts discovery."""
        self.content_repo = get_content_repository()

    def list_built_products(self) -> list[str]:
        """List products that have been built and have artifacts available.

        Returns:
            List of product identifiers with build artifacts
        """
        logger.debug("Listing built products")

        build_path = self.content_repo.build_path
        if not build_path.exists():
            logger.warning(f"Build directory does not exist: {build_path}")
            return []

        built_products = []
        for product_dir in build_path.iterdir():
            if product_dir.is_dir() and not product_dir.name.startswith("."):
                # Check if it looks like a product build (has some common files/dirs)
                if self._is_product_build_dir(product_dir):
                    built_products.append(product_dir.name)

        logger.info(f"Found {len(built_products)} built products")
        return sorted(built_products)

    def get_rendered_rule(self, product: str, rule_id: str) -> RenderedRule | None:
        """Get rendered rule content from build directory.

        Args:
            product: Product identifier
            rule_id: Rule identifier

        Returns:
            RenderedRule or None if not found
        """
        logger.debug(f"Getting rendered rule: {rule_id} for product: {product}")

        product_build = self.content_repo.get_product_build_path(product)
        if not product_build:
            logger.warning(f"No build directory for product: {product}")
            return None

        # Build directory structure:
        # build/{product}/rules/{rule_id}.json - rendered rule metadata
        # build/{product}/fixes_from_templates/{type}/{rule_id}.sh - rendered remediations
        # build/{product}/checks/oval/{rule_id}.xml - rendered OVAL checks

        # Read rendered rule JSON
        import json

        rule_json_path = product_build / "rules" / f"{rule_id}.json"
        if not rule_json_path.exists():
            logger.debug(f"Rule {rule_id} not found in build for {product}")
            return None

        with open(rule_json_path) as f:
            rule_data = json.load(f)

        # Convert JSON back to YAML-like format for consistency
        import yaml

        rendered_yaml = yaml.dump(rule_data, default_flow_style=False, sort_keys=False)

        # Read rendered OVAL
        rendered_oval = None
        oval_path = product_build / "checks" / "oval" / f"{rule_id}.xml"
        if oval_path.exists():
            try:
                rendered_oval = oval_path.read_text()
            except Exception as e:
                logger.debug(f"Failed to read OVAL: {e}")

        # Read rendered remediations
        rendered_remediations = {}
        remediation_types = {
            "bash": ".sh",
            "ansible": ".yml",
            "anaconda": ".anaconda",
            "puppet": ".pp",
            "ignition": ".yml",
            "kubernetes": ".yml",
            "blueprint": ".toml",
        }

        for rem_type, ext in remediation_types.items():
            rem_dir = product_build / "fixes_from_templates" / rem_type
            if rem_dir.exists():
                rem_file = rem_dir / f"{rule_id}{ext}"
                if rem_file.exists():
                    try:
                        rendered_remediations[rem_type] = rem_file.read_text()
                    except Exception as e:
                        logger.debug(f"Failed to read {rem_type} remediation: {e}")

        return RenderedRule(
            rule_id=rule_id,
            product=product,
            rendered_yaml=rendered_yaml,
            rendered_oval=rendered_oval,
            rendered_remediations=rendered_remediations,
            build_path=str(rule_json_path.parent.relative_to(self.content_repo.path)),
        )

    def get_datastream_info(self, product: str) -> DatastreamInfo | None:
        """Get information about a built datastream.

        Args:
            product: Product identifier

        Returns:
            DatastreamInfo or None if not found
        """
        logger.debug(f"Getting datastream info for product: {product}")

        # Look for datastream file
        build_path = self.content_repo.build_path
        datastream_patterns = [
            f"ssg-{product}-ds.xml",
            f"ssg-{product}-xccdf.xml",
            f"{product}/ssg-{product}-ds.xml",
        ]

        datastream_path = None
        for pattern in datastream_patterns:
            potential_path = build_path / pattern
            if potential_path.exists():
                datastream_path = potential_path
                break

        if not datastream_path:
            logger.debug(f"Datastream not found for product: {product}")
            return DatastreamInfo(
                product=product,
                datastream_path=f"build/ssg-{product}-ds.xml",
                file_size=0,
                build_time=None,
                profiles_count=0,
                rules_count=0,
                exists=False,
            )

        # Get file info
        file_size = datastream_path.stat().st_size
        build_time = datetime.fromtimestamp(datastream_path.stat().st_mtime)

        # Parse datastream for counts (basic parsing)
        profiles_count = 0
        rules_count = 0
        try:
            tree = ET.parse(datastream_path)
            root = tree.getroot()

            # Count profiles (rough estimation)
            profiles = root.findall(".//{http://checklists.nist.gov/xccdf/1.2}Profile")
            profiles_count = len(profiles)

            # Count rules (rough estimation)
            rules = root.findall(".//{http://checklists.nist.gov/xccdf/1.2}Rule")
            rules_count = len(rules)
        except Exception as e:
            logger.debug(f"Failed to parse datastream XML: {e}")

        return DatastreamInfo(
            product=product,
            datastream_path=str(datastream_path.relative_to(self.content_repo.path)),
            file_size=file_size,
            build_time=build_time,
            profiles_count=profiles_count,
            rules_count=rules_count,
            exists=True,
        )

    def search_rendered_content(
        self, query: str, product: str | None = None, limit: int = 50
    ) -> list[RenderSearchResult]:
        """Search in rendered build artifacts.

        Args:
            query: Search query
            product: Optional product filter
            limit: Maximum results

        Returns:
            List of RenderSearchResult objects
        """
        logger.debug(f"Searching rendered content: query={query}, product={product}")

        results = []
        query_lower = query.lower()

        # Determine which products to search
        if product:
            products = [product]
        else:
            products = self.list_built_products()

        # Search through build artifacts
        for prod in products:
            product_build = self.content_repo.get_product_build_path(prod)
            if not product_build:
                continue

            # Search in rule JSON files
            rules_dir = product_build / "rules"
            if rules_dir.exists():
                for rule_json in rules_dir.glob("*.json"):
                    try:
                        content = rule_json.read_text()
                        if query_lower in content.lower():
                            # Extract snippet around match
                            snippet = self._extract_snippet(content, query_lower)
                            rule_id = rule_json.stem  # filename without .json
                            results.append(
                                RenderSearchResult(
                                    rule_id=rule_id,
                                    product=prod,
                                    match_type="rule_json",
                                    match_snippet=snippet,
                                    file_path=str(rule_json.relative_to(self.content_repo.path)),
                                )
                            )
                            if len(results) >= limit:
                                return results
                    except Exception as e:
                        logger.debug(f"Failed to search in {rule_json}: {e}")

            # Search in remediation files
            fixes_dir = product_build / "fixes_from_templates"
            if fixes_dir.exists():
                for rem_file in fixes_dir.glob("**/*"):
                    if not rem_file.is_file():
                        continue
                    # Skip if not a text file
                    if rem_file.suffix not in [".sh", ".yml", ".yaml", ".pp", ".toml", ".anaconda"]:
                        continue

                    try:
                        content = rem_file.read_text()
                        if query_lower in content.lower():
                            snippet = self._extract_snippet(content, query_lower)
                            rule_id = rem_file.stem  # filename without extension
                            rem_type = rem_file.parent.name  # bash, ansible, etc.
                            results.append(
                                RenderSearchResult(
                                    rule_id=rule_id,
                                    product=prod,
                                    match_type=f"remediation_{rem_type}",
                                    match_snippet=snippet,
                                    file_path=str(rem_file.relative_to(self.content_repo.path)),
                                )
                            )
                            if len(results) >= limit:
                                return results
                    except Exception as e:
                        logger.debug(f"Failed to search in {rem_file}: {e}")

            # Search in OVAL files
            oval_dir = product_build / "checks" / "oval"
            if oval_dir.exists():
                for oval_file in oval_dir.glob("*.xml"):
                    try:
                        content = oval_file.read_text()
                        if query_lower in content.lower():
                            snippet = self._extract_snippet(content, query_lower)
                            rule_id = oval_file.stem
                            results.append(
                                RenderSearchResult(
                                    rule_id=rule_id,
                                    product=prod,
                                    match_type="oval",
                                    match_snippet=snippet,
                                    file_path=str(oval_file.relative_to(self.content_repo.path)),
                                )
                            )
                            if len(results) >= limit:
                                return results
                    except Exception as e:
                        logger.debug(f"Failed to search in {oval_file}: {e}")

        logger.info(f"Found {len(results)} matches in rendered content")
        return results

    def _is_product_build_dir(self, path: Path) -> bool:
        """Check if a directory looks like a product build directory.

        Args:
            path: Directory path

        Returns:
            True if it appears to be a product build
        """
        # Look for common build artifacts
        indicators = [
            "ssg-*.xml",  # Datastreams
            "guides/",  # HTML guides
            "ansible/",  # Ansible playbooks
            "bash/",  # Bash scripts
            "rules/",  # Rules directory
        ]

        for indicator in indicators:
            if list(path.glob(indicator)):
                return True

        return False

    def _extract_snippet(self, content: str, query: str, context_chars: int = 100) -> str:
        """Extract a snippet around the search match.

        Args:
            content: Full content
            query: Search query (lowercase)
            context_chars: Characters of context on each side

        Returns:
            Snippet with surrounding context
        """
        content_lower = content.lower()
        pos = content_lower.find(query)
        if pos == -1:
            return ""

        start = max(0, pos - context_chars)
        end = min(len(content), pos + len(query) + context_chars)

        snippet = content[start:end]
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."

        return snippet


# Module-level functions for convenient access
def list_built_products() -> list[str]:
    """List products that have been built.

    Returns:
        List of product identifiers
    """
    discovery = BuildArtifactsDiscovery()
    return discovery.list_built_products()


def get_rendered_rule(product: str, rule_id: str) -> RenderedRule | None:
    """Get rendered rule content.

    Args:
        product: Product identifier
        rule_id: Rule identifier

    Returns:
        RenderedRule or None if not found
    """
    discovery = BuildArtifactsDiscovery()
    return discovery.get_rendered_rule(product, rule_id)


def get_datastream_info(product: str) -> DatastreamInfo | None:
    """Get datastream information.

    Args:
        product: Product identifier

    Returns:
        DatastreamInfo or None if not found
    """
    discovery = BuildArtifactsDiscovery()
    return discovery.get_datastream_info(product)


def search_rendered_content(
    query: str, product: str | None = None, limit: int = 50
) -> list[RenderSearchResult]:
    """Search rendered content.

    Args:
        query: Search query
        product: Optional product filter
        limit: Maximum results

    Returns:
        List of RenderSearchResult objects
    """
    discovery = BuildArtifactsDiscovery()
    return discovery.search_rendered_content(query, product, limit)
