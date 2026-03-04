"""MCP resource handlers."""

import logging
from typing import Any
from urllib.parse import urlparse

from content_agent.core import discovery

logger = logging.getLogger(__name__)


async def handle_resource_read(uri: str) -> str:
    """Handle resource read requests.

    Args:
        uri: Resource URI (e.g., cac://products, cac://rules/sshd_set_idle_timeout)

    Returns:
        Resource content as string (JSON-serialized)

    Raises:
        ValueError: If URI is invalid or resource not found
    """
    logger.debug(f"Reading resource: {uri}")

    parsed = urlparse(uri)
    if parsed.scheme != "cac":
        raise ValueError(f"Invalid URI scheme: {parsed.scheme}, expected 'cac'")

    # Handle both cac://products and cac:products formats
    # urlparse treats "cac://products" as netloc, not path
    if parsed.netloc:
        # cac://products format - netloc contains the resource type
        path_parts = [parsed.netloc] + [p for p in parsed.path.strip("/").split("/") if p]
    else:
        # cac:products format - path contains everything
        path_parts = [p for p in parsed.path.strip("/").split("/") if p]

    if not path_parts or not path_parts[0]:
        raise ValueError("Invalid resource path")

    resource_type = path_parts[0]

    # Handle different resource types
    if resource_type == "products":
        if len(path_parts) == 1:
            # List all products
            products_result = discovery.list_products()
            import json

            return json.dumps([p.model_dump() for p in products_result.items], indent=2)
        elif len(path_parts) == 2:
            # Get specific product
            product_id = path_parts[1]
            product = discovery.get_product_details(product_id)
            if not product:
                raise ValueError(f"Product not found: {product_id}")
            import json

            return json.dumps(product.model_dump(), indent=2)
        else:
            raise ValueError(f"Invalid products resource path: {uri}")

    elif resource_type == "rules":
        if len(path_parts) == 1:
            # List all rules (limited)
            rules_result = discovery.search_rules(limit=100)
            import json

            return json.dumps([r.model_dump() for r in rules_result.items], indent=2)
        elif len(path_parts) == 2:
            # Get specific rule
            rule_id = path_parts[1]
            rule = discovery.get_rule_details(rule_id)
            if not rule:
                raise ValueError(f"Rule not found: {rule_id}")
            import json

            return json.dumps(rule.model_dump(), indent=2)
        else:
            raise ValueError(f"Invalid rules resource path: {uri}")

    elif resource_type == "templates":
        if len(path_parts) == 1:
            # List all templates
            templates = discovery.list_templates()
            import json

            return json.dumps([t.model_dump() for t in templates], indent=2)
        elif len(path_parts) == 2:
            # Get template schema
            template_name = path_parts[1]
            schema = discovery.get_template_schema(template_name)
            if not schema:
                raise ValueError(f"Template not found: {template_name}")
            import json

            return json.dumps(schema.model_dump(), indent=2)
        else:
            raise ValueError(f"Invalid templates resource path: {uri}")

    elif resource_type == "profiles":
        if len(path_parts) == 1:
            # List all profiles
            profiles_result = discovery.list_profiles()
            import json

            return json.dumps([p.model_dump() for p in profiles_result.items], indent=2)
        elif len(path_parts) == 3:
            # Get specific profile (product/profile_id)
            product = path_parts[1]
            profile_id = path_parts[2]
            profile = discovery.get_profile_details(profile_id, product)
            if not profile:
                raise ValueError(f"Profile not found: {profile_id} in {product}")
            import json

            return json.dumps(profile.model_dump(), indent=2)
        else:
            raise ValueError(f"Invalid profiles resource path: {uri}")

    elif resource_type == "controls":
        if len(path_parts) == 1:
            # List control frameworks
            controls = discovery.list_controls()
            import json

            return json.dumps(controls, indent=2)
        else:
            raise ValueError(f"Invalid controls resource path: {uri}")

    elif resource_type == "build":
        # Handle build artifacts resources
        if len(path_parts) == 1:
            # List built products
            products = discovery.list_built_products()
            import json

            return json.dumps({"products": products, "count": len(products)}, indent=2)
        elif len(path_parts) == 2:
            # Get product datastream info
            product = path_parts[1]
            info = discovery.get_datastream_info(product)
            if not info:
                raise ValueError(f"No build artifacts for product: {product}")
            import json

            return json.dumps(info.model_dump(), indent=2)
        elif len(path_parts) >= 4 and path_parts[2] == "rules":
            # Get rendered rule: build/{product}/rules/{rule_id}
            product = path_parts[1]
            rule_id = path_parts[3]
            rendered = discovery.get_rendered_rule(product, rule_id)
            if not rendered:
                raise ValueError(f"Rendered rule not found: {rule_id} for {product}")
            import json

            return json.dumps(rendered.model_dump(), indent=2)
        else:
            raise ValueError(f"Invalid build resource path: {uri}")

    else:
        raise ValueError(f"Unknown resource type: {resource_type}")


def list_resources() -> list[dict[str, Any]]:
    """List available resources.

    Returns:
        List of resource descriptors
    """
    return [
        {
            "uri": "cac://products",
            "name": "Products",
            "description": "List of all available products",
            "mimeType": "application/json",
        },
        {
            "uri": "cac://products/{product_id}",
            "name": "Product Details",
            "description": "Detailed information about a specific product",
            "mimeType": "application/json",
        },
        {
            "uri": "cac://rules",
            "name": "Rules",
            "description": "List of available rules",
            "mimeType": "application/json",
        },
        {
            "uri": "cac://rules/{rule_id}",
            "name": "Rule Details",
            "description": "Detailed information about a specific rule",
            "mimeType": "application/json",
        },
        {
            "uri": "cac://templates",
            "name": "Templates",
            "description": "List of available templates",
            "mimeType": "application/json",
        },
        {
            "uri": "cac://templates/{template_name}",
            "name": "Template Schema",
            "description": "Schema definition for a template",
            "mimeType": "application/json",
        },
        {
            "uri": "cac://profiles",
            "name": "Profiles",
            "description": "List of all profiles",
            "mimeType": "application/json",
        },
        {
            "uri": "cac://profiles/{product}/{profile_id}",
            "name": "Profile Details",
            "description": "Detailed information about a specific profile",
            "mimeType": "application/json",
        },
        {
            "uri": "cac://controls",
            "name": "Control Frameworks",
            "description": "List of available control frameworks",
            "mimeType": "application/json",
        },
        {
            "uri": "cac://build",
            "name": "Built Products",
            "description": "List of products with build artifacts available",
            "mimeType": "application/json",
        },
        {
            "uri": "cac://build/{product}",
            "name": "Product Build Info",
            "description": "Build information and datastream details for a product",
            "mimeType": "application/json",
        },
        {
            "uri": "cac://build/{product}/rules/{rule_id}",
            "name": "Rendered Rule",
            "description": "Fully rendered rule content from build directory (after Jinja processing)",
            "mimeType": "application/json",
        },
    ]
