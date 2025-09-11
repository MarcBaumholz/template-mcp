#!/usr/bin/env python3
"""
Example Integration of Dynamic Task Management with MCP Tools
"""

from tools.shared_utilities.dynamic_task_manager import update_tasks_after_tool
from tools.shared_utilities.task_update_templates import TaskUpdateTemplates

def your_existing_mcp_tool(param1, param2):
    """Your existing MCP tool"""
    # Your existing implementation
    result = {
        'output_path': f'outputs/{param1}_result.json',
        'analysis': f'Processed {param1} with {param2}',
        'status': 'success'
    }
    return result

def enhanced_mcp_tool_with_tasks(param1, param2):
    """Enhanced version with task management"""
    # Execute your existing tool
    result = your_existing_mcp_tool(param1, param2)
    
    # Update tasks automatically
    update_tasks_after_tool(
        tool_name="your_existing_mcp_tool",
        output_path=result.get('output_path'),
        analysis=result.get('analysis'),
        new_requirements=TaskUpdateTemplates.get_tool_specific_requirements(
            "your_existing_mcp_tool", 
            result.get('output_path'), 
            result.get('analysis')
        )
    )
    
    return result

# Usage
if __name__ == "__main__":
    # Use the enhanced version
    result = enhanced_mcp_tool_with_tasks("test_param", "test_value")
    print(f"Result: {result}")
