"""FastMCP server for Rundeck integration."""

import logging

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    TextContent,
    Tool,
    ToolAnnotations,
)

from .client import get_client_manager
from .tools import all_tools, read_tools, write_tools
from .utils import get_tool_description, load_tool_prompts

logger = logging.getLogger(__name__)


class RundeckMCPServer:
    """Rundeck MCP Server implementation."""

    def __init__(self, enable_write_tools: bool = False):
        """Initialize the server.

        Args:
            enable_write_tools: Whether to enable write operations
        """
        self.enable_write_tools = enable_write_tools
        self.tool_prompts = load_tool_prompts()
        self.server = Server("rundeck-mcp-server")

        # Register handlers
        self.server.list_tools = self._list_tools
        self.server.call_tool = self._call_tool

        logger.info(f"Rundeck MCP Server initialized (write tools: {enable_write_tools})")

    async def _list_tools(self, request: ListToolsRequest) -> list[Tool]:
        """List available tools."""
        tools = []

        # Always include read tools
        for tool_func in read_tools:
            tool_name = tool_func.__name__
            description = get_tool_description(tool_name, self.tool_prompts)

            tools.append(
                Tool(
                    name=tool_name,
                    description=description,
                    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True),
                )
            )

        # Include write tools if enabled
        if self.enable_write_tools:
            for tool_func in write_tools:
                tool_name = tool_func.__name__
                description = get_tool_description(tool_name, self.tool_prompts)

                # Determine if tool is destructive
                destructive_tools = [
                    "abort_execution",
                    "delete_execution",
                    "disable_job",
                    "disable_job_schedule",
                    "set_execution_mode",
                ]
                is_destructive = tool_name in destructive_tools

                tools.append(
                    Tool(
                        name=tool_name,
                        description=description,
                        annotations=ToolAnnotations(
                            readOnlyHint=False, destructiveHint=is_destructive, idempotentHint=not is_destructive
                        ),
                    )
                )

        logger.info(f"Listed {len(tools)} tools (write tools: {self.enable_write_tools})")
        return tools

    async def _call_tool(self, request: CallToolRequest) -> CallToolResult:
        """Call a tool."""
        tool_name = request.params.name
        arguments = request.params.arguments or {}

        logger.info(f"Calling tool: {tool_name}")

        # Find the tool function
        tool_func = None
        for func in all_tools:
            if func.__name__ == tool_name:
                tool_func = func
                break

        if tool_func is None:
            return CallToolResult(content=[TextContent(type="text", text=f"Unknown tool: {tool_name}")], isError=True)

        # Check if write tool is enabled
        if tool_func in write_tools and not self.enable_write_tools:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=(
                            f"Write tool '{tool_name}' is disabled. "
                            "Use --enable-write-tools to enable write operations."
                        ),
                    )
                ],
                isError=True,
            )

        try:
            # Call the tool function
            result = tool_func(**arguments)

            # Format the result
            if hasattr(result, "model_dump_json"):
                # Pydantic model
                content = result.model_dump_json(indent=2)
            elif hasattr(result, "json"):
                # Pydantic model (older version)
                content = result.json(indent=2)
            elif isinstance(result, dict | list):
                # Regular dict/list
                import json

                content = json.dumps(result, indent=2, default=str)
            else:
                # String or other
                content = str(result)

            return CallToolResult(content=[TextContent(type="text", text=content)])

        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error calling {tool_name}: {str(e)}")], isError=True
            )

    async def run(self):
        """Run the server."""
        import sys

        print("DEBUG: Starting Rundeck MCP Server...", file=sys.stderr)
        logger.info("Starting Rundeck MCP Server...")

        try:
            # Initialize client manager
            print("DEBUG: Initializing client manager...", file=sys.stderr)
            client_manager = get_client_manager()

            # Optional health check - don't let it block server startup
            try:
                print("DEBUG: Running health checks...", file=sys.stderr)
                health_status = client_manager.health_check_all()
                healthy_servers = [name for name, status in health_status.items() if status]

                if not healthy_servers:
                    logger.warning("No healthy Rundeck servers found during startup check")
                else:
                    logger.info(f"Connected to {len(healthy_servers)} healthy server(s): {', '.join(healthy_servers)}")
            except Exception as e:
                print(f"DEBUG: Health check error: {e}", file=sys.stderr)
                logger.warning(f"Health check failed during startup: {e}")
                logger.info("Server will start anyway - health checks will be performed on demand")

            # Run the server
            print("DEBUG: Starting MCP server with stdio...", file=sys.stderr)
            async with stdio_server() as (read_stream, write_stream):
                print("DEBUG: Got stdio streams, starting server.run...", file=sys.stderr)
                await self.server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name="rundeck-mcp-server",
                        server_version="1.0.0",
                        capabilities=self.server.capabilities
                    ),
                )
        except Exception as e:
            print(f"DEBUG: Exception in server.run: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            raise


async def main(enable_write_tools: bool = False):
    """Main entry point for the server.

    Args:
        enable_write_tools: Whether to enable write operations
    """
    server = RundeckMCPServer(enable_write_tools=enable_write_tools)
    await server.run()
