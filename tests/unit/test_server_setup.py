"""Tests that the MCP server can be built with the installed MCP SDK."""

import json
from datetime import timedelta

import pytest
from mcp.shared.memory import create_connected_server_and_client_session


def test_server_registers_handlers():
    """Fails when the installed MCP SDK lacks the Server decorator API."""
    from content_agent.server.mcp_server import ContentAgentServer

    server = ContentAgentServer()
    assert server.server.name == "content_agent"


@pytest.mark.asyncio
async def test_resource_reads_through_mcp_session(initialized_content_repo):
    """Exercise URI conversion through the SDK, which passes AnyUrl to the handler."""
    from content_agent.server.mcp_server import ContentAgentServer

    server = ContentAgentServer()
    async with create_connected_server_and_client_session(
        server.server, read_timeout_seconds=timedelta(seconds=5)
    ) as client:
        products = await client.read_resource("cac://products")
        assert json.loads(products.contents[0].text)[0]["product_id"] == "rhel9"

        details = await client.read_resource("cac://products/rhel9")
        assert json.loads(details.contents[0].text)["product_id"] == "rhel9"
