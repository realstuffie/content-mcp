"""MCP server implementation."""

import logging
from typing import Any

from mcp.server import Server
from mcp.server.lowlevel.helper_types import ReadResourceContents
from mcp.server.stdio import stdio_server
from mcp.types import Resource, ResourceTemplate, Tool
from pydantic import AnyUrl

from content_agent.server.handlers import prompts, resources, tools

logger = logging.getLogger(__name__)


class ContentAgentServer:
    """MCP server for ComplianceAsCode/content."""

    def __init__(self) -> None:
        """Initialize MCP server."""
        self.server = Server("content_agent")
        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Set up MCP protocol handlers."""

        # List resources handler
        @self.server.list_resources()
        async def handle_list_resources() -> list[Resource]:
            """Handle list resources request."""
            logger.debug("Listing resources")
            resource_list = resources.list_resources()
            return [
                Resource(
                    uri=r["uri"],
                    name=r["name"],
                    description=r.get("description"),
                    mimeType=r.get("mimeType"),
                )
                for r in resource_list
            ]

        @self.server.list_resource_templates()
        async def handle_list_resource_templates() -> list[ResourceTemplate]:
            """Advertise parameterized URIs as templates, not concrete resources."""
            return [ResourceTemplate(**r) for r in resources.list_resource_templates()]

        # Read resource handler
        @self.server.read_resource()
        async def handle_read_resource(uri: AnyUrl) -> list[ReadResourceContents]:
            """Handle read resource request."""
            logger.debug(f"Reading resource: {uri}")
            content = await resources.handle_resource_read(str(uri))
            return [ReadResourceContents(content=content, mime_type="application/json")]

        # List tools handler
        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """Handle list tools request."""
            logger.debug("Listing tools")
            tool_list = tools.list_tools()
            return [
                Tool(
                    name=t["name"],
                    description=t["description"],
                    inputSchema=t["inputSchema"],
                )
                for t in tool_list
            ]

        # Call tool handler
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[Any]:
            """Handle call tool request."""
            logger.debug(f"Calling tool: {name}")
            return await tools.handle_tool_call(name, arguments)

        # List prompts handler
        @self.server.list_prompts()
        async def handle_list_prompts() -> list[Any]:
            """Handle list prompts request."""
            logger.debug("Listing prompts")
            return prompts.list_prompts()

        # Get prompt handler
        @self.server.get_prompt()
        async def handle_get_prompt(name: str, arguments: dict[str, Any]) -> Any:
            """Handle get prompt request."""
            logger.debug(f"Getting prompt: {name}")
            return await prompts.handle_prompt_get(name, arguments)

    async def run_stdio(self) -> None:
        """Run server with stdio transport."""
        logger.info("Starting MCP server with stdio transport")
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options(),
            )


async def run_stdio_server() -> None:
    """Run the MCP server with stdio transport.

    This is the main entry point for stdio mode.
    """
    server = ContentAgentServer()
    await server.run_stdio()
