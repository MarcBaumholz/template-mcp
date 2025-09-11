#!/usr/bin/env python3
"""
Test Dynamic Task Management System
Demonstrates how the system updates tasks after each MCP tool execution
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.shared_utilities.dynamic_task_manager import task_manager, update_tasks_after_tool
from tools.shared_utilities.task_update_templates import TaskUpdateTemplates
from tools.shared_utilities.mcp_tool_integration import mcp_integration, register_mcp_tool

def test_dynamic_task_management():
    """Test the dynamic task management system"""
    print("🧪 Testing Dynamic Task Management System")
    print("=" * 50)
    
    # Initialize task manager
    print("\n1. Initializing Task Manager...")
    task_manager.current_tasks = []
    task_manager.new_tasks = []
    
    # Create initial task list
    print("\n2. Creating Initial Task List...")
    initial_tasks = [
        "Bootstrap environment and verify RAG connectivity",
        "Upload API specifications to RAG system",
        "Analyze JSON fields and generate mapping recommendations",
        "Run reasoning agent for comprehensive mapping analysis",
        "Generate Kotlin mapper code",
        "Run quality suite and fix issues",
        "Execute TDD validation tests"
    ]
    
    for i, task_content in enumerate(initial_tasks):
        task_manager.add_manual_task(task_content)
    
    print(f"✅ Created {len(initial_tasks)} initial tasks")
    
    # Simulate MCP tool executions
    print("\n3. Simulating MCP Tool Executions...")
    
    # Simulate upload_api_specification
    print("\n📤 Simulating upload_api_specification...")
    update_tasks_after_tool(
        tool_name="upload_api_specification",
        output_path="outputs/api_spec_uploaded.json",
        analysis="Successfully uploaded Flip API specification with 45 endpoints",
        new_requirements=TaskUpdateTemplates.get_tool_specific_requirements(
            "upload_api_specification", 
            "outputs/api_spec_uploaded.json", 
            "Successfully uploaded Flip API specification with 45 endpoints"
        )
    )
    
    # Simulate analyze_json_fields_with_rag
    print("\n🔍 Simulating analyze_json_fields_with_rag...")
    update_tasks_after_tool(
        tool_name="analyze_json_fields_with_rag",
        output_path="outputs/field_analysis_report.md",
        analysis="Analyzed 23 fields with 85% mapping confidence",
        new_requirements=TaskUpdateTemplates.get_tool_specific_requirements(
            "analyze_json_fields_with_rag",
            "outputs/field_analysis_report.md",
            "Analyzed 23 fields with 85% mapping confidence"
        )
    )
    
    # Simulate reasoning_agent
    print("\n🧠 Simulating reasoning_agent...")
    update_tasks_after_tool(
        tool_name="reasoning_agent",
        output_path="outputs/reasoning_agent_report.md",
        analysis="Generated comprehensive mapping strategy with 18 verified endpoints",
        new_requirements=TaskUpdateTemplates.get_tool_specific_requirements(
            "reasoning_agent",
            "outputs/reasoning_agent_report.md",
            "Generated comprehensive mapping strategy with 18 verified endpoints"
        )
    )
    
    # Simulate get_direct_api_mapping_prompt
    print("\n📝 Simulating get_direct_api_mapping_prompt...")
    update_tasks_after_tool(
        tool_name="get_direct_api_mapping_prompt",
        output_path="outputs/optimized_mapping_prompt.md",
        analysis="Generated optimized mapping prompt with 15 specific instructions",
        new_requirements=TaskUpdateTemplates.get_tool_specific_requirements(
            "get_direct_api_mapping_prompt",
            "outputs/optimized_mapping_prompt.md",
            "Generated optimized mapping prompt with 15 specific instructions"
        )
    )
    
    # Simulate phase3_generate_mapper
    print("\n⚙️ Simulating phase3_generate_mapper...")
    update_tasks_after_tool(
        tool_name="phase3_generate_mapper",
        output_path="outputs/phase3/AbsenceToWorkdayMapper.kt",
        analysis="Generated Kotlin mapper with Controller/Service/Mapper architecture",
        new_requirements=TaskUpdateTemplates.get_tool_specific_requirements(
            "phase3_generate_mapper",
            "outputs/phase3/AbsenceToWorkdayMapper.kt",
            "Generated Kotlin mapper with Controller/Service/Mapper architecture"
        )
    )
    
    # Simulate phase3_quality_suite
    print("\n🔍 Simulating phase3_quality_suite...")
    update_tasks_after_tool(
        tool_name="phase3_quality_suite",
        output_path="outputs/phase3/quality/quality_report.md",
        analysis="Quality suite passed with 95% score, 2 minor issues identified",
        new_requirements=TaskUpdateTemplates.get_tool_specific_requirements(
            "phase3_quality_suite",
            "outputs/phase3/quality/quality_report.md",
            "Quality suite passed with 95% score, 2 minor issues identified"
        )
    )
    
    # Simulate phase4_tdd_validation
    print("\n🧪 Simulating phase4_tdd_validation...")
    update_tasks_after_tool(
        tool_name="phase4_tdd_validation",
        output_path="outputs/phase4/tdd_validation_report.md",
        analysis="TDD validation completed with 12/12 tests passing",
        new_requirements=TaskUpdateTemplates.get_tool_specific_requirements(
            "phase4_tdd_validation",
            "outputs/phase4/tdd_validation_report.md",
            "TDD validation completed with 12/12 tests passing"
        )
    )
    
    # Display final results
    print("\n4. Final Results...")
    print("=" * 50)
    
    # Show task summary
    summary = task_manager.get_task_summary()
    print(f"📊 Task Summary:")
    print(f"   Total Tasks: {summary['total_tasks']}")
    print(f"   Completed: {summary['completed_tasks']}")
    print(f"   Current: {summary['current_tasks']}")
    print(f"   New Generated: {summary['new_tasks']}")
    print(f"   Completion Rate: {summary['completion_rate']:.1%}")
    
    # Show next task
    next_task = task_manager.get_next_task()
    if next_task:
        print(f"\n🎯 Next Task: {next_task['content']}")
    else:
        print("\n🎉 All tasks completed!")
    
    # Show execution summary
    execution_summary = mcp_integration.get_execution_summary()
    print(f"\n📈 Execution Summary:")
    print(f"   Total Executions: {execution_summary['total_executions']}")
    print(f"   Successful: {execution_summary['successful_executions']}")
    print(f"   Failed: {execution_summary['failed_executions']}")
    print(f"   Tools Used: {', '.join(execution_summary['tools_used'])}")
    
    print("\n✅ Dynamic Task Management System Test Completed!")
    print("Check TASKS.md and STATUS.md files for detailed results.")

def test_task_templates():
    """Test task update templates"""
    print("\n🧪 Testing Task Update Templates")
    print("=" * 50)
    
    # Test different tool types
    tools_to_test = [
        "upload_api_specification",
        "analyze_json_fields_with_rag", 
        "reasoning_agent",
        "get_direct_api_mapping_prompt",
        "phase3_generate_mapper",
        "phase3_quality_suite",
        "phase4_tdd_validation"
    ]
    
    for tool in tools_to_test:
        print(f"\n🔧 Testing {tool}...")
        requirements = TaskUpdateTemplates.get_tool_specific_requirements(
            tool, f"outputs/{tool}_result.json", "Test analysis result"
        )
        print(f"   Generated {len(requirements)} requirements:")
        for i, req in enumerate(requirements, 1):
            print(f"   {i}. {req}")
    
    print("\n✅ Task Update Templates Test Completed!")

if __name__ == "__main__":
    print("🚀 Dynamic Task Management System Test Suite")
    print("=" * 60)
    
    try:
        test_dynamic_task_management()
        test_task_templates()
        
        print("\n🎉 All Tests Passed Successfully!")
        print("\n📋 Next Steps:")
        print("1. Review TASKS.md for updated task list")
        print("2. Check STATUS.md for workflow status")
        print("3. Integrate with your MCP tools")
        print("4. Use the task management system in your workflow")
        
    except Exception as e:
        print(f"\n❌ Test Failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
