"""
Field Enhancement Tools

This module provides tools for enhancing JSON field analysis using RAG and LLM.
"""

import json
from typing import Dict, Any, Optional
from pathlib import Path

from .rag_tools import get_rag_system
from .llm_client import get_llm_response, enhance_field_analysis


def enhance_json_fields(input_json: str, database_name: str = "flip_openapi") -> str:
    """
    Enhance JSON field analysis data using RAG system with targeted queries and LLM analysis.
    
    Args:
        input_json: JSON string with field analysis data to enhance
        database_name: RAG collection name to query
        
    Returns:
        Enhanced analysis as a string
    """
    try:
        # Parse input JSON
        data = json.loads(input_json)
        
        # Get RAG system
        rag = get_rag_system()
        
        enhanced_results = {}
        
        # Process each field in the data
        for field_name, field_info in data.items():
            if isinstance(field_info, dict):
                # Create targeted queries for this field
                queries = [
                    f"field {field_name}",
                    f"parameter {field_name}",
                    f"property {field_name}",
                    f"{field_name} definition",
                    f"{field_name} validation",
                    f"{field_name} type"
                ]
                
                # Collect relevant context from RAG
                context_results = []
                for query in queries:
                    results = rag.query(query, database_name, limit=2, score_threshold=0.3)
                    context_results.extend([r for r in results if 'error' not in r])
                
                # Remove duplicates and get top results
                unique_results = {}
                for result in context_results:
                    text = result['text']
                    if text not in unique_results or result['score'] > unique_results[text]['score']:
                        unique_results[text] = result
                
                top_context = sorted(unique_results.values(), key=lambda x: x['score'], reverse=True)[:3]
                
                # Prepare context for LLM
                api_context = "\n".join([
                    f"Score: {result['score']:.3f}\n{result['text']}"
                    for result in top_context
                ])
                
                # Enhance field analysis with LLM
                enhanced_analysis = enhance_field_analysis(field_name, field_info, api_context)
                
                enhanced_results[field_name] = {
                    "original_data": field_info,
                    "rag_context": top_context,
                    "enhanced_analysis": enhanced_analysis
                }
            else:
                # Handle simple field values
                enhanced_results[field_name] = {
                    "original_data": field_info,
                    "note": "Simple value - no enhancement needed"
                }
        
        # Create comprehensive summary
        summary_prompt = f"""Based on the enhanced field analysis below, provide a comprehensive summary:

Enhanced Field Data:
{json.dumps(enhanced_results, indent=2, default=str)}

Please provide:
1. Overall data structure insights
2. Key relationships between fields
3. Business context and usage patterns
4. Data quality observations
5. Recommendations for data handling

Format as a structured summary."""
        
        summary = get_llm_response(summary_prompt)
        
        # Combine results
        final_result = {
            "enhanced_fields": enhanced_results,
            "comprehensive_summary": summary,
            "metadata": {
                "total_fields_analyzed": len(enhanced_results),
                "database_used": database_name
            }
        }
        
        return json.dumps(final_result, indent=2, default=str)
        
    except Exception as e:
        return f"Error enhancing JSON fields: {str(e)}"


def enhance_json_fields_from_file(file_path: str, database_name: str = "flip_openapi", output_path: Optional[str] = None) -> str:
    """
    Enhance JSON field analysis from a file.
    
    Args:
        file_path: Path to JSON file to enhance
        database_name: RAG collection name to query
        output_path: Optional output file path
        
    Returns:
        Status message
    """
    try:
        # Read input file
        with open(file_path, 'r', encoding='utf-8') as f:
            input_json = f.read()
        
        # Enhance the data
        enhanced_data = enhance_json_fields(input_json, database_name)
        
        # Determine output path
        if output_path is None:
            input_path = Path(file_path)
            output_path = input_path.parent / f"{input_path.stem}_enhanced.json"
        
        # Save enhanced data
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(enhanced_data)
        
        return f"Enhanced analysis saved to: {output_path}"
        
    except Exception as e:
        return f"Error enhancing file: {str(e)}"


def analyze_field_patterns(fields_data: Dict[str, Any]) -> str:
    """
    Analyze patterns across multiple fields.
    
    Args:
        fields_data: Dictionary of field data
        
    Returns:
        Pattern analysis as a string
    """
    try:
        # Extract field characteristics
        field_types = {}
        field_patterns = {}
        
        for field_name, field_info in fields_data.items():
            if isinstance(field_info, dict):
                # Extract type information
                if 'type' in field_info:
                    field_type = field_info['type']
                    if field_type not in field_types:
                        field_types[field_type] = []
                    field_types[field_type].append(field_name)
                
                # Look for naming patterns
                if '_' in field_name:
                    pattern = 'snake_case'
                elif field_name[0].islower() and any(c.isupper() for c in field_name):
                    pattern = 'camelCase'
                elif field_name.isupper():
                    pattern = 'UPPER_CASE'
                else:
                    pattern = 'other'
                
                if pattern not in field_patterns:
                    field_patterns[pattern] = []
                field_patterns[pattern].append(field_name)
        
        # Create analysis prompt
        prompt = f"""Analyze the following field patterns and provide insights:

Field Types Distribution:
{json.dumps(field_types, indent=2)}

Naming Patterns:
{json.dumps(field_patterns, indent=2)}

Please provide:
1. Data type distribution analysis
2. Naming convention consistency
3. Potential data modeling insights
4. Recommendations for standardization
5. Any anomalies or concerns

Format as a structured analysis."""
        
        return get_llm_response(prompt)
        
    except Exception as e:
        return f"Error analyzing field patterns: {str(e)}"