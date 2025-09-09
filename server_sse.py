#!/usr/bin/env python3
"""
Fast-loading MCP Server for Connector with Schema Mapping and RAG Tools
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
    logger = logging.getLogger("connector-mcp-sse")
    logger.debug(f"Loading .env from: {env_path}")
    logger.debug(f"OPENROUTER_API_KEY loaded: {'Yes' if os.getenv('OPENROUTER_API_KEY') else 'No'}")
except ImportError:
    pass  # dotenv not available, environment variables should be set manually

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("connector-mcp-sse")

# Initialize MCP server
mcp = FastMCP("Connector MCP Server - SSE")

# Global variables for lazy loading
_json_extraction_tool = None
_combined_json_tool = None
_rag_wrapper = None
_coding_tool = None
_api_spec_getter = None
_reasoning_agent = None
_rules_mcp_tool = None
_phase3_orchestrator = None
_phase3_quality_suite = None
_phase3_selector = None

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
        from tools.phase1_data_extraction.analyze_json_fields_with_rag import CombinedFieldAnalysisAgent
        _combined_json_tool = CombinedFieldAnalysisAgent()
    return _combined_json_tool

def get_coding_tool():
    """Lazy import coding tool"""
    global _coding_tool
    if _coding_tool is None:
        from tools.03_phase3_code_generation.generate_kotlin_mapping_code import generate_enhanced_prompt
        _coding_tool = generate_enhanced_prompt
    return _coding_tool

def get_api_spec_getter():
    """Lazy import API spec getter"""
    global _api_spec_getter
    if _api_spec_getter is None:
        from tools.phase2_analysis_mapping.get_direct_api_mapping_prompt import get_api_spec_with_direct_llm_query
        _api_spec_getter = get_api_spec_with_direct_llm_query
    return _api_spec_getter

def get_reasoning_agent():
    """Lazy import reasoning agent"""
    global _reasoning_agent
    if _reasoning_agent is None:
        from tools.phase2_analysis_mapping.reasoning_agent import reasoning_agent
        _reasoning_agent = reasoning_agent
    return _reasoning_agent

def get_rules_mcp_tool():
    """Lazy import rules MCP tool"""
    global _rules_mcp_tool
    if _rules_mcp_tool is None:
        from tools.shared_utilities.copy_rules_to_working_directory import copy_rules_to_working_directory, get_rules_source_info
        _rules_mcp_tool = {
            'copy_rules': copy_rules_to_working_directory,
            'get_info': get_rules_source_info
        }
    return _rules_mcp_tool

def get_phase3_orchestrator():
    global _phase3_orchestrator
    if _phase3_orchestrator is None:
        from tools.phase3_code_generation.phase3_orchestrator import generate_mapper
        _phase3_orchestrator = generate_mapper
    return _phase3_orchestrator

def get_phase3_quality_suite():
    global _phase3_quality_suite
    if _phase3_quality_suite is None:
        from tools.phase3_code_generation.phase3_quality_suite import run_quality_suite
        _phase3_quality_suite = run_quality_suite
    return _phase3_quality_suite

def get_phase3_selector():
    global _phase3_selector
    if _phase3_selector is None:
        from tools.phase3_code_generation.phase3_selector import select_best_candidate
        _phase3_selector = select_best_candidate
    return _phase3_selector

# RAG Tools (lazy loaded)
@mcp.tool()
def test_rag_system() -> str:
    """Test RAG system and LLM connectivity"""
    from tools.shared_utilities.test_rag_system import test_rag_system as test_rag
    return test_rag()

@mcp.tool()
def list_available_api_specs() -> str:
    """List all available API specification collections in the RAG system with metadata"""
    try:
        from tools.phase1_data_extraction.rag_core import get_rag_system
        rag = get_rag_system()
        collections = rag.list_collections()
        
        if not collections:
            return "No collections found. Upload an API spec first."
        
        # Get detailed collection information
        collection_info = []
        total_points = 0
        
        for name in collections:
            try:
                info = rag.client.get_collection(name)
                points_count = info.points_count
                total_points += points_count
                collection_info.append(f"• {name} ({points_count:,} points)")
            except Exception as e:
                collection_info.append(f"• {name} (metadata unavailable)")
        
        result = f"📊 Available API Collections ({len(collections)}):\n"
        result += "\n".join(collection_info)
        result += f"\n\n📈 Total Points: {total_points:,}"
        
        return result
        
    except Exception as e:
        return f"❌ Error listing collections: {str(e)}"

@mcp.tool()
def upload_api_specification(openapi_file_path: str, collection_name: str, metadata: Optional[Dict[str, Any]] = None) -> str:
    """Upload a new OpenAPI specification file (.yml or .json) to the RAG system for analysis"""
    from tools.phase1_data_extraction.upload_api_spec_tool import upload_openapi_spec_to_rag
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
    from tools.phase1_data_extraction.query_api_spec_tool import retrieve_from_rag
    
    # Convert empty string to None for backward compatibility
    current_path_arg = current_path if current_path else None
    
    return retrieve_from_rag(query, collection_name, limit, score_threshold, current_path_arg)

@mcp.tool()
def delete_api_specification(collection_name: str) -> str:
    """Delete an entire API specification collection from the RAG system"""
    from tools.phase1_data_extraction.delete_api_spec_tool import delete_rag_collection
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
        from tools.phase1_data_extraction.analyze_fields_tool import analyze_fields_with_rag_and_llm as enhanced_analyze
    
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
from tools.phase2_analysis_mapping.iterative_mapping_with_feedback import iterative_field_mapping

# Rules MCP Tools (lazy loaded)
@mcp.tool()
def copy_rules_to_working_directory(target_directory: str = "") -> str:
    """
    Copy the entire .cursor/rules folder structure to the current working directory.
    
    This tool copies all rules, guidelines, and configuration files from the connector-mcp
    .cursor/rules folder to your current working directory. This is the first tool you
    should call when starting development on a new machine or project.
    
    Args:
        target_directory: Optional target directory (defaults to current working directory)
    
    Returns:
        Status message with details about the copy operation
    """
    try:
        rules_tool = get_rules_mcp_tool()
        return rules_tool['copy_rules'](target_directory if target_directory else None)
    except Exception as e:
        logger.error(f"Rules copy failed: {e}")
        return f"❌ Rules copy failed: {str(e)}"

@mcp.tool()
def get_rules_source_info() -> str:
    """
    Get information about the source rules directory structure.
    
    This tool shows you what rules and files will be copied when you use
    copy_rules_to_working_directory. Useful for understanding what's available.
    
    Returns:
        Information about the current rules structure and contents
    """
    try:
        rules_tool = get_rules_mcp_tool()
        return rules_tool['get_info']()
    except Exception as e:
        logger.error(f"Rules info failed: {e}")
        return f"❌ Rules info failed: {str(e)}"

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

@mcp.tool()
def phase3_generate_mapper(
    mapping_report_path: str,
    output_directory: str = "outputs/phase3",
    company_name: str = "flip",
    project_name: str = "integrations",
    backend_name: str = "stackone",
    model: str = "qwen/qwen3-coder:free",
    max_tokens: int = 4000
) -> str:
    try:
        orchestrator = get_phase3_orchestrator()
        result = orchestrator(
            mapping_report_path=mapping_report_path,
            output_directory=output_directory,
            company_name=company_name,
            project_name=project_name,
            backend_name=backend_name,
            model=model,
            max_tokens=max_tokens,
        )
        return result.final_mapper_code or "❌ Generation returned no code"
    except Exception as e:
        return f"❌ Phase 3 mapper generation failed: {str(e)}"

@mcp.tool()
def phase3_quality_suite(
    kotlin_file_path: str,
    mapping_report_path: str,
    output_directory: str = "outputs/phase3/quality",
    model: str = "qwen/qwen3-coder:free"
) -> str:
    try:
        runner = get_phase3_quality_suite()
        report = runner(
            kotlin_file_path=kotlin_file_path,
            mapping_report_path=mapping_report_path,
            output_directory=output_directory,
            model=model,
        )
        import json as _json
        return _json.dumps(report, indent=2)
    except Exception as e:
        return f"❌ Phase 3 quality suite failed: {str(e)}"

@mcp.tool()
def phase3_select_best_candidate(
    kotlin_files: List[str],
    mapping_report_path: str,
    model: str = "qwen/qwen3-coder:free"
) -> str:
    try:
        selector = get_phase3_selector()
        payload = selector(kotlin_files=kotlin_files, mapping_report_path=mapping_report_path, model=model)
        import json as _json
        return _json.dumps(payload, indent=2)
    except Exception as e:
        return f"❌ Phase 3 selector failed: {str(e)}"
if __name__ == "__main__":
    logger.info("🚀 Starting Connector MCP Server with Optimized RAG Tools (SSE)...")
    logger.info("📡 Server will be available via SSE transport on port 8080")
    logger.info("🌐 Use ngrok to expose: ngrok http 8080")
    logger.info("🔧 Available tools:")
    logger.info("   • copy_rules_to_working_directory() - Bootstrap rules folder")
    logger.info("   • get_rules_source_info() - View rules structure")
    logger.info("   • test_rag_system() - Test optimized RAG system")
    logger.info("   • upload_api_specification() - Upload with enhanced chunking")
    logger.info("   • query_api_specification() - Enhanced semantic search")
    logger.info("   • analyze_json_fields_with_rag() - Combined JSON analysis")
    logger.info("   • reasoning_agent() - Complete mapping orchestration")
    logger.info("   • enhanced_rag_analysis() - Enhanced RAG analysis")
    logger.info("   • get_direct_api_mapping_prompt() - Direct API analysis")
    logger.info("   • generate_kotlin_mapping_code() - Kotlin code generation")
    logger.info("   • phase3_generate_mapper() - End-to-end Kotlin generator")
    logger.info("   • phase3_quality_suite() - Audit + TDD tests")
    logger.info("   • phase3_select_best_candidate() - Consistency selector")
    # Run with SSE transport for web compatibility
    mcp.run(transport="sse", port=8080)