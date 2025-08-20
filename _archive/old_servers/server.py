#!/usr/bin/env python3
"""
MCP JSON Analysis and RAG Server

A Model Context Protocol server that provides JSON analysis tools and RAG functionality.
"""

import asyncio
import json
import logging
from typing import Any, List
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, rely on system environment

import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio

# Import RAG tools
try:
    from tools.rag_tools import (
    upload_openapi_spec_to_rag,
    retrieve_from_rag,
        analyze_fields_with_rag_and_llm,
        list_rag_collections,
    delete_rag_collection,
        enhance_csv_with_rag,
        test_rag_system
    )
    from tools.field_enhancer import enhance_json_fields, enhance_json_fields_from_file
    from tools.llm_client import test_llm_connection
    # Import schema mapping components
    from tools.mapping import SchemaMappingTool
    from tools.mapping_models import SchemaMappingRequest
    from tools.report_generator import MarkdownReportGenerator
    RAG_AVAILABLE = True
except ImportError as e:
    RAG_AVAILABLE = False
    print(f"RAG tools not available: {e}")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a server instance
server = Server("mcp-json-rag-server")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List available tools.
    Each tool specifies its arguments using JSON schema validation.
    """
    tools = [
        # JSON Analysis Tools
        types.Tool(
            name="analyze_json_structure",
            description="Analyze the structure of a JSON object and return detailed schema information",
            inputSchema={
                "type": "object",
                "properties": {
                    "json_data": {
                        "type": "string",
                        "description": "JSON string to analyze",
                    }
                },
                "required": ["json_data"],
            },
        ),
        types.Tool(
            name="extract_json_fields",
            description="Extract specific fields from a JSON object using dot notation paths",
            inputSchema={
                "type": "object",
                "properties": {
                    "json_data": {
                        "type": "string",
                        "description": "JSON string to extract fields from",
                    },
                    "field_paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Array of dot notation paths to extract (e.g., ['user.name', 'user.email'])",
                    }
                },
                "required": ["json_data", "field_paths"],
            },
        ),
        types.Tool(
            name="flatten_json",
            description="Flatten a nested JSON object into a flat structure with dot notation keys",
            inputSchema={
                "type": "object",
                "properties": {
                    "json_data": {
                        "type": "string",
                        "description": "JSON string to flatten",
                    }
                },
                "required": ["json_data"],
            },
        ),
    ]
    
    # Add RAG tools if available
    if RAG_AVAILABLE:
        rag_tools = [
            types.Tool(
                name="test_rag_system",
                description="Test RAG system and LLM connectivity",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            ),
            types.Tool(
                name="list_available_api_specs",
                description="List all available API specification collections in the RAG system",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            ),
            types.Tool(
                name="upload_api_specification",
                description="Upload a new OpenAPI specification file (.yml or .json) to the RAG system for analysis",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "openapi_file_path": {
                            "type": "string",
                            "description": "Path to the OpenAPI specification file (.json or .yaml)",
                        },
                        "collection_name": {
                            "type": "string",
                            "description": "The name of the Qdrant collection to create/use",
                        },
                        "metadata": {
                            "type": "object",
                            "description": "Optional metadata to attach to all points",
                        }
                    },
                    "required": ["openapi_file_path", "collection_name"],
                },
            ),
            types.Tool(
                name="query_api_specification",
                description="Perform a direct query against a specified API collection to retrieve raw documentation snippets",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query",
                        },
                        "collection_name": {
                            "type": "string",
                            "description": "The collection to search in",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "The maximum number of results to return",
                            "default": 3,
                        },
                        "score_threshold": {
                            "type": "number",
                            "description": "The minimum score for a result to be considered relevant",
                            "default": 0.3,
                        }
                    },
                    "required": ["query", "collection_name"],
                },
            ),
            types.Tool(
                name="delete_api_specification",
                description="Delete an entire API specification collection from the RAG system",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "collection_name": {
                            "type": "string",
                            "description": "The name of the collection to delete",
                        }
                    },
                    "required": ["collection_name"],
                },
            ),
            types.Tool(
                name="analyze_fields_with_rag_and_llm",
                description="Analyze a list of fields against an API spec using LLM to synthesize findings. Optional context_topic for more accurate results",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "fields_to_analyze": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "A list of field names to analyze",
                        },
                        "collection_name": {
                            "type": "string",
                            "description": "The name of the Qdrant collection to search in",
                            "default": "flip_api_v2",
                        },
                        "context_topic": {
                            "type": "string",
                            "description": "An optional string describing the overall context, such as an event name or API endpoint",
                        }
                    },
                    "required": ["fields_to_analyze"],
                },
            ),
            types.Tool(
                name="enhance_json_fields",
                description="Enhance JSON field analysis data using RAG system with targeted queries and LLM analysis",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "input_json": {
                            "type": "string",
                            "description": "JSON string with field analysis data to enhance",
                        },
                        "database_name": {
                            "type": "string",
                            "description": "RAG collection name to query",
                            "default": "flip_openapi",
                        }
                    },
                    "required": ["input_json"],
                },
            ),
            types.Tool(
                name="enhance_csv_with_rag",
                description="Enhance a CSV file by using RAG system to find relevant context and LLM to generate business insights",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "csv_file_path": {
                            "type": "string",
                            "description": "Path to the CSV file to enhance",
                        },
                        "collection_name": {
                            "type": "string",
                            "description": "The Qdrant collection containing the OpenAPI spec embeddings",
                        },
                        "context_query": {
                            "type": "string",
                            "description": "A natural language query describing the business context of the data",
                        },
                        "output_dir": {
                            "type": "string",
                            "description": "Directory to save the enhanced files. Defaults to same as input",
                        }
                    },
                    "required": ["csv_file_path", "collection_name", "context_query"],
                },
            ),
        ]
        tools.extend(rag_tools)
    
    # Add Schema Mapping Tool
    schema_mapping_tool = types.Tool(
        name="intelligent_schema_mapping",
        description=(
            "Intelligent field mapping between APIs using AI agents and cognitive matching. "
            "Analyzes source JSON and Markdown files to find compatible target API fields "
            "with confidence scoring and detailed insights."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "source_json_path": {
                    "type": "string",
                    "description": "Path to the source JSON file (e.g., clean.json)",
                },
                "source_analysis_md_path": {
                    "type": "string", 
                    "description": "Path to the analysis Markdown file (e.g., analyze_api_fields.md)",
                },
                "target_collection_name": {
                    "type": "string",
                    "description": "Name of the target API collection in Qdrant vector database",
                },
                "mapping_context": {
                    "type": "string",
                    "description": "Context for mapping (e.g., 'HR platform integration', 'User data migration')",
                },
                "max_matches_per_field": {
                    "type": "integer",
                    "description": "Maximum number of matches to return per field (default: 3)",
                    "default": 3
                },
                "output_path": {
                    "type": "string",
                    "description": "Optional path to save the mapping report (Markdown format)",
                }
            },
            "required": ["source_json_path", "source_analysis_md_path", "target_collection_name", "mapping_context"],
        },
    )
    tools.append(schema_mapping_tool)
    
    return tools

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handle tool execution requests.
    Tools can modify server state and notify clients of changes.
    """
    if not arguments:
        arguments = {}

    try:
        # JSON Analysis Tools
        if name == "analyze_json_structure":
            json_data = arguments.get("json_data")
            if not json_data:
                raise ValueError("Missing json_data argument")
            
            result = analyze_structure(json_data)
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )
            ]
        
        elif name == "extract_json_fields":
            json_data = arguments.get("json_data")
            field_paths = arguments.get("field_paths")
            
            if not json_data:
                raise ValueError("Missing json_data argument")
            if not field_paths:
                raise ValueError("Missing field_paths argument")
            
            result = extract_fields(json_data, field_paths)
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )
            ]
        
        elif name == "flatten_json":
            json_data = arguments.get("json_data")
            if not json_data:
                raise ValueError("Missing json_data argument")
            
            result = flatten_object(json_data)
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )
            ]
        
        # RAG Tools
        elif name == "test_rag_system" and RAG_AVAILABLE:
            rag_result = test_rag_system()
            llm_result = test_llm_connection()
            result = f"RAG System Test:\n{rag_result}\n\nLLM Connection Test:\n{llm_result}"
            return [
                types.TextContent(
                    type="text",
                    text=result
                )
            ]
        
        elif name == "list_available_api_specs" and RAG_AVAILABLE:
            result = list_rag_collections()
            return [
                types.TextContent(
                    type="text",
                    text=result
                )
            ]
        
        elif name == "upload_api_specification" and RAG_AVAILABLE:
            openapi_file_path = arguments.get("openapi_file_path")
            collection_name = arguments.get("collection_name")
            metadata = arguments.get("metadata")
            
            if not openapi_file_path:
                raise ValueError("Missing openapi_file_path argument")
            if not collection_name:
                raise ValueError("Missing collection_name argument")
            
            result = upload_openapi_spec_to_rag(openapi_file_path, collection_name, metadata)
            return [
                types.TextContent(
                    type="text",
                    text=result
                )
            ]
        
        elif name == "query_api_specification" and RAG_AVAILABLE:
            query = arguments.get("query")
            collection_name = arguments.get("collection_name")
            limit = arguments.get("limit", 5)
            score_threshold = arguments.get("score_threshold", 0.5)
            
            if not query:
                raise ValueError("Missing query argument")
            if not collection_name:
                raise ValueError("Missing collection_name argument")
            
            results = retrieve_from_rag(query, collection_name, limit, score_threshold)
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(results, indent=2)
                )
            ]
        
        elif name == "delete_api_specification" and RAG_AVAILABLE:
            collection_name = arguments.get("collection_name")
            
            if not collection_name:
                raise ValueError("Missing collection_name argument")
            
            result = delete_rag_collection(collection_name)
            return [
                types.TextContent(
                    type="text",
                    text=result
                )
            ]
        
        elif name == "analyze_api_fields" and RAG_AVAILABLE:
            fields_to_analyze = arguments.get("fields_to_analyze")
            collection_name = arguments.get("collection_name", "flip_api_v2")
            context_topic = arguments.get("context_topic")
            
            if not fields_to_analyze:
                raise ValueError("Missing fields_to_analyze argument")
            
            result = analyze_fields_with_rag_and_llm(fields_to_analyze, collection_name, context_topic)
            return [
                types.TextContent(
                    type="text",
                    text=result
                )
            ]
        
        elif name == "enhance_json_fields" and RAG_AVAILABLE:
            input_json = arguments.get("input_json")
            database_name = arguments.get("database_name", "flip_openapi")
            
            if not input_json:
                raise ValueError("Missing input_json argument")
            
            result = enhance_json_fields(input_json, database_name)
            return [
                types.TextContent(
                    type="text",
                    text=result
                )
            ]
        
        elif name == "enhance_csv_with_rag" and RAG_AVAILABLE:
            csv_file_path = arguments.get("csv_file_path")
            collection_name = arguments.get("collection_name")
            context_query = arguments.get("context_query")
            output_dir = arguments.get("output_dir")
            
            if not csv_file_path:
                raise ValueError("Missing csv_file_path argument")
            if not collection_name:
                raise ValueError("Missing collection_name argument")
            if not context_query:
                raise ValueError("Missing context_query argument")
            
            result = enhance_csv_with_rag(csv_file_path, collection_name, context_query, output_dir)
            return [
                types.TextContent(
                    type="text",
                    text=result
                )
            ]
        
        # Schema Mapping Tool
        elif name == "intelligent_schema_mapping":
            if not RAG_AVAILABLE:
                return [
                    types.TextContent(
                        type="text",
                        text="❌ Schema mapping requires RAG tools to be available.\n\nRequired dependencies:\n- sentence-transformers\n- qdrant-client\n- PyYAML\n- pandas\n- openai\n\nRequired environment variable:\n- OPENROUTER_API_KEY (for OpenRouter API access)\n\nInstall with: pip install -r requirements.txt\nThen add your OpenRouter API key to .env file."
                    )
                ]
                
            source_json_path = arguments.get("source_json_path")
            source_analysis_md_path = arguments.get("source_analysis_md_path")
            target_collection_name = arguments.get("target_collection_name")
            mapping_context = arguments.get("mapping_context")
            max_matches_per_field = arguments.get("max_matches_per_field", 3)
            output_path = arguments.get("output_path")
            
            if not source_json_path:
                raise ValueError("Missing source_json_path argument")
            if not source_analysis_md_path:
                raise ValueError("Missing source_analysis_md_path argument")
            if not target_collection_name:
                raise ValueError("Missing target_collection_name argument")
            if not mapping_context:
                raise ValueError("Missing mapping_context argument")
            
            # Create schema mapping request
            request = SchemaMappingRequest(
                source_json_path=source_json_path,
                source_analysis_md_path=source_analysis_md_path,
                target_collection_name=target_collection_name,
                mapping_context=mapping_context,
                max_matches_per_field=max_matches_per_field
            )
            
            # Initialize the schema mapping tool
            mapping_tool = SchemaMappingTool()
            
            # Perform the mapping
            report = await mapping_tool.map_schema(request)
            
            # Generate Markdown report
            report_generator = MarkdownReportGenerator()
            markdown_content = report_generator.generate_report(report, output_path)
            
            return [
                types.TextContent(
                    type="text",
                    text=markdown_content
                )
            ]
        
        else:
            if not RAG_AVAILABLE and name in ["test_rag_system", "list_available_api_specs", "upload_api_specification", 
                                             "query_api_specification", "delete_api_specification", 
                                             "analyze_api_fields", "enhance_json_fields", "enhance_csv_with_rag"]:
                return [
                    types.TextContent(
                        type="text",
                        text="❌ RAG tools are not available.\n\nRequired dependencies:\n- sentence-transformers\n- qdrant-client\n- PyYAML\n- pandas\n- openai\n\nRequired environment variable:\n- OPENROUTER_API_KEY (for OpenRouter API access)\n\nInstall with: pip install -r requirements.txt\nThen add your OpenRouter API key to .env file."
                    )
                ]
            raise ValueError(f"Unknown tool: {name}")
    
    except Exception as e:
        logger.error(f"Error in tool {name}: {str(e)}")
        return [
            types.TextContent(
                type="text",
                text=f"Error: {str(e)}"
            )
        ]

# Helper functions for JSON operations
def analyze_structure(json_data: str) -> dict:
    """Analyze the structure of a JSON object."""
    try:
        data = json.loads(json_data)
        return {
            "type": type(data).__name__,
            "structure": _analyze_recursive(data),
            "total_keys": _count_keys(data) if isinstance(data, dict) else 0,
            "max_depth": _calculate_depth(data)
        }
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON: {str(e)}"}

def _analyze_recursive(obj: Any) -> Any:
    """Recursively analyze object structure."""
    if isinstance(obj, dict):
        return {key: _analyze_recursive(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        if obj:
            return [_analyze_recursive(obj[0])]  # Analyze first element as sample
        return []
    else:
        return type(obj).__name__

def _count_keys(obj: Any) -> int:
    """Count total keys in nested dict."""
    if isinstance(obj, dict):
        return len(obj) + sum(_count_keys(v) for v in obj.values())
    elif isinstance(obj, list):
        return sum(_count_keys(item) for item in obj)
    return 0

def _calculate_depth(obj: Any, current_depth: int = 0) -> int:
    """Calculate maximum depth of nested structure."""
    if isinstance(obj, dict):
        if not obj:
            return current_depth
        return max(_calculate_depth(v, current_depth + 1) for v in obj.values())
    elif isinstance(obj, list):
        if not obj:
            return current_depth
        return max(_calculate_depth(item, current_depth + 1) for item in obj)
    return current_depth

def extract_fields(json_data: str, field_paths: List[str]) -> dict:
    """Extract fields from JSON using dot notation paths."""
    try:
        data = json.loads(json_data)
        result = {}
        
        for path in field_paths:
            try:
                value = get_nested_value(data, path)
                result[path] = value
            except KeyError:
                result[path] = None
        
        return result
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON: {str(e)}"}

def get_nested_value(data: Any, path: str) -> Any:
    """Get nested value using dot notation path."""
    keys = path.split('.')
    current = data
    
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        elif isinstance(current, list) and key.isdigit():
            index = int(key)
            if 0 <= index < len(current):
                current = current[index]
            else:
                raise KeyError(f"Index {index} out of range")
        else:
            raise KeyError(f"Key '{key}' not found")
    
    return current

def flatten_object(json_data: str, separator: str = '.') -> dict:
    """Flatten a nested JSON object."""
    try:
        data = json.loads(json_data)
        
        def _flatten(obj: Any, parent_key: str = '') -> dict:
            items = []
            
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_key = f"{parent_key}{separator}{key}" if parent_key else key
                    items.extend(_flatten(value, new_key).items())
            elif isinstance(obj, list):
                for i, value in enumerate(obj):
                    new_key = f"{parent_key}{separator}{i}" if parent_key else str(i)
                    items.extend(_flatten(value, new_key).items())
            else:
                return {parent_key: obj}
            
            return dict(items)
        
        return _flatten(data)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON: {str(e)}"}

async def main():
    """Main entry point for the server."""
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="mcp-json-rag-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())