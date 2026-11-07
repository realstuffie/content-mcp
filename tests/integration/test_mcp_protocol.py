"""Exercise MCP messages through SDK sessions and the actual stdio entry point."""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path

import pytest
import yaml
from mcp.shared.exceptions import McpError
from mcp.shared.memory import create_connected_server_and_client_session

from content_agent.server.mcp_server import ContentAgentServer

RULE = "protocol_test_rule"
TITLE = 'SSH access — accès sécurisé 日本語 "quoted"'


@pytest.fixture
def protocol_repo(initialized_content_repo):
    """A small repository with every readable resource, including build timestamps."""
    from content_agent.core.integration import get_ssg_modules

    root = initialized_content_repo.path
    rule = root / "linux_os" / "guide" / RULE / "rule.yml"
    rule.parent.mkdir(parents=True)
    rule.write_text(
        yaml.safe_dump(
            {
                "documentation_complete": True,
                "title": TITLE,
                "description": "Disable direct root login over SSH.\nPreserve this text.",
                "rationale": "Restrict privileged access.",
                "severity": "medium",
                "template": {"name": "package_installed", "vars": {"pkgname": "openssh"}},
            },
            allow_unicode=True,
        )
    )
    get_ssg_modules().yaml.open_and_expand.side_effect = lambda path, substitutions: yaml.safe_load(
        Path(path).read_text()
    )
    (root / "products" / "rhel9" / "profiles" / "test.profile").write_text(
        f"title: Test profile\ndescription: Protocol fixture\nselections:\n  - {RULE}\n"
    )
    template = root / "shared" / "templates" / "package_installed"
    template.mkdir()
    (template / "template.yml").write_text("supported_languages:\n  - bash\n  - oval\n")
    (root / "controls" / "test.yml").write_text(
        "id: test\ntitle: Test policy\ncontrols:\n"
        f"  - id: R1\n    title: SSH access\n    rules: [{RULE}]\n    status: automated\n"
        "  - id: R2\n    title: Manual review\n    rules: []\n    status: pending\n"
    )
    (root / "policy.md").write_text(f"# Policy\n\n## R1\n\n{TITLE}\n")
    built = root / "build" / "rhel9" / "rules"
    built.mkdir(parents=True)
    (built / f"{RULE}.json").write_text(json.dumps({"title": TITLE, "description": "SSH"}))
    (root / "build" / "ssg-rhel9-ds.xml").write_text(
        '<Benchmark xmlns="http://checklists.nist.gov/xccdf/1.2">'
        '<Profile id="test"/><Rule id="test"/></Benchmark>'
    )
    return root


@pytest.fixture
def mcp_session(protocol_repo):
    server = ContentAgentServer()
    return create_connected_server_and_client_session(
        server.server, read_timeout_seconds=timedelta(seconds=5)
    )


def _json_content(result):
    assert not result.isError
    assert len(result.content) == 1
    assert result.content[0].type == "text"
    text = result.content[0].text
    # Some existing tools put a readable summary before the JSON payload.
    start = re.search(r"^[\[{]", text, re.MULTILINE)
    assert start is not None, text
    return json.loads(text[start.start() :])


@pytest.mark.parametrize(
    "uri",
    [
        "cac://products",
        "cac://products/rhel9",
        "cac://rules",
        f"cac://rules/{RULE}",
        "cac://templates",
        "cac://templates/package_installed",
        "cac://profiles",
        "cac://profiles/rhel9/test",
        "cac://controls",
        "cac://build",
        "cac://build/rhel9",
        f"cac://build/rhel9/rules/{RULE}",
    ],
)
async def test_resource_content_is_json(mcp_session, uri):
    async with mcp_session as mcp_session:
        result = await mcp_session.read_resource(uri)
        assert len(result.contents) == 1
        content = result.contents[0]
        assert str(content.uri) == uri
        assert content.mimeType == "application/json"
        data = json.loads(content.text)
        assert data
        if uri == f"cac://rules/{RULE}":
            assert data["title"] == TITLE
            datetime.fromisoformat(data["last_modified"])
        if uri == "cac://build/rhel9":
            assert data["exists"]
            datetime.fromisoformat(data["build_time"])
            assert data["rules_count"] == data["profiles_count"] == 1


async def test_resource_discovery_separates_templates(mcp_session):
    async with mcp_session as mcp_session:
        listing = await mcp_session.list_resources()
        assert listing.nextCursor is None
        uris = [str(resource.uri) for resource in listing.resources]
        assert len(uris) == len(set(uris))
        assert all("{" not in uri and "%7B" not in uri for uri in uris)
        assert set(uris) == {
            "cac://products",
            "cac://rules",
            "cac://templates",
            "cac://profiles",
            "cac://controls",
            "cac://build",
        }
        templates = await mcp_session.list_resource_templates()
        assert {template.uriTemplate for template in templates.resourceTemplates} == {
            "cac://products/{product_id}",
            "cac://rules/{rule_id}",
            "cac://templates/{template_name}",
            "cac://profiles/{product}/{profile_id}",
            "cac://build/{product}",
            "cac://build/{product}/rules/{rule_id}",
        }
        for descriptor in [*listing.resources, *templates.resourceTemplates]:
            assert descriptor.mimeType == "application/json"


@pytest.mark.parametrize(
    "uri, message",
    [
        ("https://products", "Invalid URI scheme"),
        ("cac://unknown", "Unknown resource type"),
        ("cac://products/missing", "Product not found"),
        ("cac://rules/missing", "Rule not found"),
        ("cac://templates/missing", "Template not found"),
        ("cac://profiles/rhel9/missing", "Profile not found"),
        ("cac://products/rhel9/extra", "Invalid products resource path"),
        (f"cac://build/rhel9/rules/{RULE}/extra", "Invalid build resource path"),
    ],
)
async def test_resource_errors_leave_session_usable(mcp_session, uri, message):
    async with mcp_session as mcp_session:
        with pytest.raises(McpError, match=message) as error:
            await mcp_session.read_resource(uri)
        expected_code = -32002 if "not found" in message else -32602
        assert error.value.error.code == expected_code
        if expected_code == -32002:
            assert error.value.error.data == {"uri": uri}
        await mcp_session.send_ping()
        assert (
            _json_content(await mcp_session.call_tool("list_products", {}))[0]["product_id"]
            == "rhel9"
        )


async def test_resource_parse_failure_uses_internal_error(mcp_session, protocol_repo):
    product = protocol_repo / "products" / "broken"
    product.mkdir()
    (product / "product.yml").write_text("product: [\n")
    async with mcp_session as mcp_session:
        with pytest.raises(McpError) as error:
            await mcp_session.read_resource("cac://products/broken")
        assert error.value.error.code == -32603
        await mcp_session.send_ping()


@pytest.mark.parametrize(
    "name, arguments, message",
    [
        ("get_product_details", {}, "required property"),
        ("get_product_details", {"product_id": 42}, "not of type"),
        ("search_rules", {"limit": "three"}, "not of type"),
        ("search_rules", {"severity": "critical"}, "not one of"),
        ("get_rule_details", {"rule_id": RULE, "rendered_detail": "invalid"}, "not one of"),
        ("unknown_tool", {}, "Unknown tool"),
        ("get_product_details", {"product_id": "missing"}, "Product not found"),
        ("get_rule_details", {"rule_id": "missing"}, "Rule not found"),
        ("get_template_schema", {"template_name": "missing"}, "Template not found"),
        ("get_profile_details", {"product": "rhel9", "profile_id": "missing"}, "Profile not found"),
        ("get_control_details", {"control_id": "missing"}, "Control not found"),
        ("get_control_stats", {"control_id": "missing"}, "Control not found"),
        ("list_unmapped_requirements", {"control_id": "missing"}, "Control not found"),
        ("get_rule_product_availability", {"rule_id": "missing"}, "Rule not found"),
        (
            "get_requirement_file_path",
            {"control_id": "missing", "requirement_id": "R1"},
            "not found",
        ),
        (
            "get_rendered_rule",
            {"product": "rhel9", "rule_id": "missing"},
            "Rendered rule not found",
        ),
    ],
)
async def test_tool_errors_are_flagged(mcp_session, name, arguments, message):
    async with mcp_session as mcp_session:
        result = await mcp_session.call_tool(name, arguments)
        assert result.isError
        assert message in result.content[0].text
        await mcp_session.send_ping()
        assert not (await mcp_session.call_tool("list_products", {})).isError


async def test_execution_failure_is_flagged(mcp_session, protocol_repo):
    async with mcp_session as mcp_session:
        product = protocol_repo / "products" / "broken"
        product.mkdir()
        (product / "product.yml").write_text("product: [\n")
        result = await mcp_session.call_tool("get_product_details", {"product_id": "broken"})
        assert result.isError
        assert "Tool execution failed" in result.content[0].text
        await mcp_session.send_ping()


async def test_partial_discovery_warning_is_not_a_tool_error(mcp_session, protocol_repo):
    product = protocol_repo / "products" / "broken"
    product.mkdir()
    (product / "product.yml").write_text("product: [\n")
    async with mcp_session as mcp_session:
        result = await mcp_session.call_tool("list_products", {})
        assert not result.isError
        assert "WARNING:" in result.content[0].text
        assert _json_content(result)[0]["product_id"] == "rhel9"
