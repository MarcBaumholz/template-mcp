#!/usr/bin/env python3
"""
MCP HR API Mapping Server - SSE Transport
A FastMCP server for HR API field mapping and analysis with simplified tools.
"""

import os
import json
import logging
import asyncio
from typing import Optional, Dict, Any
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import FastMCP
try:
    from fastmcp import FastMCP
except ImportError:
    print("❌ FastMCP not available. Install with: pip install fastmcp")
    exit(1)

# Import our simplified tools
try:
    from tools.rag_tools import (
        upload_openapi_spec_to_rag,
        retrieve_from_rag,
        analyze_fields_with_rag_and_llm,
        list_rag_collections,
        delete_rag_collection,
        test_rag_system
    )
    from tools.reasoning_agent import reasoning_agent
    from tools.api_spec_getter import get_api_spec_with_direct_llm_query
    from tools.llm_client import test_llm_connection
    from tools.json_tool.combined_analysis_agent import CombinedFieldAnalysisAgent
    from tools.codingtool.biggerprompt import generate_enhanced_prompt
    TOOLS_AVAILABLE = True
except ImportError as e:
    TOOLS_AVAILABLE = False
    print(f"❌ Tools not available: {e}")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastMCP server instance
mcp = FastMCP(
    name="HR-API-Mapping-Server",
    instructions="""
    A comprehensive HR API mapping server that provides tools for:
    - JSON field analysis and extraction
    - RAG-based API specification analysis
    - Intelligent field mapping with proof tool integration
    - Kotlin code generation for mappings
    
    Use these tools to map HR data fields to target API specifications efficiently.
    """
)

# Global instances for lazy loading
_combined_json_tool = None
_kotlin_template_content = None

def get_combined_json_tool():
    """Get or create combined JSON analysis tool."""
    global _combined_json_tool
    if _combined_json_tool is None:
        _combined_json_tool = CombinedFieldAnalysisAgent()
    return _combined_json_tool

def get_kotlin_template():
    """Get Kotlin template content."""
    global _kotlin_template_content
    if _kotlin_template_content is None:
        template_path = Path(__file__).parent / "tools" / "codingtool" / "template.kt"
        if template_path.exists():
            _kotlin_template_content = template_path.read_text(encoding='utf-8')
        else:
            _kotlin_template_content = "// Kotlin template not found - provide template content manually"
    return _kotlin_template_content

# ============================================================================
# CORE WORKFLOW TOOLS (3 tools for complete HR API mapping)
# ============================================================================

@mcp.tool()
async def analyze_json_fields_with_rag(
    webhook_json_path: str = "",
    current_directory: str = "",
    collection_name: str = "flip_api_v2"
) -> str:
    """
    Combined JSON field extraction and RAG analysis in a single tool.
    
    This tool combines step 2 (JSON field extraction) and step 3 (RAG analysis)
    in a single workflow. It systematically extracts all relevant
    JSON fields and analyzes them directly with the API specification.
    
    Args:
        webhook_json_path: Path to the JSON file for analysis
        current_directory: Directory to save results (optional)
        collection_name: Name of the RAG collection (default: "flip_api_v2")
    
    Returns:
        Comprehensive analysis report with field extraction and RAG-based evaluation
    """
    if not TOOLS_AVAILABLE:
        return "❌ Tools not available. Check dependencies."
    
    try:
        # Load JSON data
        if not webhook_json_path or not Path(webhook_json_path).exists():
            return f"❌ JSON file not found: {webhook_json_path}"
        
        with open(webhook_json_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        # Use combined analysis agent
        agent = get_combined_json_tool()
        result = await agent.process_json_with_combined_analysis(
            json_data=json_data,
            json_file_path=webhook_json_path,
            current_directory=current_directory,
            collection_name=collection_name
        )
        
        if result.status == "completed":
            return f"✅ JSON Analysis completed successfully!\n\n{result.result.context}"
        else:
            return f"❌ JSON Analysis failed: {result.error}"
            
    except Exception as e:
        logger.error(f"JSON analysis failed: {e}")
        return f"❌ JSON extraction failed: {str(e)}"

@mcp.tool()
async def reasoning_agent_orchestrator(
    source_analysis_path: str,
    api_spec_path: str,
    output_directory: str,
    target_collection_name: str = ""
) -> str:
    """
    Orchestrates the entire schema mapping process from a high-level goal with integrated proof tool functionality.
    
    This enhanced reasoning agent:
    1. Analyzes inputs and chooses optimal strategy (direct vs RAG)
    2. Executes comprehensive mapping analysis
    3. Identifies unmapped fields and generates creative solutions
    4. Provides verification and implementation guidance
    
    Args:
        source_analysis_path: Path to the markdown file with source field analysis
        api_spec_path: Path to the target OpenAPI specification (.json or .yml)
        output_directory: Directory where the final report should be saved
        target_collection_name: Optional RAG collection name for the target API
    
    Returns:
        Path to the generated comprehensive mapping report
    """
    if not TOOLS_AVAILABLE:
        return "❌ Tools not available. Check dependencies."
    
    try:
        result = await reasoning_agent(
            source_analysis_path=source_analysis_path,
            api_spec_path=api_spec_path,
            output_directory=output_directory,
            target_collection_name=target_collection_name if target_collection_name else None
        )
        return result
    except Exception as e:
        logger.error(f"Enhanced reasoning agent failed: {e}")
        return f"❌ Enhanced reasoning agent failed: {str(e)}"

@mcp.tool()
async def generate_kotlin_mapping_code(mapping_report_path: str) -> str:
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
    if not TOOLS_AVAILABLE:
        return "❌ Tools not available. Check dependencies."
    
    try:
        # Read mapping report
        mapping_path = Path(mapping_report_path)
        if not mapping_path.exists():
            return f"❌ Mapping report not found: {mapping_report_path}"
        
        mapping_content = mapping_path.read_text(encoding='utf-8')
       
        
        # Generate enhanced prompt
        prompt = generate_enhanced_prompt(mapping_content)
        
        # Save prompt to file
        output_dir = mapping_path.parent
        prompt_filename = f"kotlin_generation_prompt_{mapping_path.stem}.md"
        prompt_path = output_dir / prompt_filename
        
        with open(prompt_path, 'w', encoding='utf-8') as f:
            f.write(f"# Kotlin Code Generation Prompt\n\n")
            f.write(f"**Generated for mapping report:** {mapping_report_path}\n\n")
            f.write(f"---\n\n")
            f.write(prompt)
        
        return f"✅ Kotlin generation prompt created!\n\n📄 Saved to: {prompt_path}\n\n{prompt}"
        
    except Exception as e:
        logger.error(f"Failed to generate Kotlin prompt: {e}")
        return f"❌ Failed to generate prompt: {str(e)}"

# ============================================================================
# RAG SYSTEM TOOLS (4 tools for RAG management)
# ============================================================================

@mcp.tool()
async def upload_api_specification(
    openapi_file_path: str,
    collection_name: str,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Upload a new OpenAPI specification file (.yml or .json) to the RAG system for analysis.
    
    Args:
        openapi_file_path: Path to the OpenAPI specification file
        collection_name: Name for the RAG collection
        metadata: Optional metadata to attach
    
    Returns:
        Upload status and statistics
    """
    if not TOOLS_AVAILABLE:
        return "❌ Tools not available. Check dependencies."
    
    try:
        result = upload_openapi_spec_to_rag(openapi_file_path, collection_name, metadata)
        return result
    except Exception as e:
        logger.error(f"API spec upload failed: {e}")
        return f"❌ Upload failed: {str(e)}"

@mcp.tool()
async def query_api_specification(
    query: str,
    collection_name: str,
    current_path: str = "",
    limit: int = 5,
    score_threshold: float = 0.5
) -> str:
    """
    Perform a direct query against a specified API collection to retrieve raw documentation snippets and save results as markdown.
    
    Args:
        query: The search query
        collection_name: The collection to search in
        current_path: Current working directory for saving results
        limit: Maximum number of results to return
        score_threshold: Minimum score threshold for relevance
    
    Returns:
        Query results and path to saved markdown file
    """
    if not TOOLS_AVAILABLE:
        return "❌ Tools not available. Check dependencies."
    
    try:
        result = retrieve_from_rag(
            query=query,
            collection_name=collection_name,
            limit=limit,
            score_threshold=score_threshold,
            current_path=current_path if current_path else None
        )
        return result
    except Exception as e:
        logger.error(f"API spec query failed: {e}")
        return f"❌ Query failed: {str(e)}"

@mcp.tool()
async def list_available_api_specs() -> str:
    """
    List all available API specification collections in the RAG system.
    
    Returns:
        List of available collections
    """
    if not TOOLS_AVAILABLE:
        return "❌ Tools not available. Check dependencies."
    
    try:
        result = list_rag_collections()
        return result
    except Exception as e:
        logger.error(f"Failed to list collections: {e}")
        return f"❌ List failed: {str(e)}"

@mcp.tool()
async def delete_api_specification(collection_name: str) -> str:
    """
    Delete an entire API specification collection from the RAG system.
    
    Args:
        collection_name: Name of the collection to delete
    
    Returns:
        Deletion status
    """
    if not TOOLS_AVAILABLE:
        return "❌ Tools not available. Check dependencies."
    
    try:
        result = delete_rag_collection(collection_name)
        return result
    except Exception as e:
        logger.error(f"Failed to delete collection: {e}")
        return f"❌ Delete failed: {str(e)}"

# ============================================================================
# UTILITY TOOLS (2 tools for direct analysis and testing)
# ============================================================================

@mcp.tool()
async def get_direct_api_mapping_prompt(
    api_spec_path: str,
    analysis_md_path: str
) -> str:
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
    if not TOOLS_AVAILABLE:
        return "❌ Tools not available. Check dependencies."
    
    try:
        result = get_api_spec_with_direct_llm_query(api_spec_path, analysis_md_path)
        return result
    except Exception as e:
        logger.error(f"Failed to generate direct mapping prompt: {e}")
        return f"❌ Error calling tool 'get_direct_api_mapping_prompt': {str(e)}"

@mcp.tool()
async def test_rag_system_and_llm() -> str:
    """
    Test RAG system and LLM connectivity.
    
    Returns:
        Status of RAG system and LLM connection
    """
    if not TOOLS_AVAILABLE:
        return "❌ Tools not available. Check dependencies."
    
    try:
        rag_result = test_rag_system()
        llm_result = test_llm_connection()
        
        result = f"""# System Status Test

## 🔍 RAG System Test
{rag_result}

## 🤖 LLM Connection Test  
{llm_result}

## 📊 Summary
- RAG System: {'✅ Working' if '✅' in rag_result else '❌ Issues'}
- LLM Connection: {'✅ Working' if '✅' in llm_result else '❌ Issues'}
"""
        return result
    except Exception as e:
        logger.error(f"System test failed: {e}")
        return f"❌ System test failed: {str(e)}"

# ============================================================================
# SERVER STARTUP
# ============================================================================

if __name__ == "__main__":
    print("🚀 Starting HR API Mapping Server...")
    print(f"🔧 Tools Available: {TOOLS_AVAILABLE}")
    
    if not TOOLS_AVAILABLE:
        print("⚠️  Some tools may not work properly. Check dependencies.")
    
    print("🌐 Server will be available at: http://localhost:8080")
    print("🔗 Ngrok URL: https://9e7b4aa28520.ngrok-free.app")
    print("📋 Add this to your MCP client config:")
    print('"hr_api_mapping_server": {')
    print('  "transport": "sse",')
    print('  "url": "https://9e7b4aa28520.ngrok-free.app/sse/"')
    print('}')
    print()
    print("🛠️  Available Tools:")
    print("   1. analyze_json_fields_with_rag() - JSON field analysis")
    print("   2. reasoning_agent_orchestrator() - Complete mapping orchestration")
    print("   3. generate_kotlin_mapping_code() - Kotlin code generation")
    print("   4. upload_api_specification() - Upload API specs to RAG")
    print("   5. query_api_specification() - Query RAG system")
    print("   6. list_available_api_specs() - List RAG collections")
    print("   7. delete_api_specification() - Delete RAG collections")
    print("   8. get_direct_api_mapping_prompt() - Direct API analysis")
    print("   9. test_rag_system_and_llm() - System health check")
    print()
    
    # Use SSE transport on port 8080 to match ngrok tunnel
    mcp.run(transport="sse", port=8080)