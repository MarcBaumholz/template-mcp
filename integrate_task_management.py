#!/usr/bin/env python3
"""
Integration Script for Dynamic Task Management
Integrates the task management system with your existing MCP tools
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def integrate_with_existing_tools():
    """Show how to integrate task management with existing MCP tools"""
    print("🔧 Integrating Dynamic Task Management with Existing MCP Tools")
    print("=" * 70)
    
    print("\n1. Import the task management system:")
    print("""
from tools.shared_utilities.dynamic_task_manager import update_tasks_after_tool
from tools.shared_utilities.task_update_templates import TaskUpdateTemplates
""")
    
    print("\n2. Wrap your existing MCP tool calls:")
    print("""
# Before (your existing code):
result = your_mcp_tool(param1, param2, param3)

# After (with task management):
result = your_mcp_tool(param1, param2, param3)

# Add this after each MCP tool call:
update_tasks_after_tool(
    tool_name="your_mcp_tool",
    output_path=result.get('output_path', 'No output path'),
    analysis=result.get('analysis', 'No analysis available'),
    new_requirements=TaskUpdateTemplates.get_tool_specific_requirements(
        "your_mcp_tool", 
        result.get('output_path', 'No output path'), 
        result.get('analysis', 'No analysis available')
    )
)
""")
    
    print("\n3. For specific MCP tools, use the integrated versions:")
    print("""
# Instead of:
result = mcp_connector_mcp_upload_api_specification(file_path, collection)

# Use:
from tools.shared_utilities.mcp_tool_integration import upload_api_spec_with_tasks
result = upload_api_spec_with_tasks(file_path, collection)
""")
    
    print("\n4. Add task management to your orchestrator:")
    print("""
# In your orchestrator function:
def run_integration_workflow():
    # ... your existing code ...
    
    # After each MCP tool execution:
    if tool_result:
        update_tasks_after_tool(
            tool_name=current_tool,
            output_path=tool_result.get('output_path'),
            analysis=tool_result.get('analysis'),
            new_requirements=TaskUpdateTemplates.get_tool_specific_requirements(
                current_tool, 
                tool_result.get('output_path'), 
                tool_result.get('analysis')
            )
        )
    
    # ... rest of your code ...
""")
    
    print("\n5. Monitor task progress:")
    print("""
from tools.shared_utilities.dynamic_task_manager import task_manager

# Get current task status
summary = task_manager.get_task_summary()
print(f"Completion rate: {summary['completion_rate']:.1%}")

# Get next task
next_task = task_manager.get_next_task()
if next_task:
    print(f"Next task: {next_task['content']}")
""")

def create_integration_example():
    """Create an example integration file"""
    integration_code = '''#!/usr/bin/env python3
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
'''
    
    with open("example_integration.py", "w") as f:
        f.write(integration_code)
    
    print(f"\n✅ Created example_integration.py with integration example")

def main():
    """Main integration function"""
    print("🎯 Dynamic Task Management Integration Guide")
    print("=" * 60)
    
    try:
        # Show integration instructions
        integrate_with_existing_tools()
        
        # Create example file
        create_integration_example()
        
        print("\n" + "=" * 60)
        print("📋 Integration Summary:")
        print("1. Import the task management system")
        print("2. Wrap your MCP tool calls with update_tasks_after_tool()")
        print("3. Use integrated MCP tools where available")
        print("4. Monitor task progress with task_manager")
        print("5. Check TASKS.md and STATUS.md for updates")
        
        print("\n✅ Integration guide completed!")
        print("\n📁 Files created:")
        print("- example_integration.py (integration example)")
        print("- TASKS.md (dynamic task list)")
        print("- STATUS.md (workflow status)")
        
    except Exception as e:
        print(f"\n❌ Integration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
