#!/usr/bin/env python3
"""
Debug script to test MCP server initialization.
"""

import asyncio
import json
import logging
from typing import Any, List

import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create a server instance
server = Server("mcp-json-analysis")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools."""
    return [
        types.Tool(
            name="test_tool",
            description="A simple test tool",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Test message"
                    }
                },
                "required": ["message"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent]:
    """Handle tool calls."""
    if name == "test_tool":
        message = arguments.get("message", "No message") if arguments else "No message"
        return [types.TextContent(type="text", text=f"Test response: {message}")]
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    """Main entry point for the server."""
    logger.info("Starting server initialization...")
    
    # Test capabilities first
    try:
        capabilities = server.get_capabilities(
            notification_options=NotificationOptions(),
            experimental_capabilities={},
        )
        logger.info(f"Capabilities: {capabilities}")
    except Exception as e:
        logger.error(f"Error getting capabilities: {e}")
        return
    
    # Test InitializationOptions
    try:
        init_options = InitializationOptions(
            server_name="mcp-json-analysis",
            server_version="1.0.0",
            capabilities=capabilities
        )
        logger.info(f"InitializationOptions created successfully: {init_options}")
    except Exception as e:
        logger.error(f"Error creating InitializationOptions: {e}")
        return
    
    # Run the server using stdin/stdout streams
    try:
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            logger.info("Starting server run...")
            await server.run(read_stream, write_stream, init_options)
    except Exception as e:
        logger.error(f"Error running server: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())