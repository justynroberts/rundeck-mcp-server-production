#!/usr/bin/env python3
"""Final working Rundeck MCP server implementation"""

import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool

from .tools import read_tools, write_tools
from .utils import generate_input_schema, get_tool_description, load_tool_prompts

async def main_final(enable_write_tools: bool = False):
    """Final working MCP server implementation."""
    server = Server("rundeck-mcp-server")
    tool_prompts = load_tool_prompts()

    # Define tools handler with exact working pattern
    @server.list_tools()
    async def handle_list_tools():
        """List available tools - exact working pattern"""
        tools = []

        # Add read tools
        for tool_func in read_tools:
            tool_name = tool_func.__name__
            description = get_tool_description(tool_name, tool_prompts)
            input_schema = generate_input_schema(tool_func)

            tools.append(Tool(
                name=tool_name,
                description=description,
                inputSchema=input_schema
            ))

        # Add write tools if enabled
        if enable_write_tools:
            for tool_func in write_tools:
                tool_name = tool_func.__name__
                description = get_tool_description(tool_name, tool_prompts)
                input_schema = generate_input_schema(tool_func)

                tools.append(Tool(
                    name=tool_name,
                    description=description,
                    inputSchema=input_schema
                ))

        return tools

    # Define call handler with exact working pattern
    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict = None):
        """Call a tool - exact working pattern"""
        # Find the tool function
        all_tools = read_tools + (write_tools if enable_write_tools else [])
        tool_func = None

        for tool in all_tools:
            if tool.__name__ == name:
                tool_func = tool
                break

        if tool_func is None:
            return [{"type": "text", "text": f"❌ Unknown tool: {name}"}]

        # Check if write tool is enabled
        if tool_func in write_tools and not enable_write_tools:
            return [{"type": "text", "text": f"❌ Write tool '{name}' is disabled. Use --enable-write-tools to enable write operations."}]

        try:
            # Call the tool function
            if arguments:
                result = tool_func(**arguments)
            else:
                result = tool_func()

            # Handle the result
            if hasattr(result, 'content'):
                content = result.content
            elif isinstance(result, str):
                content = result
            else:
                content = str(result)

            return [{"type": "text", "text": content}]

        except Exception as e:
            return [{"type": "text", "text": f"❌ Error calling {name}: {str(e)}"}]

    # Start server with exact working pattern
    async with stdio_server() as streams:
        await server.run(*streams, server.create_initialization_options())