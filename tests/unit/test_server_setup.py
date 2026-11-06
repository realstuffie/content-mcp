"""Tests that the MCP server can be built with the installed MCP SDK."""


def test_server_registers_handlers():
    """Fails when the installed MCP SDK lacks the Server decorator API."""
    from content_agent.server.mcp_server import ContentAgentServer

    server = ContentAgentServer()
    assert server.server.name == "content_agent"
