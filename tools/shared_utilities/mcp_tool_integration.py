"""
MCP Tool Integration with Dynamic Task Management
Wraps MCP tools to automatically update task list after execution
"""

import functools
import json
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
from .dynamic_task_manager import task_manager, update_tasks_after_tool
from .task_update_templates import TaskUpdateTemplates

def mcp_tool_with_task_update(tool_name: str, auto_generate_tasks: bool = True):
    """
    Decorator that wraps MCP tools to automatically update task list after execution
    
    Args:
        tool_name: Name of the MCP tool for logging and task generation
        auto_generate_tasks: Whether to automatically generate new tasks based on output
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            print(f"🚀 Executing {tool_name}...")
            
            try:
                # Execute the original MCP tool
                result = func(*args, **kwargs)
                
                # Extract output information
                output_path = _extract_output_path(result)
                analysis = _extract_analysis(result)
                
                # Generate new task requirements if enabled
                new_requirements = []
                if auto_generate_tasks:
                    new_requirements = TaskUpdateTemplates.get_tool_specific_requirements(
                        tool_name, output_path, analysis
                    )
                
                # Update task list
                update_tasks_after_tool(
                    tool_name=tool_name,
                    output_path=output_path,
                    analysis=analysis,
                    new_requirements=new_requirements
                )
                
                # Add result metadata
                if isinstance(result, dict):
                    result['_task_updated'] = True
                    result['_new_tasks_generated'] = len(new_requirements)
                    result['_timestamp'] = datetime.now().isoformat()
                
                print(f"✅ {tool_name} completed successfully. Generated {len(new_requirements)} new tasks.")
                return result
                
            except Exception as e:
                print(f"❌ {tool_name} failed: {str(e)}")
                
                # Update tasks with error information
                update_tasks_after_tool(
                    tool_name=tool_name,
                    output_path=f"ERROR: {str(e)}",
                    analysis=f"Tool execution failed: {str(e)}",
                    new_requirements=[
                        f"🚨 URGENT: Fix {tool_name} execution error",
                        f"Review error details: {str(e)}",
                        "Identify root cause and implement fix",
                        "Re-run tool after fixing issues"
                    ]
                )
                
                raise e
        
        return wrapper
    return decorator

def _extract_output_path(result: Any) -> str:
    """Extract output path from MCP tool result"""
    if isinstance(result, dict):
        # Try common output path keys
        for key in ['output_path', 'output_file', 'file_path', 'result_path', 'path']:
            if key in result and result[key]:
                return str(result[key])
        
        # Try to extract from result content
        if 'result' in result and isinstance(result['result'], str):
            return result['result']
    
    elif isinstance(result, str):
        return result
    
    return "No output path available"

def _extract_analysis(result: Any) -> str:
    """Extract analysis information from MCP tool result"""
    if isinstance(result, dict):
        # Try common analysis keys
        for key in ['analysis', 'summary', 'description', 'message', 'status']:
            if key in result and result[key]:
                return str(result[key])
        
        # Try to extract from result content
        if 'result' in result and isinstance(result['result'], str):
            return result['result'][:200] + "..." if len(result['result']) > 200 else result['result']
    
    elif isinstance(result, str):
        return result[:200] + "..." if len(result) > 200 else result
    
    return "No analysis available"

class MCPToolIntegration:
    """Main integration class for MCP tools with task management"""
    
    def __init__(self):
        self.tool_registry = {}
        self.execution_history = []
    
    def register_tool(self, tool_name: str, tool_function: Callable, auto_generate_tasks: bool = True):
        """Register an MCP tool with task management integration"""
        wrapped_tool = mcp_tool_with_task_update(tool_name, auto_generate_tasks)(tool_function)
        self.tool_registry[tool_name] = wrapped_tool
        print(f"✅ Registered tool: {tool_name}")
    
    def execute_tool(self, tool_name: str, *args, **kwargs) -> Any:
        """Execute a registered MCP tool with task management"""
        if tool_name not in self.tool_registry:
            raise ValueError(f"Tool '{tool_name}' not registered")
        
        tool_function = self.tool_registry[tool_name]
        result = tool_function(*args, **kwargs)
        
        # Log execution
        self.execution_history.append({
            'tool_name': tool_name,
            'timestamp': datetime.now().isoformat(),
            'args': str(args)[:100],
            'kwargs': str(kwargs)[:100],
            'success': True
        })
        
        return result
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get summary of tool executions"""
        return {
            'total_executions': len(self.execution_history),
            'successful_executions': len([e for e in self.execution_history if e['success']]),
            'failed_executions': len([e for e in self.execution_history if not e['success']]),
            'tools_used': list(set(e['tool_name'] for e in self.execution_history)),
            'last_execution': self.execution_history[-1] if self.execution_history else None
        }
    
    def get_next_recommended_tool(self) -> Optional[str]:
        """Get next recommended tool based on current task state"""
        next_task = task_manager.get_next_task()
        if not next_task:
            return None
        
        task_content = next_task['content'].lower()
        
        # Map task content to tool names
        if 'upload' in task_content or 'specification' in task_content:
            return 'upload_api_specification'
        elif 'analyze' in task_content or 'field' in task_content:
            return 'analyze_json_fields_with_rag'
        elif 'reasoning' in task_content or 'mapping' in task_content:
            return 'reasoning_agent'
        elif 'generate' in task_content or 'code' in task_content:
            return 'phase3_generate_mapper'
        elif 'validate' in task_content or 'test' in task_content:
            return 'phase4_tdd_validation'
        elif 'quality' in task_content:
            return 'phase3_quality_suite'
        else:
            return None

# Global integration instance
mcp_integration = MCPToolIntegration()

def register_mcp_tool(tool_name: str, tool_function: Callable, auto_generate_tasks: bool = True):
    """Register an MCP tool with task management integration"""
    mcp_integration.register_tool(tool_name, tool_function, auto_generate_tasks)

def execute_mcp_tool(tool_name: str, *args, **kwargs) -> Any:
    """Execute an MCP tool with task management integration"""
    return mcp_integration.execute_tool(tool_name, *args, **kwargs)

def get_next_recommended_tool() -> Optional[str]:
    """Get next recommended tool based on current task state"""
    return mcp_integration.get_next_recommended_tool()

def get_execution_summary() -> Dict[str, Any]:
    """Get summary of tool executions"""
    return mcp_integration.get_execution_summary()

# Convenience functions for common MCP tools
def upload_api_spec_with_tasks(openapi_file_path: str, collection_name: str, metadata: Dict = None) -> Any:
    """Upload API specification with task management"""
    from .mcp_tools import upload_api_specification
    return execute_mcp_tool('upload_api_specification', openapi_file_path, collection_name, metadata)

def analyze_fields_with_tasks(webhook_json_path: str, current_directory: str = "", collection_name: str = "flip_api_v2") -> Any:
    """Analyze JSON fields with task management"""
    from .mcp_tools import analyze_json_fields_with_rag
    return execute_mcp_tool('analyze_json_fields_with_rag', webhook_json_path, current_directory, collection_name)

def reasoning_agent_with_tasks(source_analysis_path: str, api_spec_path: str, output_directory: str, target_collection_name: str = "") -> Any:
    """Run reasoning agent with task management"""
    from .mcp_tools import reasoning_agent
    return execute_mcp_tool('reasoning_agent', source_analysis_path, api_spec_path, output_directory, target_collection_name)

def generate_mapper_with_tasks(mapping_report_path: str, output_directory: str = "outputs/phase3") -> Any:
    """Generate Kotlin mapper with task management"""
    from .mcp_tools import phase3_generate_mapper
    return execute_mcp_tool('phase3_generate_mapper', mapping_report_path, output_directory)

def quality_suite_with_tasks(kotlin_file_path: str, mapping_report_path: str, output_directory: str = "outputs/phase3/quality") -> Any:
    """Run quality suite with task management"""
    from .mcp_tools import phase3_quality_suite
    return execute_mcp_tool('phase3_quality_suite', kotlin_file_path, mapping_report_path, output_directory)

def tdd_validation_with_tasks(kotlin_file_path: str, mapping_report_path: str, output_directory: str = "outputs/phase4") -> Any:
    """Run TDD validation with task management"""
    from .mcp_tools import phase4_tdd_validation
    return execute_mcp_tool('phase4_tdd_validation', kotlin_file_path, mapping_report_path, output_directory)
