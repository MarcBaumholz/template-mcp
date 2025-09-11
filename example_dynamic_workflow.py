#!/usr/bin/env python3
"""
Example Dynamic Workflow
Shows how to use the Dynamic Task Management System with your MCP tools
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.shared_utilities.mcp_tool_integration import (
    upload_api_spec_with_tasks,
    analyze_fields_with_tasks,
    reasoning_agent_with_tasks,
    generate_mapper_with_tasks,
    quality_suite_with_tasks,
    tdd_validation_with_tasks
)
from tools.shared_utilities.dynamic_task_manager import task_manager, get_next_task

def example_dynamic_workflow():
    """Example of using the dynamic task management system with MCP tools"""
    print("🚀 Example Dynamic Workflow")
    print("=" * 50)
    
    # Step 1: Upload API specification (automatically updates tasks)
    print("\n📤 Step 1: Uploading API Specification...")
    try:
        result = upload_api_spec_with_tasks(
            openapi_file_path="/path/to/flip_api.json",
            collection_name="flip_api_v2",
            metadata={"version": "1.0", "source": "flip"}
        )
        print(f"✅ Upload completed: {result}")
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return
    
    # Step 2: Analyze JSON fields (automatically updates tasks)
    print("\n🔍 Step 2: Analyzing JSON Fields...")
    try:
        result = analyze_fields_with_tasks(
            webhook_json_path="/path/to/sample_data.json",
            current_directory="outputs/phase1",
            collection_name="flip_api_v2"
        )
        print(f"✅ Analysis completed: {result}")
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return
    
    # Step 3: Run reasoning agent (automatically updates tasks)
    print("\n🧠 Step 3: Running Reasoning Agent...")
    try:
        result = reasoning_agent_with_tasks(
            source_analysis_path="outputs/phase1/field_analysis_report.md",
            api_spec_path="/path/to/flip_api.json",
            output_directory="outputs/phase2",
            target_collection_name="flip_api_v2"
        )
        print(f"✅ Reasoning completed: {result}")
    except Exception as e:
        print(f"❌ Reasoning failed: {e}")
        return
    
    # Step 4: Generate Kotlin mapper (automatically updates tasks)
    print("\n⚙️ Step 4: Generating Kotlin Mapper...")
    try:
        result = generate_mapper_with_tasks(
            mapping_report_path="outputs/phase2/reasoning_agent_report.md",
            output_directory="outputs/phase3"
        )
        print(f"✅ Code generation completed: {result}")
    except Exception as e:
        print(f"❌ Code generation failed: {e}")
        return
    
    # Step 5: Run quality suite (automatically updates tasks)
    print("\n🔍 Step 5: Running Quality Suite...")
    try:
        result = quality_suite_with_tasks(
            kotlin_file_path="outputs/phase3/AbsenceToWorkdayMapper.kt",
            mapping_report_path="outputs/phase2/reasoning_agent_report.md",
            output_directory="outputs/phase3/quality"
        )
        print(f"✅ Quality suite completed: {result}")
    except Exception as e:
        print(f"❌ Quality suite failed: {e}")
        return
    
    # Step 6: Run TDD validation (automatically updates tasks)
    print("\n🧪 Step 6: Running TDD Validation...")
    try:
        result = tdd_validation_with_tasks(
            kotlin_file_path="outputs/phase3/AbsenceToWorkdayMapper.kt",
            mapping_report_path="outputs/phase2/reasoning_agent_report.md",
            output_directory="outputs/phase4"
        )
        print(f"✅ TDD validation completed: {result}")
    except Exception as e:
        print(f"❌ TDD validation failed: {e}")
        return
    
    # Show final results
    print("\n📊 Final Results...")
    print("=" * 50)
    
    # Get task summary
    summary = task_manager.get_task_summary()
    print(f"📈 Task Summary:")
    print(f"   Total Tasks: {summary['total_tasks']}")
    print(f"   Completed: {summary['completed_tasks']}")
    print(f"   Current: {summary['current_tasks']}")
    print(f"   Completion Rate: {summary['completion_rate']:.1%}")
    
    # Get next task
    next_task = get_next_task()
    if next_task:
        print(f"\n🎯 Next Task: {next_task['content']}")
    else:
        print("\n🎉 All tasks completed!")
    
    print("\n✅ Dynamic Workflow Example Completed!")
    print("Check TASKS.md and STATUS.md for detailed results.")

def show_task_management_commands():
    """Show available task management commands"""
    print("\n🛠️ Available Task Management Commands")
    print("=" * 50)
    
    print("\n1. Basic Task Management:")
    print("   from tools.shared_utilities.dynamic_task_manager import task_manager")
    print("   task_manager.add_manual_task('Your task description')")
    print("   next_task = task_manager.get_next_task()")
    print("   summary = task_manager.get_task_summary()")
    
    print("\n2. Integrated MCP Tools:")
    print("   from tools.shared_utilities.mcp_tool_integration import *")
    print("   result = upload_api_spec_with_tasks(file_path, collection)")
    print("   result = analyze_fields_with_tasks(json_path)")
    print("   result = reasoning_agent_with_tasks(analysis_path, api_path)")
    print("   result = generate_mapper_with_tasks(mapping_report)")
    print("   result = quality_suite_with_tasks(kotlin_file)")
    print("   result = tdd_validation_with_tasks(kotlin_file)")
    
    print("\n3. Task Update Templates:")
    print("   from tools.shared_utilities.task_update_templates import TaskUpdateTemplates")
    print("   requirements = TaskUpdateTemplates.get_tool_specific_requirements(tool_name, output_path, analysis)")
    
    print("\n4. Manual Task Updates:")
    print("   from tools.shared_utilities.dynamic_task_manager import update_tasks_after_tool")
    print("   update_tasks_after_tool(tool_name, output_path, analysis, new_requirements)")

if __name__ == "__main__":
    print("🎯 Dynamic Task Management System - Example Usage")
    print("=" * 60)
    
    try:
        # Show available commands
        show_task_management_commands()
        
        # Run example workflow (commented out to avoid actual MCP calls)
        print("\n" + "=" * 60)
        print("📝 Example Workflow (commented out to avoid actual MCP calls)")
        print("Uncomment the example_dynamic_workflow() call below to run the full example")
        print("=" * 60)
        
        # Uncomment to run the actual example:
        # example_dynamic_workflow()
        
        print("\n✅ Example completed successfully!")
        print("\n📋 Next Steps:")
        print("1. Review the generated TASKS.md file")
        print("2. Check STATUS.md for workflow status")
        print("3. Integrate with your existing MCP tools")
        print("4. Use the task management system in your workflow")
        
    except Exception as e:
        print(f"\n❌ Example failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
