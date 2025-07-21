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
    logger = logging.getLogger("template-mcp-fast")
    logger.debug(f"Loading .env from: {env_path}")
    logger.debug(f"OPENROUTER_API_KEY loaded: {'Yes' if os.getenv('OPENROUTER_API_KEY') else 'No'}")
except ImportError:
    pass  # dotenv not available, environment variables should be set manually

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("template-mcp-fast")

# Initialize MCP server
mcp = FastMCP("Template MCP Server")

# Global variables for lazy loading
_fixed_mapping_tool = None
_json_extraction_tool = None
_rag_wrapper = None
_enhancement_tool = None
_coding_tool = None
_api_spec_getter = None
_reasoning_agent = None
_proof_tool = None

def get_fixed_mapping_tool(debug_dir: str = "outputs/schema_mapping_debug"):
    """Lazy import fixed mapping tool"""
    global _fixed_mapping_tool
    if _fixed_mapping_tool is None:
        from tools.mapping_fixed import FixedMappingTool
        _fixed_mapping_tool = FixedMappingTool(debug_dir=debug_dir)
    return _fixed_mapping_tool

def get_json_extraction_tool():
    """Lazy import JSON extraction tool"""
    global _json_extraction_tool
    if _json_extraction_tool is None:
        from tools.json_tool.json_extraction_agent import JsonExtractionAgent
        _json_extraction_tool = JsonExtractionAgent()
    return _json_extraction_tool

def get_enhancement_tool():
    """Lazy import enhancement tool"""
    global _enhancement_tool
    if _enhancement_tool is None:
        from tools.enhancer.enhancer import FieldEnhancer
        _enhancement_tool = FieldEnhancer()
    return _enhancement_tool

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

def get_proof_tool():
    """Lazy import proof tool"""
    global _proof_tool
    if _proof_tool is None:
        from tools.proof_tool import generate_proof_prompt
        _proof_tool = generate_proof_prompt
    return _proof_tool

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
def analyze_fields_with_rag_and_llm(
    fields_to_analyze: List[str], 
    collection_name: str = "flip_api_v2", 
    context_topic: str = "",
    current_path: str = ""
) -> str:
    """Analyze a list of fields against an API spec using LLM to synthesize findings. Optional current_path parameter to specify where to save analysis files"""
    from tools.rag_tools import analyze_fields_with_rag_and_llm as analyze_fields
    
    # Convert empty strings to None for backward compatibility
    context_topic_arg = context_topic if context_topic else None
    current_path_arg = current_path if current_path else None
    
    return analyze_fields(fields_to_analyze, collection_name, context_topic_arg, current_path_arg)


# Reasoning Agent Tool (lazy loaded)
@mcp.tool()
async def reasoning_agent(
    source_analysis_path: str,
    api_spec_path: str,
    output_directory: str,
    target_collection_name: str = ""
) -> str:
    """
    Orchestrates the entire schema mapping process from a high-level goal.
    Decides whether to use direct analysis or a RAG-based approach,
    executes the necessary tools, and returns a final report.
    """
    agent = get_reasoning_agent()
    # Convert empty string to None for backward compatibility
    collection_name_arg = target_collection_name if target_collection_name else None
    return await agent(
        source_analysis_path=source_analysis_path,
        api_spec_path=api_spec_path,
        output_directory=output_directory,
        target_collection_name=collection_name_arg
    )


# Schema Mapping Tool (lazy loaded)
"""
@mcp.tool()
async def intelligent_schema_mapping(
    source_json_path: str,
    target_collection_name: str,
    mapping_context: str,
    source_analysis_md_path: str = "",
    max_matches_per_field: int = 3,
    output_path: str = ""
) -> str:
    '''
    Intelligent schema mapping using multi-agent AI system with RAG-based target field discovery.
    
    This tool performs cognitive pattern matching between source fields and target API fields,
    using multiple AI agents to provide comprehensive analysis and mapping recommendations.
    '''
    try:
        # Convert empty strings to None for backward compatibility
        source_analysis_md_path_arg = source_analysis_md_path if source_analysis_md_path else None
        output_path_arg = output_path if output_path else None
        
        # Get mapping tool and run analysis
        mapping_tool = get_mapping_tool()
        result = await mapping_tool.map_schema(
            source_json_path=source_json_path,
            target_collection_name=target_collection_name,
            mapping_context=mapping_context,
            source_analysis_md_path=source_analysis_md_path_arg,
            max_matches_per_field=max_matches_per_field,
            output_path=output_path_arg
        )
        
        return result
            
    except Exception as e:
        logger.error(f"Schema mapping failed: {e}")
        return f"Schema mapping failed: {str(e)}"
"""

"""
@mcp.tool()
async def intelligent_schema_mapping_fixed(
    source_json_path: str,
    target_collection_name: str,
    mapping_context: str,
    source_analysis_md_path: str = "",
    max_matches_per_field: int = 3,
    output_path: str = ""
) -> str:
    '''
    Enhanced intelligent schema mapping using multi-agent AI system with RAG-based target field discovery.
    
    This version uses structured RAG data and generates detailed debug markdown files.
    
    This tool performs cognitive pattern matching between source fields and target API fields,
    using multiple AI agents to provide comprehensive analysis and mapping recommendations.
    
    Args:
        source_json_path: Path to JSON file containing source schema fields
        target_collection_name: Name of the RAG collection containing target API documentation
        mapping_context: Business context for the mapping (e.g., "HR system integration")
        source_analysis_md_path: Optional path to markdown analysis of source fields
        max_matches_per_field: Maximum number of target matches to find per source field (default: 3)
        output_path: Optional output directory for debug files
    
    Returns:
        Comprehensive markdown report of schema mapping results with detailed analysis
    '''
    try:
        # Create the fixed mapping tool with debug output
        debug_dir = output_path if output_path else "outputs/schema_mapping_debug"
        mapping_tool = get_fixed_mapping_tool(debug_dir)
        
        # Execute the mapping
        result = await mapping_tool.map_schema(
            source_json_path=source_json_path,
            target_collection_name=target_collection_name,
            mapping_context=mapping_context,
            source_analysis_md_path=source_analysis_md_path if source_analysis_md_path else None,
            max_matches_per_field=max_matches_per_field,
            output_path=output_path if output_path else None
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Fixed schema mapping failed: {e}")
        return f"❌ Schema mapping failed: {str(e)}"
"""

# JSON Extraction Tool (lazy loaded)
@mcp.tool()
async def identify_relevant_json_fields(
    webhook_json_path: str = "",
    current_directory: str = ""
) -> str:
    """
    Extract and analyze important fields from HRIS webhook JSON data using LangGraph agent.
    
    This tool uses a LangGraph-based agent with LLM analysis to extract key fields from JSON webhook data,
    validate the data structure, and provide business context insights.
    
    Args:
        webhook_json_path: Path to the webhook JSON file to analyze
        current_directory: Optional current directory path where result files should be saved (defaults to agent's results directory)
    
    Returns:
        Comprehensive analysis report with extracted fields, validation status, and business insights
    """
    try:
        # Load the JSON data
        if not os.path.exists(webhook_json_path):
            return f"❌ Error: JSON file not found at path: {webhook_json_path}"
        
        with open(webhook_json_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        # Get the JSON extraction tool
        extraction_agent = get_json_extraction_tool()
        
        # If current_directory is provided, update the agent's results directory
        if current_directory:
            if os.path.exists(current_directory):
                extraction_agent.results_dir = current_directory
            else:
                logger.warning(f"Current directory {current_directory} doesn't exist, using default results directory")
        
        # Process the JSON data
        result = await extraction_agent.process_json(json_data)
        
        if result.status == "error":
            return f"❌ JSON extraction failed: {result.error}"
        
        # Format the successful result
        report = f"""# 🔍 JSON Field Extraction Results

## ✅ Processing Status: {result.status.upper()}
**Agent**: {result.agent_name}
**Processed At**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 Extracted Fields
```json
{json.dumps(result.result.extracted_fields, indent=2)}
```

## 🎯 Analysis Summary
- **Validation Status**: {result.result.validation_status}
- **Confidence Score**: {result.result.confidence_score:.2f}/1.0
- **Data Quality**: {'High' if result.result.confidence_score > 0.8 else 'Medium' if result.result.confidence_score > 0.5 else 'Low'}

## 📝 Processing Notes
{result.result.processing_notes}

## 🧠 Business Context
{result.result.context}

## 📁 Result Files
- **JSON file analyzed**: `{webhook_json_path}`
- **Results saved to**: `{extraction_agent.results_dir}/`
- **Detailed JSON result**: Saved with timestamp in results directory

## 🔄 Next Steps
1. Review the extracted fields for completeness
2. Validate the business context interpretation
3. Use the extracted fields for downstream processing
4. Check the detailed JSON result file for full extraction data

---
*Analysis completed using LangGraph FieldExtractionAgent with OpenRouter LLM*"""
        
        return report
        
    except json.JSONDecodeError as e:
        return f"❌ Invalid JSON format in file {webhook_json_path}: {str(e)}"
    except Exception as e:
        logger.error(f"JSON extraction failed: {e}")
        return f"❌ JSON extraction failed: {str(e)}"
'''
# Field Enhancement Tool (lazy loaded)
@mcp.tool()
async def enhance_json_fields(
    json_result_path: str,
    current_directory: str = ""
) -> str:
    """
    Enhance extracted JSON fields with semantic metadata using LangGraph agent.
    
    This tool takes a JSON extraction result and enhances the fields with semantic descriptions,
    synonyms, possible data types, and business context using AI analysis.
    
    Args:
        json_result_path: Path to the JSON extraction result file to enhance
        current_directory: Optional current directory path where enhanced result files should be saved (defaults to agent's results directory)
    
    Returns:
        Comprehensive enhancement report with semantic metadata for each field
    """
    try:
        # Load the JSON extraction result
        if not os.path.exists(json_result_path):
            return f"❌ Error: JSON result file not found at path: {json_result_path}"
        
        with open(json_result_path, 'r', encoding='utf-8') as f:
            extraction_result = json.load(f)
        
        # Get the enhancement tool
        enhancement_agent = get_enhancement_tool()
        
        # If current_directory is provided, update the agent's results directory
        if current_directory:
            if os.path.exists(current_directory):
                enhancement_agent.results_dir = current_directory
            else:
                logger.warning(f"Current directory {current_directory} doesn't exist, using default results directory")
        
        # Process the extraction result for enhancement
        result = await enhancement_agent.enhance_fields(extraction_result)
        
        if result.status == "error":
            return f"❌ Field enhancement failed: {result.error}"
        
        # Format the successful result
        enhanced_fields_summary = []
        for field in result.result.enhanced_fields:
            enhanced_fields_summary.append(f"""
### 📋 {field.field_name}
- **Description**: {field.semantic_description}
- **Synonyms**: {', '.join(field.synonyms) if field.synonyms else 'None'}
- **Data Types**: {', '.join(field.possible_datatypes)}
- **Business Context**: {field.business_context}
""")
        
        report = f"""# 🧠 Field Enhancement Results

## ✅ Processing Status: {result.status.upper()}
**Agent**: {result.agent_name}
**Enhancement Confidence**: {result.result.enhancement_confidence:.2f}/1.0
**Processed At**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🎯 Processing Context
{result.result.processing_context}

## 📊 Enhanced Fields Summary
{''.join(enhanced_fields_summary)}

## 📁 Result Files
- **Original JSON file**: `{json_result_path}`
- **Enhanced results saved to**: `{enhancement_agent.results_dir}/`
- **Detailed enhancement file**: Saved with timestamp in results directory

## 🔄 Next Steps
1. Review the enhanced field metadata for accuracy
2. Use the semantic descriptions for API mapping
3. Leverage synonyms for field matching in different systems
4. Apply business context for integration decisions
5. Check the detailed enhancement result file for complete data

---
*Enhancement completed using LangGraph FieldEnhancementAgent with OpenRouter LLM*"""
        
        return report
        
    except json.JSONDecodeError as e:
        return f"❌ Invalid JSON format in file {json_result_path}: {str(e)}"
    except Exception as e:
        logger.error(f"Field enhancement failed: {e}")
        return f"❌ Field enhancement failed: {str(e)}"
'''

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

# Proof Tool (lazy loaded)
@mcp.tool()
async def generate_proof_prompt(
    mapping_report_path: str,
    api_spec_path: str,
    current_path: str = "",
    collection_name: str = "flip_api_v2"
) -> str:
    """
    Generate a comprehensive proof prompt for Cursor to double-check field mappings
    and provide creative solutions for unmapped fields.
    
    This tool analyzes existing mapping reports, identifies unmapped fields,
    searches the API specification for missed opportunities, and generates
    creative solutions for handling unmapped fields. The output is a detailed
    prompt that can be used in Cursor to perform thorough verification and
    implementation of field mappings.
    
    Args:
        mapping_report_path: Path to the mapping analysis report
        api_spec_path: Path to the OpenAPI specification
        current_path: Current working directory path (defaults to "reports")
        collection_name: RAG collection name for API spec (defaults to "flip_api_v2")
    
    Returns:
        Comprehensive prompt string for Cursor with verification tasks and creative solutions
    """
    try:
        proof_tool = get_proof_tool()
        result = await proof_tool(
            mapping_report_path=mapping_report_path,
            api_spec_path=api_spec_path,
            current_path=current_path,
            collection_name=collection_name
        )
        return result
    except Exception as e:
        logger.error(f"Failed to generate proof prompt: {e}")
        return f"❌ Failed to generate proof prompt: {str(e)}"

if __name__ == "__main__":
    logger.info("Starting Template MCP Server (Fast Loading)...")
    mcp.run()