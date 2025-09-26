#!/usr/bin/env python3
"""Alternative MCP server implementation using direct stdio approach."""

import asyncio
import logging
import sys
from typing import Any

from mcp.server import Server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    TextContent,
    Tool,
    ToolAnnotations,
)

from .client import get_client_manager
from .tools import read_tools, write_tools
from .utils import get_tool_description, load_tool_prompts

logger = logging.getLogger(__name__)


def create_server(enable_write_tools: bool = False) -> Server:
    """Create and configure the MCP server."""
    server = Server("rundeck-mcp-server")
    tool_prompts = load_tool_prompts()

    @server.list_tools()
    async def handle_list_tools() -> list[Tool]:
        """Handle the list_tools request."""
        tools = []

        # Always include read tools
        for tool_func in read_tools:
            tool_name = tool_func.__name__
            description = get_tool_description(tool_name, tool_prompts)
            tools.append(
                Tool(
                    name=tool_name,
                    description=description,
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    },
                    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True),
                )
            )

        # Include write tools if enabled
        if enable_write_tools:
            for tool_func in write_tools:
                tool_name = tool_func.__name__
                description = get_tool_description(tool_name, tool_prompts)

                # Determine if tool is destructive
                destructive_tools = [
                    "abort_execution",
                    "delete_execution",
                    "disable_job",
                    "disable_job_schedule",
                    "set_execution_mode",
                    "delete_job",
                ]
                is_destructive = tool_name in destructive_tools

                tools.append(
                    Tool(
                        name=tool_name,
                        description=description,
                        inputSchema={
                            "type": "object",
                            "properties": {},
                            "required": []
                        },
                        annotations=ToolAnnotations(
                            readOnlyHint=False,
                            destructiveHint=is_destructive,
                            idempotentHint=not is_destructive,
                        ),
                    )
                )

        return tools

    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict[str, Any] | None = None) -> list[TextContent]:
        """Handle tool execution requests."""
        print(f"DEBUG: Calling tool {name} with args {arguments}", file=sys.stderr)

        # Find the tool function
        all_available_tools = read_tools + (write_tools if enable_write_tools else [])
        tool_func = None

        for tool in all_available_tools:
            if tool.__name__ == name:
                tool_func = tool
                break

        if tool_func is None:
            available_tools = [t.__name__ for t in all_available_tools]
            raise ValueError(f"Unknown tool: {name}. Available tools: {available_tools}")

        try:
            # Execute the tool
            if arguments:
                result = tool_func(**arguments)
            else:
                result = tool_func()

            # Format the result
            if isinstance(result, str):
                content = result
            else:
                import json
                content = json.dumps(result, indent=2, default=str)

            return [TextContent(type="text", text=content)]

        except Exception as e:
            logger.error(f"Error executing tool {name}: {e}")
            return [TextContent(type="text", text=f"Error calling {name}: {str(e)}")]

    return server


async def main_simple(enable_write_tools: bool = False):
    """Simple main function using standard MCP patterns."""
    print("DEBUG: Creating simple server", file=sys.stderr)

    # Initialize client manager with health check
    try:
        client_manager = get_client_manager()
        health_status = client_manager.health_check_all()
        healthy_servers = [name for name, status in health_status.items() if status]
        print(f"DEBUG: Found {len(healthy_servers)} healthy servers", file=sys.stderr)
    except Exception as e:
        print(f"DEBUG: Health check failed: {e}", file=sys.stderr)

    # Create server
    server = create_server(enable_write_tools)
    print("DEBUG: Server created, running with stdio", file=sys.stderr)

    # Run with stdio
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read_stream, write_stream):
        print("DEBUG: Got streams, starting server", file=sys.stderr)
        await server.run(read_stream, write_stream, server.create_initialization_options())