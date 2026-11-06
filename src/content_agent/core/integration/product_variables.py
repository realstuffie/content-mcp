"""Load the Jinja2 variables the ComplianceAsCode build uses for a product."""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def load_product_variables(
    ssg_products: Any, repo_path: Path, product: str
) -> dict[str, Any] | None:
    """Return a product's Jinja2 variables, or None when the product can't be loaded.

    Like ssg.environment.open_environment(), this is the product's product.yml plus
    the product_properties directory, which together define variables such as
    full_name, families, auid and audisp_conf_path.

    Args:
        ssg_products: The ssg.products module
        repo_path: Path to the content repository
        product: Product ID, such as "ubuntu2204"
    """
    product_yaml = repo_path / "products" / product / "product.yml"
    try:
        loaded = ssg_products.load_product_yaml(str(product_yaml))
        properties_dir = repo_path / "product_properties"
        if properties_dir.is_dir():
            loaded.read_properties_from_directory(str(properties_dir))
        return dict(loaded)
    except Exception as e:
        logger.debug(f"Could not load the variables of product {product}: {e}")
        return None
