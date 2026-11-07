"""MCP tool handlers."""

import json
import logging
import re
from typing import Any

from content_agent.core import discovery, scaffolding
from content_agent.core.parsing.base_parser import BaseParser
from content_agent.models.control import CONTROL_STATUSES, DocumentSection

logger = logging.getLogger(__name__)


# Tool definitions
TOOLS = [
    # Discovery tools
    {
        "name": "list_products",
        "description": "List all available products in the ComplianceAsCode/content repository",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_product_details",
        "description": "Get detailed information about a specific product",
        "inputSchema": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "string",
                    "description": "Product identifier (e.g., rhel9, fedora, ocp4)",
                }
            },
            "required": ["product_id"],
        },
    },
    {
        "name": "search_rules",
        "description": "Search for rules by keyword, product, or severity",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (matches rule ID, title, description)",
                },
                "product": {
                    "type": "string",
                    "description": (
                        "Filter by product ID: rules that the product's profiles select, "
                        "or that have identifiers for the product"
                    ),
                },
                "severity": {
                    "type": "string",
                    "description": "Filter by severity (low, medium, high, unknown)",
                    "enum": ["low", "medium", "high", "unknown"],
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results (default: 50)",
                    "default": 50,
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_rule_details",
        "description": "Get complete information about a specific rule. Automatically includes rendered content metadata from build artifacts if available (low token usage by default).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "rule_id": {
                    "type": "string",
                    "description": "Rule identifier",
                },
                "include_rendered": {
                    "type": "boolean",
                    "description": "Include rendered content from builds (default: true). Automatically detects and includes info about rendered YAML, OVAL, and remediations.",
                    "default": True,
                },
                "product": {
                    "type": "string",
                    "description": "Optional product filter for rendered content. If specified, only includes rendered content for this product.",
                },
                "rendered_detail": {
                    "type": "string",
                    "description": "Detail level for rendered content: 'metadata' (default, ~2k tokens - sizes and availability only) or 'full' (~18k tokens - includes complete rendered text). Use 'full' only when you need to see actual rendered content.",
                    "enum": ["metadata", "full"],
                    "default": "metadata",
                },
            },
            "required": ["rule_id"],
        },
    },
    {
        "name": "list_templates",
        "description": "List all available rule templates",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_template_schema",
        "description": "Get a template's parameters, the languages it generates, and an example from a real rule. Parameters come from docs/templates/template_reference.md and from the vars of the rules that use the template, including parameters the reference leaves out; used_by_rules says how many rules set each one. Rules can set a value for one product with a name@product key, such as pkgname@ubuntu2204.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "template_name": {
                    "type": "string",
                    "description": "Template name",
                }
            },
            "required": ["template_name"],
        },
    },
    {
        "name": "list_profiles",
        "description": "List profiles for a product or all products",
        "inputSchema": {
            "type": "object",
            "properties": {
                "product": {
                    "type": "string",
                    "description": "Optional product filter",
                }
            },
            "required": [],
        },
    },
    {
        "name": "get_profile_details",
        "description": "Get detailed information about a profile",
        "inputSchema": {
            "type": "object",
            "properties": {
                "profile_id": {
                    "type": "string",
                    "description": "Profile identifier",
                },
                "product": {
                    "type": "string",
                    "description": "Product identifier",
                },
            },
            "required": ["profile_id", "product"],
        },
    },
    # Scaffolding tools
    {
        "name": "generate_rule_boilerplate",
        "description": "Generate basic rule structure with boilerplate files",
        "inputSchema": {
            "type": "object",
            "properties": {
                "rule_id": {
                    "type": "string",
                    "description": "Rule identifier (will be used as directory name)",
                },
                "title": {
                    "type": "string",
                    "description": "Rule title",
                },
                "description": {
                    "type": "string",
                    "description": "Rule description",
                },
                "severity": {
                    "type": "string",
                    "description": "Rule severity",
                    "enum": ["low", "medium", "high", "unknown"],
                },
                "product": {
                    "type": "string",
                    "description": "Primary product for this rule",
                },
                "location": {
                    "type": "string",
                    "description": "Optional custom location path (e.g., linux_os/guide/services/ssh)",
                },
                "rationale": {
                    "type": "string",
                    "description": "Optional rationale for the rule",
                },
            },
            "required": ["rule_id", "title", "description", "severity", "product"],
        },
    },
    {
        "name": "validate_rule_yaml",
        "description": "Validate rule.yml YAML content",
        "inputSchema": {
            "type": "object",
            "properties": {
                "rule_yaml": {
                    "type": "string",
                    "description": "YAML content to validate",
                },
                "check_references": {
                    "type": "boolean",
                    "description": "Whether to check reference format (default: true)",
                    "default": True,
                },
                "auto_fix": {
                    "type": "boolean",
                    "description": "Whether to attempt auto-fixing issues (default: false)",
                    "default": False,
                },
            },
            "required": ["rule_yaml"],
        },
    },
    {
        "name": "generate_rule_from_template",
        "description": "Generate rule using a template (Phase 3 feature)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "template_name": {
                    "type": "string",
                    "description": "Template name",
                },
                "parameters": {
                    "type": "object",
                    "description": "Template parameters",
                },
                "rule_id": {
                    "type": "string",
                    "description": "Rule identifier",
                },
                "product": {
                    "type": "string",
                    "description": "Product identifier",
                },
            },
            "required": ["template_name", "parameters", "rule_id", "product"],
        },
    },
    # Build artifacts tools
    {
        "name": "list_built_products",
        "description": "List products that have been built and have artifacts available in build/ directory",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_rendered_rule",
        "description": "Get fully rendered rule content from build directory (after Jinja template processing and variable expansion). Shows the actual content that goes into the datastream.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "product": {
                    "type": "string",
                    "description": "Product identifier (e.g., rhel9, fedora)",
                },
                "rule_id": {
                    "type": "string",
                    "description": "Rule identifier",
                },
            },
            "required": ["product", "rule_id"],
        },
    },
    {
        "name": "get_datastream_info",
        "description": "Get information about a built datastream for a product",
        "inputSchema": {
            "type": "object",
            "properties": {
                "product": {
                    "type": "string",
                    "description": "Product identifier",
                },
            },
            "required": ["product"],
        },
    },
    {
        "name": "search_rendered_content",
        "description": "Search in rendered build artifacts (useful for finding actual values after template expansion, searching in final content)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query",
                },
                "product": {
                    "type": "string",
                    "description": "Optional product filter",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results (default: 50)",
                    "default": 50,
                },
            },
            "required": ["query"],
        },
    },
    # Control file tools
    {
        "name": "parse_policy_document",
        "description": "Parse security policy document (PDF, Markdown, HTML, or text) and extract requirements with exact text preservation",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "Path to file or URL of policy document",
                },
                "document_type": {
                    "type": "string",
                    "description": "Document type",
                    "enum": ["pdf", "markdown", "text", "html"],
                },
                "requirement_id": {
                    "type": "string",
                    "description": "Optional: extract only the section matching this requirement ID (e.g., 'R34', '1.1.1.1', 'RHEL-09-171011'). Returns the same JSON structure with sections filtered to the match.",
                },
            },
            "required": ["source", "document_type"],
        },
    },
    {
        "name": "generate_control_files",
        "description": "Generate control file structure from extracted requirements. Use 'inline' format for a single monolithic file or 'directory' format for a parent file with individual requirement files.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "policy_id": {
                    "type": "string",
                    "description": "Policy identifier",
                },
                "policy_title": {
                    "type": "string",
                    "description": "Policy title",
                },
                "format": {
                    "type": "string",
                    "enum": ["inline", "directory"],
                    "description": "Output format. 'inline': single file with all requirements in a controls list. 'directory': parent file with controls_dir referencing individual requirement files.",
                },
                "source_document": {
                    "type": "string",
                    "description": "Source document path or URL",
                },
                "requirements_json": {
                    "type": "string",
                    "description": 'JSON string of extracted requirements. Format: {"requirements": [{"id": "...", "title": "...", "description": "...", "section": "..."}]} or just the array',
                },
                "version": {
                    "type": "string",
                    "description": "Optional version string (e.g., 'v3r1', '1.0')",
                },
                "levels": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional compliance levels (e.g., ['high', 'medium', 'low'])",
                },
                "product": {
                    "type": "string",
                    "description": "Optional product ID; generates into products/<product>/controls/ instead of controls/",
                },
            },
            "required": ["policy_id", "policy_title", "format", "requirements_json"],
        },
    },
    {
        "name": "validate_control_file",
        "description": "Validate control file YAML syntax, structure, and rule references",
        "inputSchema": {
            "type": "object",
            "properties": {
                "control_file_path": {
                    "type": "string",
                    "description": "Path to control file",
                },
            },
            "required": ["control_file_path"],
        },
    },
    {
        "name": "review_control_generation",
        "description": "Review generated control files with validation, text comparison, and AI suggestions",
        "inputSchema": {
            "type": "object",
            "properties": {
                "control_file_path": {
                    "type": "string",
                    "description": "Path to generated control file",
                },
                "generate_suggestions": {
                    "type": "boolean",
                    "description": "Whether to generate AI rule suggestions (default: true)",
                    "default": True,
                },
            },
            "required": ["control_file_path"],
        },
    },
    {
        "name": "list_controls",
        "description": "List available control frameworks",
        "inputSchema": {
            "type": "object",
            "properties": {
                "product": {
                    "type": "string",
                    "description": "Optional product ID to scope to product-specific controls (e.g., 'rhel9')",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_control_details",
        "description": "Get detailed information about a control framework",
        "inputSchema": {
            "type": "object",
            "properties": {
                "control_id": {
                    "type": "string",
                    "description": "Control framework identifier",
                },
                "product": {
                    "type": "string",
                    "description": "Optional product ID to scope to product-specific controls (e.g., 'rhel9')",
                },
            },
            "required": ["control_id"],
        },
    },
    {
        "name": "get_control_stats",
        "description": "Get aggregate requirement statistics for a control file (total, by-status, mapped/unmapped counts). Use this instead of counting requirements manually.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "control_id": {
                    "type": "string",
                    "description": "Control framework identifier",
                },
                "product": {
                    "type": "string",
                    "description": "Optional product ID to scope to product-specific controls (e.g., 'rhel9')",
                },
            },
            "required": ["control_id"],
        },
    },
    {
        "name": "get_control_rule_index",
        "description": "Build a complete index of all requirements and rule mappings across all control frameworks. Useful for cross-framework rule discovery.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "include_unmapped": {
                    "type": "boolean",
                    "description": "Include requirements without rule mappings (default: true)",
                    "default": True,
                },
                "control_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of control framework IDs to index (default: all)",
                },
                "product": {
                    "type": "string",
                    "description": "Optional product ID to scope to product-specific controls (e.g., 'rhel9')",
                },
            },
            "required": [],
        },
    },
    {
        "name": "find_similar_requirements",
        "description": "Find requirements with similar text across all control frameworks using text similarity. Useful for discovering how different frameworks address the same security concern.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "requirement_text": {
                    "type": "string",
                    "description": "Requirement text to search for similar requirements",
                },
                "min_similarity": {
                    "type": "number",
                    "description": "Minimum similarity score 0.0-1.0 (default: 0.2)",
                    "default": 0.2,
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results (default: 20)",
                    "default": 20,
                },
                "exclude_control_id": {
                    "type": "string",
                    "description": "Optional control framework to exclude from results",
                },
                "product": {
                    "type": "string",
                    "description": "Optional product ID to scope to product-specific controls (e.g., 'rhel9')",
                },
            },
            "required": ["requirement_text"],
        },
    },
    {
        "name": "get_rule_product_availability",
        "description": "Check which products include a given rule, via identifiers, profile selections, and build artifacts. Useful for cross-product compliance analysis.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "rule_id": {
                    "type": "string",
                    "description": "Rule identifier",
                },
            },
            "required": ["rule_id"],
        },
    },
    {
        "name": "search_control_requirements",
        "description": "Search within control files for specific requirements",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (matches title, description, ID)",
                },
                "control_id": {
                    "type": "string",
                    "description": "Optional control framework to search within",
                },
                "product": {
                    "type": "string",
                    "description": "Optional product ID to scope to product-specific controls (e.g., 'rhel9')",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_requirement_file_path",
        "description": "Resolve the filesystem path for a specific requirement in a control file. Handles both inline (monolithic YAML) and directory-based (controls_dir) formats.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "control_id": {
                    "type": "string",
                    "description": "Control framework identifier (e.g., 'anssi', 'srg_gpos')",
                },
                "requirement_id": {
                    "type": "string",
                    "description": "Requirement identifier (e.g., 'R1', 'SRG-OS-000001-GPOS-00001')",
                },
                "product": {
                    "type": "string",
                    "description": "Optional product ID to scope to product-specific controls (e.g., 'rhel9')",
                },
            },
            "required": ["control_id", "requirement_id"],
        },
    },
    {
        "name": "list_unmapped_requirements",
        "description": "List requirements in a control file that need rule mappings. Returns requirements filtered by status, defaulting to 'pending' status. Lighter than get_control_details when you only need the work queue.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "control_id": {
                    "type": "string",
                    "description": "Control framework identifier (e.g., 'anssi', 'srg_gpos')",
                },
                "status_filter": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Status values to include (default: ['pending']). Common values: pending, manual, partial, does not meet",
                },
                "product": {
                    "type": "string",
                    "description": "Optional product ID to scope to product-specific controls (e.g., 'rhel9')",
                },
            },
            "required": ["control_id"],
        },
    },
    # Scaffolding tools - write operations
    {
        "name": "update_requirement_rules",
        "description": "Update the rules list and status for a specific requirement in a control file. Handles both inline (monolithic YAML) and directory-based (controls_dir) formats. Preserves Jinja2 templating, comments, and formatting, and changes only the requirement's own rules and status, not those of nested requirements. The edited file is parsed before it is written; if anything else would change, the file is left unchanged and an error is returned. Requirements whose rules use Jinja2 conditionals are refused.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "control_id": {
                    "type": "string",
                    "description": "Control framework identifier (e.g., 'anssi', 'srg_gpos')",
                },
                "requirement_id": {
                    "type": "string",
                    "description": "Requirement identifier (e.g., 'R1', 'SRG-OS-000001-GPOS-00001')",
                },
                "rules": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Rule IDs to set for this requirement (replaces existing rules)",
                },
                "status": {
                    "type": "string",
                    "enum": list(CONTROL_STATUSES),
                    "description": "ComplianceAsCode control status to set (default: 'automated')",
                },
                "product": {
                    "type": "string",
                    "description": "Optional product ID to scope to product-specific controls (e.g., 'rhel9')",
                },
            },
            "required": ["control_id", "requirement_id", "rules"],
        },
    },
]


_REQ_ID_PATTERN = re.compile(r"(?:^|[\s*>)\]#])(\d+(?:\.\d+){2,}|R\d+)\b")


def _find_section_by_requirement_id(
    sections: list[DocumentSection], requirement_id: str
) -> DocumentSection | None:
    """Find a section whose title contains the requirement ID.

    Uses word-boundary matching to avoid partial matches
    (e.g., 'R3' should not match 'R30').

    For flat-heading documents (e.g., CIS benchmarks where all headings are
    level 1), collects following sibling sections that belong to the matched
    requirement — stopping at the next requirement ID heading.
    """
    escaped = re.escape(requirement_id)
    pattern = re.compile(r"(?<![.\w])" + escaped + r"(?![.\w])", re.IGNORECASE)

    # Search titles first (most policy documents use the ID in headings)
    for i, section in enumerate(sections):
        if pattern.search(section.title):
            # Collect following sibling sections that are body headings
            # (not new requirement IDs) for flat-heading documents
            extra_content_parts: list[str] = []
            for sibling in sections[i + 1 :]:
                if _REQ_ID_PATTERN.search(sibling.title):
                    break  # hit next requirement
                extra_content_parts.append(f"## {sibling.title}\n\n{sibling.content}")
            if extra_content_parts:
                combined = section.content
                if combined:
                    combined += "\n\n"
                combined += "\n\n".join(extra_content_parts)
                section = DocumentSection(
                    id=section.id,
                    title=section.title,
                    level=section.level,
                    content=combined,
                    subsections=section.subsections,
                    parent_id=section.parent_id,
                )
            return section
        # Also recurse into subsections
        found = _find_section_by_requirement_id(section.subsections, requirement_id)
        if found:
            return found

    # Fallback: search section content (STIG has IDs in body, not headings)
    for section in sections:
        if pattern.search(section.content):
            return section
        for sub in section.subsections:
            if pattern.search(sub.content):
                return sub

    return None


async def handle_tool_call(name: str, arguments: dict[str, Any]) -> list[Any]:
    """Handle tool call.

    Args:
        name: Tool name
        arguments: Tool arguments

    Returns:
        List of content items (text or image)

    Raises:
        ValueError: If tool not found or execution fails
    """
    logger.info(f"Calling tool: {name} with arguments: {arguments}")

    try:
        # Discovery tools
        if name == "list_products":
            discovery_result: Any = discovery.list_products()
            result: Any = [p.model_dump(mode="json") for p in discovery_result.items]
            text = json.dumps(result, indent=2)
            if discovery_result.errors:
                warnings = "\n".join(f"- {e}" for e in discovery_result.errors)
                text = f"WARNING: {len(discovery_result.errors)} product(s) failed to parse:\n{warnings}\n\n{text}"
            return [{"type": "text", "text": text}]

        elif name == "get_product_details":
            product_id = arguments["product_id"]
            product = discovery.get_product_details(product_id)
            if not product:
                return [{"type": "text", "text": f"Product not found: {product_id}"}]
            return [{"type": "text", "text": json.dumps(product.model_dump(mode="json"), indent=2)}]

        elif name == "search_rules":
            query = arguments.get("query")
            product = arguments.get("product")
            severity = arguments.get("severity")
            limit = arguments.get("limit", 50)

            discovery_result = discovery.search_rules(
                query=query, product=product, severity=severity, limit=limit
            )
            result = [r.model_dump(mode="json") for r in discovery_result.items]
            summary = f"Found {len(discovery_result.items)} rules matching search criteria.\n\n"
            if discovery_result.errors:
                warnings = "\n".join(f"- {e}" for e in discovery_result.errors)
                summary += f"WARNING: {len(discovery_result.errors)} rule(s) failed to parse:\n{warnings}\n\n"
            return [{"type": "text", "text": summary + json.dumps(result, indent=2)}]

        elif name == "get_rule_details":
            rule_id = arguments["rule_id"]
            include_rendered = arguments.get("include_rendered", True)
            product = arguments.get("product")
            rendered_detail = arguments.get("rendered_detail", "metadata")

            rule = discovery.get_rule_details(rule_id, include_rendered, product, rendered_detail)
            if not rule:
                return [{"type": "text", "text": f"Rule not found: {rule_id}"}]

            # Add informative message about rendered content
            result_json = json.dumps(rule.model_dump(mode="json"), indent=2)
            if include_rendered and rule.rendered:
                products_with_rendered = list(rule.rendered.keys())
                detail_msg = (
                    "metadata only (use rendered_detail='full' to see actual content)"
                    if rendered_detail == "metadata"
                    else "full content"
                )
                summary = (
                    f"Rule details for '{rule_id}' with rendered {detail_msg} "
                    f"from {len(products_with_rendered)} product(s): {', '.join(products_with_rendered)}\n\n"
                )
                return [{"type": "text", "text": summary + result_json}]
            elif include_rendered:
                summary = f"Rule details for '{rule_id}' (no build artifacts found)\n\n"
                return [{"type": "text", "text": summary + result_json}]
            else:
                return [{"type": "text", "text": result_json}]

        elif name == "list_templates":
            templates = discovery.list_templates()
            result = [t.model_dump(mode="json") for t in templates]
            return [{"type": "text", "text": json.dumps(result, indent=2)}]

        elif name == "get_template_schema":
            template_name = arguments["template_name"]
            schema = discovery.get_template_schema(template_name)
            if not schema:
                return [{"type": "text", "text": f"Template not found: {template_name}"}]
            return [{"type": "text", "text": json.dumps(schema.model_dump(mode="json"), indent=2)}]

        elif name == "list_profiles":
            product = arguments.get("product")
            discovery_result = discovery.list_profiles(product=product)
            result = [p.model_dump(mode="json") for p in discovery_result.items]
            text = json.dumps(result, indent=2)
            if discovery_result.errors:
                warnings = "\n".join(f"- {e}" for e in discovery_result.errors)
                text = f"WARNING: {len(discovery_result.errors)} profile(s) failed to parse:\n{warnings}\n\n{text}"
            return [{"type": "text", "text": text}]

        elif name == "get_profile_details":
            profile_id = arguments["profile_id"]
            product = arguments["product"]
            profile = discovery.get_profile_details(profile_id, product)
            if not profile:
                return [
                    {
                        "type": "text",
                        "text": f"Profile not found: {profile_id} in {product}",
                    }
                ]
            return [{"type": "text", "text": json.dumps(profile.model_dump(mode="json"), indent=2)}]

        # Scaffolding tools
        elif name == "generate_rule_boilerplate":
            result = scaffolding.generate_rule_boilerplate(
                rule_id=arguments["rule_id"],
                title=arguments["title"],
                description=arguments["description"],
                severity=arguments["severity"],
                product=arguments["product"],
                location=arguments.get("location"),
                rationale=arguments.get("rationale"),
            )
            return [{"type": "text", "text": json.dumps(result.model_dump(mode="json"), indent=2)}]

        elif name == "validate_rule_yaml":
            result = scaffolding.validate_rule_yaml(
                yaml_content=arguments["rule_yaml"],
                check_references=arguments.get("check_references", True),
                auto_fix=arguments.get("auto_fix", False),
            )
            return [{"type": "text", "text": json.dumps(result.model_dump(mode="json"), indent=2)}]

        elif name == "generate_rule_from_template":
            result = scaffolding.generate_rule_from_template(
                template_name=arguments["template_name"],
                parameters=arguments["parameters"],
                rule_id=arguments["rule_id"],
                product=arguments["product"],
            )
            return [{"type": "text", "text": json.dumps(result.model_dump(mode="json"), indent=2)}]

        # Build artifacts tools
        elif name == "list_built_products":
            products = discovery.list_built_products()
            summary = f"Found {len(products)} products with build artifacts.\n\n"
            result = {"products": products, "count": len(products)}
            return [{"type": "text", "text": summary + json.dumps(result, indent=2)}]

        elif name == "get_rendered_rule":
            product = arguments["product"]
            rule_id = arguments["rule_id"]
            rendered = discovery.get_rendered_rule(product, rule_id)
            if not rendered:
                return [
                    {
                        "type": "text",
                        "text": f"Rendered rule not found: {rule_id} for product {product}.\n"
                        f"Make sure the product has been built (./build_product {product}).",
                    }
                ]
            return [
                {"type": "text", "text": json.dumps(rendered.model_dump(mode="json"), indent=2)}
            ]

        elif name == "get_datastream_info":
            product = arguments["product"]
            info = discovery.get_datastream_info(product)
            if not info:
                return [
                    {
                        "type": "text",
                        "text": f"Datastream info not available for product: {product}",
                    }
                ]
            return [{"type": "text", "text": json.dumps(info.model_dump(mode="json"), indent=2)}]

        elif name == "search_rendered_content":
            query = arguments["query"]
            product = arguments.get("product")
            limit = arguments.get("limit", 50)

            results = discovery.search_rendered_content(query, product, limit)
            result = [r.model_dump(mode="json") for r in results]
            summary = f"Found {len(results)} matches in rendered build artifacts.\n\n"
            return [{"type": "text", "text": summary + json.dumps(result, indent=2)}]

        # Control file tools
        elif name == "parse_policy_document":
            from pathlib import Path

            from content_agent.core.parsing import (
                HTMLParser,
                MarkdownParser,
                PDFParser,
                TextParser,
            )

            source = arguments["source"]
            doc_type = arguments["document_type"]

            # Select parser
            parser: BaseParser
            if doc_type == "pdf":
                parser = PDFParser()
            elif doc_type == "markdown":
                parser = MarkdownParser()
            elif doc_type == "text":
                parser = TextParser()
            elif doc_type == "html":
                parser = HTMLParser()
            else:
                return [{"type": "text", "text": f"Unsupported document type: {doc_type}"}]

            # Parse document
            parsed = parser.parse(source)

            # Filter sections by requirement ID if provided
            requirement_id = arguments.get("requirement_id")
            if requirement_id:
                matching = _find_section_by_requirement_id(parsed.sections, requirement_id)
                if matching:
                    parsed.sections = [matching]
                else:
                    parsed.sections = []
                    parsed.metadata["requirement_not_found"] = requirement_id

            result = parsed.model_dump(mode="json")
            summary = f"Parsed {doc_type} document: {parsed.title}\n"
            summary += f"Sections: {len(parsed.sections)}\n"
            summary += f"Source: {parsed.source_path}\n\n"

            return [{"type": "text", "text": summary + json.dumps(result, indent=2)}]

        elif name == "generate_control_files":
            from pathlib import Path

            from content_agent.core.scaffolding.control_generator import ControlGenerator
            from content_agent.models.control import ExtractedRequirement

            policy_id = arguments["policy_id"]
            policy_title = arguments["policy_title"]
            requirements_json = arguments["requirements_json"]
            source_document = arguments.get("source_document")
            version = arguments.get("version")
            levels = arguments.get("levels")
            # Parse requirements JSON
            requirements_data = json.loads(requirements_json)

            # Handle both wrapped and unwrapped formats
            if isinstance(requirements_data, dict) and "requirements" in requirements_data:
                reqs_list = requirements_data["requirements"]
            elif isinstance(requirements_data, list):
                reqs_list = requirements_data
            else:
                return [
                    {
                        "type": "text",
                        "text": "Invalid requirements format. Expected list or object with 'requirements' key.",
                    }
                ]

            # Map fields to ExtractedRequirement format
            requirements = []
            for r in reqs_list:
                # Map fields: description->text, id->potential_id, section->section_title
                section_title = r.get("section", "default")
                section_id = (
                    section_title.lower().replace(" ", "_").replace(":", "").replace("&", "and")
                )

                # Determine requirement text (for YAML title field)
                # Priority: description > text > title
                # ComplianceAsCode format requires full requirement text in title field
                req_text = r.get("description") or r.get("text") or r.get("title") or ""

                # Store short title in context if it's different from description
                short_title = r.get("title")
                context_note = None
                if short_title and r.get("description") and short_title != r.get("description"):
                    context_note = f"Short title: {short_title}"

                req = ExtractedRequirement(
                    text=req_text,
                    section_id=section_id,
                    section_title=section_title,
                    potential_id=r.get("id", r.get("potential_id")),
                    context=context_note,
                )
                requirements.append(req)

            # Generate control files
            product = arguments.get("product")
            generator = ControlGenerator()
            result = generator.generate_control_structure(
                policy_id=policy_id,
                policy_title=policy_title,
                requirements=requirements,
                format=arguments["format"],
                source_document=source_document,
                version=version,
                levels=levels,
                product=product,
            )

            summary = f"Generated control structure for {policy_id}\n"
            summary += f"Success: {result.success}\n"
            summary += f"Total requirements: {result.total_requirements}\n"
            summary += f"Files created: {len(result.requirement_files)}\n"
            summary += f"Parent file: {result.parent_file_path}\n\n"

            return [
                {
                    "type": "text",
                    "text": summary + json.dumps(result.model_dump(mode="json"), indent=2),
                }
            ]

        elif name == "validate_control_file":
            from pathlib import Path

            from content_agent.core.scaffolding.control_validators import (
                ControlValidator,
            )

            control_file_path = Path(arguments["control_file_path"])
            validator = ControlValidator()
            result = validator.validate_control_file(control_file_path)

            summary = f"Validation: {'PASSED' if result.valid else 'FAILED'}\n"
            summary += f"Errors: {len(result.errors)}\n"
            summary += f"Warnings: {len(result.warnings)}\n\n"

            return [
                {
                    "type": "text",
                    "text": summary + json.dumps(result.model_dump(mode="json"), indent=2),
                }
            ]

        elif name == "review_control_generation":
            from pathlib import Path

            from content_agent.config.settings import get_settings
            from content_agent.core.ai.claude_client import ClaudeClient
            from content_agent.core.ai.rule_mapper import RuleMapper
            from content_agent.core.review.mapping_reviewer import MappingReviewer

            control_file_path = Path(arguments["control_file_path"])
            generate_suggestions = arguments.get("generate_suggestions", True)

            # Setup reviewer
            reviewer_kwargs = {}
            if generate_suggestions:
                settings = get_settings()
                if settings.ai.enabled and settings.ai.claude_api_key:
                    client = ClaudeClient(
                        api_key=settings.ai.claude_api_key,
                        model=settings.ai.model,
                        max_tokens=settings.ai.max_tokens,
                        temperature=settings.ai.temperature,
                    )
                    mapper = RuleMapper(client)
                    reviewer_kwargs["rule_mapper"] = mapper

            reviewer = MappingReviewer(**reviewer_kwargs)
            report = reviewer.review_control_file(
                control_file_path=control_file_path,
                generate_suggestions=generate_suggestions,
            )

            # Format report
            formatted = reviewer.format_review_report(report)

            return [{"type": "text", "text": formatted}]

        elif name == "list_controls":
            from content_agent.core.discovery.controls import list_controls

            product = arguments.get("product")
            controls = list_controls(product=product)
            summary = f"Found {len(controls)} control frameworks\n\n"
            result = {"controls": controls, "count": len(controls)}
            return [{"type": "text", "text": summary + json.dumps(result, indent=2)}]

        elif name == "get_control_details":
            from content_agent.core.discovery.controls import get_control_details
            from content_agent.models.control import flatten_requirements

            control_id = arguments["control_id"]
            product = arguments.get("product")
            control = get_control_details(control_id, product=product)

            if not control:
                return [{"type": "text", "text": f"Control not found: {control_id}"}]

            summary = f"Control framework: {control.title}\n"
            summary += f"Requirements: {len(flatten_requirements(control.controls))}\n"
            if control.parse_errors:
                warnings = "\n".join(f"- {e}" for e in control.parse_errors)
                summary += f"\nWARNING: {len(control.parse_errors)} requirement(s) failed to parse:\n{warnings}\n"
            summary += "\n"

            return [
                {
                    "type": "text",
                    "text": summary + json.dumps(control.model_dump(mode="json"), indent=2),
                }
            ]

        elif name == "get_control_stats":
            from content_agent.core.discovery.controls import get_control_stats

            control_id = arguments["control_id"]
            product = arguments.get("product")
            stats = get_control_stats(control_id, product=product)

            if not stats:
                return [{"type": "text", "text": f"Control not found: {control_id}"}]

            summary = (
                f"Control: {stats.title}\n"
                f"Total requirements: {stats.total}\n"
                f"Mapped: {stats.mapped}, Unmapped: {stats.unmapped}\n\n"
            )

            return [
                {
                    "type": "text",
                    "text": summary + json.dumps(stats.model_dump(mode="json"), indent=2),
                }
            ]

        elif name == "search_control_requirements":
            from content_agent.core.discovery.controls import search_controls

            query = arguments["query"]
            control_id = arguments.get("control_id")
            product = arguments.get("product")

            control_requirements = search_controls(
                query=query, control_id=control_id, product=product
            )
            result = [r.model_dump(mode="json") for r in control_requirements]
            summary = f"Found {len(control_requirements)} matching requirements\n\n"

            return [{"type": "text", "text": summary + json.dumps(result, indent=2)}]

        elif name == "get_control_rule_index":
            from content_agent.core.discovery.controls import (
                get_control_rule_index,
            )

            include_unmapped = arguments.get("include_unmapped", True)
            control_ids = arguments.get("control_ids")
            product = arguments.get("product")

            index = get_control_rule_index(
                include_unmapped=include_unmapped, control_ids=control_ids, product=product
            )
            summary = (
                f"Control rule index: {index.total_controls} controls, "
                f"{index.total_requirements} requirements, "
                f"{index.total_mapped_rules} unique mapped rules\n\n"
            )
            return [
                {
                    "type": "text",
                    "text": summary + json.dumps(index.model_dump(mode="json"), indent=2),
                }
            ]

        elif name == "find_similar_requirements":
            from content_agent.core.discovery.controls import (
                find_similar_requirements,
            )

            requirement_text = arguments["requirement_text"]
            min_similarity = arguments.get("min_similarity", 0.2)
            max_results = arguments.get("max_results", 20)
            exclude_control_id = arguments.get("exclude_control_id")
            product = arguments.get("product")

            similar_results = find_similar_requirements(
                requirement_text=requirement_text,
                min_similarity=min_similarity,
                max_results=max_results,
                exclude_control_id=exclude_control_id,
                product=product,
            )
            result = [r.model_dump(mode="json") for r in similar_results]
            summary = f"Found {len(similar_results)} similar requirements\n\n"
            return [{"type": "text", "text": summary + json.dumps(result, indent=2)}]

        elif name == "get_rule_product_availability":
            from content_agent.core.discovery.rules import (
                get_rule_product_availability,
            )

            rule_id = arguments["rule_id"]
            availability = get_rule_product_availability(rule_id)
            if not availability:
                return [{"type": "text", "text": f"Rule not found: {rule_id}"}]

            summary = (
                f"Product availability for rule '{rule_id}': "
                f"{len(availability.products_with_identifiers)} products with identifiers, "
                f"{len(availability.products_in_profiles)} products in profiles\n\n"
            )
            return [
                {
                    "type": "text",
                    "text": summary + json.dumps(availability.model_dump(mode="json"), indent=2),
                }
            ]

        elif name == "get_requirement_file_path":
            from content_agent.core.discovery.controls import get_requirement_file_path

            control_id = arguments["control_id"]
            requirement_id = arguments["requirement_id"]
            product = arguments.get("product")
            result = get_requirement_file_path(control_id, requirement_id, product=product)

            if not result:
                return [
                    {
                        "type": "text",
                        "text": f"Requirement '{requirement_id}' not found in control '{control_id}'",
                    }
                ]

            summary = (
                f"Requirement '{requirement_id}' in '{control_id}': "
                f"format={result.format}, exists={result.exists}\n"
                f"Path: {result.file_path}\n\n"
            )
            return [
                {
                    "type": "text",
                    "text": summary + json.dumps(result.model_dump(mode="json"), indent=2),
                }
            ]

        elif name == "list_unmapped_requirements":
            from content_agent.core.discovery.controls import list_unmapped_requirements

            control_id = arguments["control_id"]
            status_filter = arguments.get("status_filter")
            product = arguments.get("product")

            requirements = list_unmapped_requirements(control_id, status_filter, product=product)  # type: ignore[assignment]

            if requirements is None:
                return [{"type": "text", "text": f"Control not found: {control_id}"}]

            result = [r.model_dump(mode="json") for r in requirements]
            summary = f"Found {len(requirements)} unmapped requirements in '{control_id}'\n\n"
            return [{"type": "text", "text": summary + json.dumps(result, indent=2)}]

        elif name == "update_requirement_rules":
            from content_agent.core.scaffolding.control_updater import ControlUpdater

            control_id = arguments["control_id"]
            requirement_id = arguments["requirement_id"]
            rules = arguments["rules"]
            status = arguments.get("status", "automated")
            product = arguments.get("product")

            updater = ControlUpdater()
            result = updater.update_requirement_rules(
                control_id=control_id,
                requirement_id=requirement_id,
                rules=rules,
                status=status,
                product=product,
            )

            if not result.success:
                error_text = f"Update failed: {'; '.join(result.errors)}"
                return [{"type": "text", "text": error_text}]

            summary = (
                f"Updated requirement '{requirement_id}' in '{control_id}'\n"
                f"Rules set: {rules}\n"
                f"Status: {status}\n"
                f"File: {result.file_path}\n"
            )
            if result.warnings:
                summary += "Warnings: " + "; ".join(result.warnings) + "\n"
            summary += "\n"
            return [
                {
                    "type": "text",
                    "text": summary + json.dumps(result.model_dump(mode="json"), indent=2),
                }
            ]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        logger.error(f"Tool execution failed: {e}", exc_info=True)
        error_msg = f"Tool execution failed: {str(e)}"
        return [{"type": "text", "text": error_msg}]


def list_tools() -> list[dict[str, Any]]:
    """List available tools.

    Returns:
        List of tool definitions
    """
    return TOOLS
