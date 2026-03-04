"""Product discovery implementation."""

import logging
from pathlib import Path

import yaml

from content_agent.core.integration import get_content_repository, get_ssg_modules
from content_agent.models import DiscoveryResult, ProductDetails, ProductStats, ProductSummary

logger = logging.getLogger(__name__)


class ProductDiscovery:
    """Product discovery and information retrieval."""

    def __init__(self) -> None:
        """Initialize product discovery."""
        self.content_repo = get_content_repository()
        self.ssg = get_ssg_modules()
        self._product_cache: dict | None = None

    def list_products(self) -> DiscoveryResult[ProductSummary]:
        """List all available products.

        Returns:
            DiscoveryResult with ProductSummary items and any parse errors
        """
        logger.debug("Listing all products")
        result: DiscoveryResult[ProductSummary] = DiscoveryResult()

        products_dir = self.content_repo.path / "products"
        if not products_dir.exists():
            logger.error(f"Products directory not found: {products_dir}")
            return result

        for product_dir in products_dir.iterdir():
            if not product_dir.is_dir():
                continue

            product_yml = product_dir / "product.yml"
            if not product_yml.exists():
                continue

            try:
                summary = self._load_product_summary(product_dir.name, product_yml)
                result.items.append(summary)
            except Exception as e:
                error_msg = f"Failed to load product {product_dir.name}: {e}"
                logger.warning(error_msg)
                result.errors.append(error_msg)

        result.items.sort(key=lambda p: p.product_id)
        logger.info(f"Found {len(result.items)} products")
        return result

    def get_product_details(self, product_id: str) -> ProductDetails | None:
        """Get detailed information about a product.

        Args:
            product_id: Product identifier

        Returns:
            ProductDetails or None if not found
        """
        logger.debug(f"Getting details for product: {product_id}")

        products_dir = self.content_repo.path / "products"
        product_dir = products_dir / product_id

        if not product_dir.exists():
            logger.warning(f"Product not found: {product_id}")
            return None

        product_yml = product_dir / "product.yml"
        if not product_yml.exists():
            logger.warning(f"product.yml not found for {product_id}")
            return None

        # Note: safe_load is appropriate here - product.yml files do not contain
        # Jinja2 macros per ComplianceAsCode ADR-0002 (Jinja2 Boundaries)
        with open(product_yml) as f:
            data = yaml.safe_load(f)

        # Get profiles
        profiles = self._get_product_profiles(product_id)

        # Get stats
        stats = self._calculate_product_stats(product_id)

        # Determine benchmark root
        benchmark_root = self._get_benchmark_root(data)

        details = ProductDetails(
            product_id=product_id,
            name=data.get("full_name", product_id),
            product_type=data.get("product_type", "unknown"),
            version=data.get("product_version"),
            description=data.get("description"),
            profiles=profiles,
            benchmark_root=benchmark_root,
            product_dir=str(product_dir.relative_to(self.content_repo.path)),
            cpe=data.get("cpe"),
            stats=stats,
        )

        logger.debug(f"Loaded details for product {product_id}")
        return details

    def _load_product_summary(self, product_id: str, product_yml: Path) -> ProductSummary:
        """Load product summary from product.yml.

        Args:
            product_id: Product identifier
            product_yml: Path to product.yml

        Returns:
            ProductSummary

        Raises:
            Exception: If YAML parsing or model construction fails
        """
        # Note: safe_load is appropriate here - product.yml files do not contain
        # Jinja2 macros per ComplianceAsCode ADR-0002 (Jinja2 Boundaries)
        with open(product_yml) as f:
            data = yaml.safe_load(f)

        return ProductSummary(
            product_id=product_id,
            name=data.get("full_name", product_id),
            product_type=data.get("product_type", "unknown"),
            version=data.get("product_version"),
            description=data.get("description"),
        )

    def _get_product_profiles(self, product_id: str) -> list[str]:
        """Get list of profile IDs for a product.

        Args:
            product_id: Product identifier

        Returns:
            List of profile IDs
        """
        profiles_dir = self.content_repo.path / "products" / product_id / "profiles"

        if not profiles_dir.exists():
            return []

        profile_ids = []
        for profile_file in profiles_dir.glob("*.profile"):
            profile_id = profile_file.stem
            profile_ids.append(profile_id)

        return sorted(profile_ids)

    def _calculate_product_stats(self, product_id: str) -> ProductStats | None:
        """Calculate statistics for a product.

        Args:
            product_id: Product identifier

        Returns:
            ProductStats or None
        """
        # For MVP, return None - full stats calculation would require
        # loading all rules and profiles which could be slow
        # This can be implemented in Phase 2 with caching
        return None

    def _get_benchmark_root(self, product_data: dict) -> str:
        """Determine benchmark root from product data.

        Args:
            product_data: Product YAML data

        Returns:
            Benchmark root path
        """
        # Most products use linux_os/guide, but some have custom roots
        benchmark_root = product_data.get("benchmark_root", "linux_os/guide")
        return benchmark_root


def list_products() -> DiscoveryResult[ProductSummary]:
    """List all available products.

    Returns:
        DiscoveryResult with ProductSummary items and any parse errors
    """
    discovery = ProductDiscovery()
    return discovery.list_products()


def get_product_details(product_id: str) -> ProductDetails | None:
    """Get detailed information about a product.

    Args:
        product_id: Product identifier

    Returns:
        ProductDetails or None if not found
    """
    discovery = ProductDiscovery()
    return discovery.get_product_details(product_id)
