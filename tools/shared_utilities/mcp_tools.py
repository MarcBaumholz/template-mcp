"""
MCP Tools Import Module
Imports actual MCP tools for integration with task management
"""

# Import MCP tools from the main server
try:
    from server_fast import (
        upload_api_specification,
        analyze_json_fields_with_rag,
        reasoning_agent,
        phase3_generate_mapper,
        phase3_quality_suite,
        phase4_tdd_validation,
        get_direct_api_mapping_prompt,
        enhanced_rag_analysis,
        iterative_mapping_with_feedback
    )
except ImportError:
    # Fallback if server_fast is not available
    print("Warning: Could not import MCP tools from server_fast")
    
    def upload_api_specification(*args, **kwargs):
        raise NotImplementedError("MCP tool not available")
    
    def analyze_json_fields_with_rag(*args, **kwargs):
        raise NotImplementedError("MCP tool not available")
    
    def reasoning_agent(*args, **kwargs):
        raise NotImplementedError("MCP tool not available")
    
    def phase3_generate_mapper(*args, **kwargs):
        raise NotImplementedError("MCP tool not available")
    
    def phase3_quality_suite(*args, **kwargs):
        raise NotImplementedError("MCP tool not available")
    
    def phase4_tdd_validation(*args, **kwargs):
        raise NotImplementedError("MCP tool not available")
    
    def get_direct_api_mapping_prompt(*args, **kwargs):
        raise NotImplementedError("MCP tool not available")
    
    def enhanced_rag_analysis(*args, **kwargs):
        raise NotImplementedError("MCP tool not available")
    
    def iterative_mapping_with_feedback(*args, **kwargs):
        raise NotImplementedError("MCP tool not available")

# Export all MCP tools
__all__ = [
    'upload_api_specification',
    'analyze_json_fields_with_rag',
    'reasoning_agent',
    'phase3_generate_mapper',
    'phase3_quality_suite',
    'phase4_tdd_validation',
    'get_direct_api_mapping_prompt',
    'enhanced_rag_analysis',
    'iterative_mapping_with_feedback'
]
