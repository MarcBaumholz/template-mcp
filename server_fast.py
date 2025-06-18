#!/usr/bin/env python3
"""
Fast-loading MCP Server for Template with Schema Mapping and RAG Tools
Uses lazy imports to reduce startup time
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("template-mcp-fast")

# Initialize MCP server
mcp = FastMCP("Template MCP Server")

# Lazy import globals
_rag_tools = None
_mapping_tool = None

def get_rag_tools():
    """Lazy import RAG tools to speed up startup"""
    global _rag_tools
    if _rag_tools is None:
        from tools.rag_tools import (
            test_rag_system, list_rag_collections, upload_openapi_spec_to_rag,
            retrieve_from_rag, delete_rag_collection,
            analyze_fields_with_rag_and_llm, enhance_csv_with_rag
        )
        _rag_tools = {
            'test_rag_system': test_rag_system,
            'list_rag_collections': list_rag_collections,
            'upload_openapi_spec_to_rag': upload_openapi_spec_to_rag,
            'retrieve_from_rag': retrieve_from_rag,
            'delete_rag_collection': delete_rag_collection,
            'analyze_fields_with_rag_and_llm': analyze_fields_with_rag_and_llm,
            'enhance_csv_with_rag': enhance_csv_with_rag
        }
    return _rag_tools

def get_mapping_tool():
    """Lazy import mapping tool to speed up startup"""
    global _mapping_tool
    if _mapping_tool is None:
        from tools.mapping import SchemaMappingTool
        _mapping_tool = SchemaMappingTool()
    return _mapping_tool

# Basic JSON tools (fast loading)
@mcp.tool()
def analyze_json_structure(json_data: str) -> str:
    """Analyze the structure of a JSON object and return detailed schema information"""
    try:
        data = json.loads(json_data)
        
        def analyze_value(value, path="root"):
            if isinstance(value, dict):
                result = {"type": "object", "path": path, "properties": {}}
                for key, val in value.items():
                    result["properties"][key] = analyze_value(val, f"{path}.{key}")
                return result
            elif isinstance(value, list):
                if value:
                    return {"type": "array", "path": path, "items": analyze_value(value[0], f"{path}[0]")}
                else:
                    return {"type": "array", "path": path, "items": {"type": "unknown"}}
            else:
                return {"type": type(value).__name__, "path": path, "value": str(value)[:100]}
        
        analysis = analyze_value(data)
        return json.dumps(analysis, indent=2)
    except Exception as e:
        return f"Error analyzing JSON: {str(e)}"

@mcp.tool()
def extract_json_fields(json_data: str, field_paths: List[str]) -> str:
    """Extract specific fields from a JSON object using dot notation paths"""
    try:
        data = json.loads(json_data)
        results = {}
        
        for path in field_paths:
            try:
                current = data
                for part in path.split('.'):
                    if '[' in part and ']' in part:
                        key, index = part.split('[')
                        index = int(index.rstrip(']'))
                        current = current[key][index]
                    else:
                        current = current[part]
                results[path] = current
            except (KeyError, IndexError, TypeError) as e:
                results[path] = f"Error: {str(e)}"
        
        return json.dumps(results, indent=2)
    except Exception as e:
        return f"Error extracting fields: {str(e)}"

@mcp.tool()
def flatten_json(json_data: str) -> str:
    """Flatten a nested JSON object into a flat structure with dot notation keys"""
    try:
        data = json.loads(json_data)
        
        def flatten_dict(d, parent_key='', sep='.'):
            items = []
            for k, v in d.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                if isinstance(v, dict):
                    items.extend(flatten_dict(v, new_key, sep=sep).items())
                elif isinstance(v, list):
                    for i, item in enumerate(v):
                        if isinstance(item, dict):
                            items.extend(flatten_dict(item, f"{new_key}[{i}]", sep=sep).items())
                        else:
                            items.append((f"{new_key}[{i}]", item))
                else:
                    items.append((new_key, v))
            return dict(items)
        
        flattened = flatten_dict(data)
        return json.dumps(flattened, indent=2)
    except Exception as e:
        return f"Error flattening JSON: {str(e)}"

# RAG Tools (lazy loaded)
@mcp.tool()
def test_rag_system() -> str:
    """Test RAG system and LLM connectivity"""
    tools = get_rag_tools()
    return tools['test_rag_system']()

@mcp.tool()
def list_available_api_specs() -> str:
    """List all available API specification collections in the RAG system"""
    tools = get_rag_tools()
    return tools['list_rag_collections']()

@mcp.tool()
def upload_api_specification(openapi_file_path: str, collection_name: str, metadata: Optional[Dict[str, Any]] = None) -> str:
    """Upload a new OpenAPI specification file (.yml or .json) to the RAG system for analysis"""
    tools = get_rag_tools()
    return tools['upload_openapi_spec_to_rag'](openapi_file_path, collection_name, metadata)

@mcp.tool()
def query_api_specification(query: str, collection_name: str, limit: int = 5, score_threshold: float = 0.5) -> str:
    """Perform a direct query against a specified API collection to retrieve raw documentation snippets"""
    tools = get_rag_tools()
    return tools['retrieve_from_rag'](query, collection_name, limit, score_threshold)

@mcp.tool()
def delete_api_specification(collection_name: str) -> str:
    """Delete an entire API specification collection from the RAG system"""
    tools = get_rag_tools()
    return tools['delete_rag_collection'](collection_name)

@mcp.tool()
def analyze_api_fields(
    fields_to_analyze: List[str], 
    collection_name: str = "flip_api_v2", 
    context_topic: Optional[str] = None,
    current_path: Optional[str] = None
) -> str:
    """Analyze a list of fields against an API spec using LLM to synthesize findings. Optional current_path for more accurate results"""
    tools = get_rag_tools()
    return tools['analyze_fields_with_rag_and_llm'](fields_to_analyze, collection_name, context_topic, current_path)

@mcp.tool()
def enhance_csv_with_rag(csv_file_path: str, collection_name: str, context_query: str, output_dir: Optional[str] = None) -> str:
    """Enhance a CSV file by using RAG system to find relevant context and LLM to generate business insights"""
    tools = get_rag_tools()
    return tools['enhance_csv_with_rag'](csv_file_path, collection_name, context_query, output_dir)

# Schema Mapping Tool (lazy loaded)
@mcp.tool()
async def intelligent_schema_mapping(
    source_json_path: str,
    target_collection_name: str,
    mapping_context: str,
    source_analysis_md_path: Optional[str] = None,
    max_matches_per_field: int = 3,
    output_path: Optional[str] = None
) -> str:
    """
    Intelligent schema mapping using multi-agent AI system with RAG-based target field discovery.
    
    This tool performs cognitive pattern matching between source fields and target API fields,
    using multiple AI agents to provide comprehensive analysis and mapping recommendations.
    """
    try:
        from tools.mapping_models import SchemaMappingRequest
        
        # Create request object
        request = SchemaMappingRequest(
            source_json_path=source_json_path,
            source_analysis_md_path=source_analysis_md_path,
            target_collection_name=target_collection_name,
            mapping_context=mapping_context,
            max_matches_per_field=max_matches_per_field,
            output_path=output_path or "schema_mapping_report.md"
        )
        
        # Get mapping tool and run analysis
        mapping_tool = get_mapping_tool()
        report = await mapping_tool.map_schema(request)
        
        # Generate markdown report
        from tools.report_generator import ReportGenerator
        generator = ReportGenerator()
        markdown_content = generator.generate_markdown_report(report)
        
        # Save report if output path specified
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            return f"Schema mapping completed successfully. Report saved to: {output_path}"
        else:
            return markdown_content
            
    except Exception as e:
        logger.error(f"Schema mapping failed: {e}")
        return f"Schema mapping failed: {str(e)}"

if __name__ == "__main__":
    logger.info("Starting Template MCP Server (Fast Loading)...")
    mcp.run() 