#!/usr/bin/env python3
"""
Fast-loading MCP Server for Template with Schema Mapping and RAG Tools
Uses lazy imports to reduce startup time - SSE Transport Version
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastmcp import FastMCP

# Load environment variables
try:
    from dotenv import load_dotenv
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(script_dir, '.env')
    load_dotenv(env_path)
    # Use logging instead of print statements to avoid JSON parsing issues
    logger = logging.getLogger("template-mcp-sse")
    logger.debug(f"Loading .env from: {env_path}")
    logger.debug(f"OPENROUTER_API_KEY loaded: {'Yes' if os.getenv('OPENROUTER_API_KEY') else 'No'}")
except ImportError:
    pass  # dotenv not available, environment variables should be set manually

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("template-mcp-sse")

# Initialize MCP server
mcp = FastMCP("Template MCP Server - SSE")

# Global variables for lazy loading
_json_extraction_tool = None
_combined_json_tool = None
_rag_wrapper = None
_coding_tool = None
_api_spec_getter = None
_reasoning_agent = None

def get_json_extraction_tool():
    """Lazy import JSON extraction tool"""
    global _json_extraction_tool
    if _json_extraction_tool is None:
        from tools.json_tool.json_agent import FieldExtractionAgent
        _json_extraction_tool = FieldExtractionAgent()
    return _json_extraction_tool

def get_combined_json_tool():
    """Lazy import combined JSON analysis tool"""
    global _combined_json_tool
    if _combined_json_tool is None:
        from tools.json_tool.combined_analysis_agent import CombinedFieldAnalysisAgent
        _combined_json_tool = CombinedFieldAnalysisAgent()
    return _combined_json_tool

def get_coding_tool():
    """Lazy import coding tool"""
    global _coding_tool
    if _coding_tool is None:
        from tools.codingtool.biggerprompt import generate_enhanced_prompt
        _coding_tool = generate_enhanced_prompt
    return _coding_tool

def get_api_spec_getter():
    """Lazy import API spec getter"""
    global _api_spec_getter
    if _api_spec_getter is None:
        from tools.api_spec_getter import get_api_spec_with_direct_llm_query
        _api_spec_getter = get_api_spec_with_direct_llm_query
    return _api_spec_getter

def get_reasoning_agent():
    """Lazy import reasoning agent"""
    global _reasoning_agent
    if _reasoning_agent is None:
        from tools.reasoning_agent import reasoning_agent
        _reasoning_agent = reasoning_agent
    return _reasoning_agent

# RAG Tools (lazy loaded)
@mcp.tool()
def test_rag_system() -> str:
    """Test RAG system and LLM connectivity"""
    from tools.rag_tools import test_rag_system as test_rag
    return test_rag()

@mcp.tool()
def list_available_api_specs() -> str:
    """List all available API specification collections in the RAG system"""
    from tools.rag_tools import list_rag_collections
    return list_rag_collections()

@mcp.tool()
def upload_api_specification(openapi_file_path: str, collection_name: str, metadata: Optional[Dict[str, Any]] = None) -> str:
    """Upload a new OpenAPI specification file (.yml or .json) to the RAG system for analysis"""
    from tools.rag_tools import upload_openapi_spec_to_rag
    return upload_openapi_spec_to_rag(openapi_file_path, collection_name, metadata)

@mcp.tool()
def query_api_specification(
    query: str, 
    collection_name: str, 
    limit: int = 5, 
    score_threshold: float = 0.5,
    current_path: str = ""
) -> str:
    """Perform a direct query against a specified API collection to retrieve raw documentation snippets and save results as markdown"""
    from tools.rag_tools import retrieve_from_rag
    
    # Convert empty string to None for backward compatibility
    current_path_arg = current_path if current_path else None
    
    return retrieve_from_rag(query, collection_name, limit, score_threshold, current_path_arg)

@mcp.tool()
def delete_api_specification(collection_name: str) -> str:
    """Delete an entire API specification collection from the RAG system"""
    from tools.rag_tools import delete_rag_collection
    return delete_rag_collection(collection_name)

@mcp.tool()
def enhanced_rag_analysis(
    fields_to_analyze: List[str], 
    collection_name: str = "flip_api_v2", 
    context_topic: str = "",
    current_path: str = ""
) -> str:
    """
    🚀 ENHANCED RAG Analysis with Optimized Semantic Matching
    
    This tool uses the optimized RAG system with:
    - Token-aware chunking with tiktoken
    - Semantic property grouping
    - Multi-stage query processing
    - Enhanced re-ranking with semantic weights
    - Hierarchical filtering for balanced results
    
    Args:
        fields_to_analyze: List of fields to analyze semantically
        collection_name: RAG collection name (default: "flip_api_v2")
        context_topic: Optional business context for analysis
        current_path: Directory to save enhanced analysis results
    
    Returns:
        Comprehensive semantic analysis with enhanced context and mapping recommendations
    """
    try:
        from tools.rag_tools import analyze_fields_with_rag_and_llm as enhanced_analyze
    
        # Convert empty strings to None for backward compatibility
        context_topic_arg = context_topic if context_topic else None
        current_path_arg = current_path if current_path else None
    
        return enhanced_analyze(fields_to_analyze, collection_name, context_topic_arg, current_path_arg)
        
    except Exception as e:
        logger.error(f"Enhanced RAG analysis failed: {e}")
        return f"❌ Enhanced RAG analysis failed: {str(e)}"

# Enhanced Reasoning Agent with Integrated Proof Tool (lazy loaded) - ACTIVE
@mcp.tool()
async def reasoning_agent(
    source_analysis_path: str,
    api_spec_path: str,
    output_directory: str,
    target_collection_name: str = ""
) -> str:
    """
    Orchestrates the entire schema mapping process from a high-level goal with integrated proof tool functionality.
    
    This enhanced agent combines mapping analysis with verification and creative solutions:
    1. Decides whether to use direct analysis or a RAG-based approach
    2. Executes the necessary mapping tools
    3. Identifies unmapped fields automatically
    4. Generates creative solutions for unmapped fields using RAG search
    5. Provides comprehensive verification checklist and implementation guide
    6. Returns a final comprehensive report with actionable next steps
    
    Args:
        source_analysis_path: Path to the markdown file with source field analysis
        api_spec_path: Path to the target OpenAPI specification (.json or .yml)
        output_directory: The directory where the final report should be saved
        target_collection_name: Optional RAG collection name (auto-generated if empty)
    
    Returns:
        Path to the comprehensive report file with mapping analysis, verification, and creative solutions
    """
    try:
        reasoning_tool = get_reasoning_agent()
        result = await reasoning_tool(
            source_analysis_path=source_analysis_path,
            api_spec_path=api_spec_path,
            output_directory=output_directory,
            target_collection_name=target_collection_name if target_collection_name else None
        )
        return result
    except Exception as e:
        logger.error(f"Enhanced reasoning agent failed: {e}")
        return f"❌ Enhanced reasoning agent failed: {str(e)}"

# Combined JSON Analysis Tool (lazy loaded) - ACTIVE
@mcp.tool()
async def analyze_json_fields_with_rag(
    webhook_json_path: str = "",
    current_directory: str = "",
    collection_name: str = "flip_api_v2"
) -> str:
    """
    Combined JSON field extraction and RAG analysis in a single tool.
    
    This tool combines step 2 (JSON field extraction) and step 3 (RAG analysis)
    in a single LangGraph workflow. It systematically extracts all relevant
    JSON fields and analyzes them directly with the Flip API specification.
    
    Args:
        webhook_json_path: Path to the JSON file for analysis
        current_directory: Directory to save results (optional)
        collection_name: Name of the RAG collection (default: "flip_api_v2")
    
    Returns:
        Comprehensive analysis report with field extraction and RAG-based evaluation
    """
    try:
        # Load JSON file
        if not os.path.exists(webhook_json_path):
            return f"❌ Error: JSON file not found at path: {webhook_json_path}"
        
        with open(webhook_json_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        # Load combined analysis tool
        combined_agent = get_combined_json_tool()
        
        # Execute combined analysis
        result = await combined_agent.process_json_with_combined_analysis(
            json_data=json_data,
            json_file_path=webhook_json_path,
            current_directory=current_directory,
            collection_name=collection_name
        )
        
        if result.status == "error":
            return f"❌ Combined JSON analysis failed: {result.error}"
        
        # Format the result
        report = f"""# 🔄 Combined JSON Field Extraction and RAG Analysis

## ✅ Processing Status: {result.status.upper()}
**Agent**: {result.agent_name}
**Processed At**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 Analysis Results
**Extracted Fields**: {len(result.result.extracted_fields)}
**Validation Status**: {result.result.validation_status}
**Confidence Score**: {result.result.confidence_score:.2f}/1.0

## 🔍 Extracted Fields
```
{', '.join(result.result.extracted_fields)}
```

## 🧠 Combined Analysis with RAG
{result.result.context}

## 📝 Processing Notes
{result.result.processing_notes}

## 📁 File Information
- **Analyzed JSON file**: `{webhook_json_path}`
- **Results saved in**: `{current_directory or 'Default directory'}`
- **RAG Collection**: `{collection_name}`

## 🔄 Next Steps
1. Review the extracted fields for completeness
2. Validate the RAG-based mapping recommendations
3. Implement the suggested field mappings
4. Test the mappings with sample data

---
*Analysis completed with CombinedFieldAnalysisAgent and LangGraph workflow*"""
        
        return report
        
    except json.JSONDecodeError as e:
        return f"❌ Invalid JSON format in file {webhook_json_path}: {str(e)}"
    except Exception as e:
        logger.error(f"Combined JSON analysis failed: {e}")
        return f"❌ Combined JSON analysis failed: {str(e)}"

@mcp.tool()
def get_direct_api_mapping_prompt(api_spec_path: str, analysis_md_path: str) -> str:
    """
    Alternative to RAG: Directly analyzes a smaller API spec to generate a mapping prompt.

    Use this when an API spec is small enough to fit in a context window. It reads
    the full spec and an analysis file to create a detailed prompt for an LLM to find
    direct and semantic field matches.

    Args:
        api_spec_path: The full path to the OpenAPI specification file.
        analysis_md_path: The full path to the markdown analysis file.

    Returns:
        A detailed prompt for an LLM or an error if the files are too large.
    """
    getter_tool = get_api_spec_getter()
    return getter_tool(api_spec_path, analysis_md_path)

@mcp.tool()
def generate_kotlin_mapping_code(mapping_report_path: str) -> str:
    """
    Generates a detailed prompt for Cursor to create Kotlin mapping code.

    This tool uses a mapping analysis report and a Kotlin template file to
    generate a rich prompt that instructs an LLM to write the final Kotlin
    code for the mapping, including handling for missing fields and data
    transformations.

    Args:
        mapping_report_path: Path to the markdown file containing the mapping analysis report.

    Returns:
        A detailed prompt to be used in Cursor for generating Kotlin code.
    """
    try:
        # Define path to the Kotlin template
        template_path = os.path.join(os.path.dirname(__file__), 'tools', 'codingtool', 'template.kt')

        # Read the mapping report
        if not os.path.exists(mapping_report_path):
            return f"❌ Error: Mapping report not found at '{mapping_report_path}'"
        with open(mapping_report_path, 'r', encoding='utf-8') as f:
            mapping_info = f.read()

        # Read the Kotlin template
        if not os.path.exists(template_path):
            return f"❌ Error: Kotlin template not found at '{template_path}'"
        with open(template_path, 'r', encoding='utf-8') as f:
            kotlin_template = f.read()

        # Get the coding tool (lazy loaded)
        prompt_generator = get_coding_tool()

        # Generate the prompt
        enhanced_prompt = prompt_generator(mapping_info, kotlin_template)
        return enhanced_prompt

    except Exception as e:
        logger.error(f"Failed to generate Kotlin mapping prompt: {e}")
        return f"❌ Failed to generate prompt: {str(e)}"

# Import the new iterative mapping tool
from tools.iterative_mapping import iterative_field_mapping

@mcp.tool()
def iterative_mapping_with_feedback(
    source_fields: str,
    target_collection: str,
    api_spec_path: str,
    output_path: str = ""
) -> str:
    """
    Perform iterative field mapping with feedback loop using ReAct pattern.

    Args:
        source_fields: Comma-separated list of source field names to map
        target_collection: RAG collection name for target API
        api_spec_path: Path to OpenAPI specification for live validation
        output_path: Optional path to save detailed results (default: current directory)

    Returns:
        Detailed mapping results with confidence scores and iteration history
    """
    try:
        fields_list = [field.strip() for field in source_fields.split(',') if field.strip()]
        if not fields_list:
            return "❌ No valid source fields provided"

        if not output_path:
            output_path = "./mapping_results"

        result = iterative_field_mapping(
            source_fields=fields_list,
            target_collection=target_collection,
            api_spec_path=api_spec_path,
            output_path=output_path
        )
        return result
    except Exception as e:
        return f"❌ Iterative mapping failed: {str(e)}"
if __name__ == "__main__":
    logger.info("🚀 Starting Template MCP Server with Optimized RAG Tools (SSE)...")
    logger.info("📡 Server will be available via SSE transport on port 8080")
    logger.info("🌐 Use ngrok to expose: ngrok http 8080")
    logger.info("🔧 Available tools:")
    logger.info("   • test_rag_system() - Test optimized RAG system")
    logger.info("   • upload_api_specification() - Upload with enhanced chunking")
    logger.info("   • query_api_specification() - Enhanced semantic search")
    logger.info("   • analyze_json_fields_with_rag() - Combined JSON analysis")
    logger.info("   • reasoning_agent() - Complete mapping orchestration")
    logger.info("   • enhanced_rag_analysis() - Enhanced RAG analysis")
    logger.info("   • get_direct_api_mapping_prompt() - Direct API analysis")
    logger.info("   • generate_kotlin_mapping_code() - Kotlin code generation")
    logger.info("   • iterative_mapping_with_feedback() - Iterative ReAct mapping")
    
    # Run with SSE transport for web compatibility
    mcp.run(transport="sse", port=8080)