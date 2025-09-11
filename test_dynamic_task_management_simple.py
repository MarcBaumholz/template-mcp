#!/usr/bin/env python3
"""
Simple Test for Dynamic Task Management MCP Tool
Tests the core functionality without server dependencies
"""

import sys
import os
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_core_functionality():
    """Test the core dynamic task management functionality"""
    print("🧪 Testing Core Dynamic Task Management Functionality")
    print("=" * 60)
    
    try:
        # Import the core components
        from tools.phase0_bootstrap.dynamic_task_management_tool import mcp_dynamic_task_management
        from tools.shared_utilities.dynamic_task_manager import task_manager
        from tools.shared_utilities.task_update_templates import TaskUpdateTemplates
        
        print("✅ Successfully imported all components")
        
        # Test 1: Initialize with some tasks
        print("\n1. Adding initial tasks...")
        result = mcp_dynamic_task_management(
            action="add_manual_task",
            task_content="Bootstrap environment and verify RAG connectivity",
            priority="high"
        )
        print(f"✅ Added task: {result['message']}")
        
        result = mcp_dynamic_task_management(
            action="add_manual_task",
            task_content="Upload API specifications to RAG system",
            priority="normal"
        )
        print(f"✅ Added task: {result['message']}")
        
        # Test 2: Simulate MCP tool executions
        print("\n2. Simulating MCP tool executions...")
        
        # Simulate upload_api_specification
        result = mcp_dynamic_task_management(
            action="update_after_tool",
            tool_name="upload_api_specification",
            output_path="outputs/api_spec_uploaded.json",
            analysis="Successfully uploaded Flip API specification with 45 endpoints"
        )
        print(f"✅ Upload tool simulation: {result['message']}")
        print(f"   Generated {result['new_tasks_generated']} new tasks")
        
        # Simulate analyze_json_fields_with_rag
        result = mcp_dynamic_task_management(
            action="update_after_tool",
            tool_name="analyze_json_fields_with_rag",
            output_path="outputs/field_analysis_report.md",
            analysis="Analyzed 23 fields with 85% mapping confidence"
        )
        print(f"✅ Analysis tool simulation: {result['message']}")
        print(f"   Generated {result['new_tasks_generated']} new tasks")
        
        # Simulate reasoning_agent
        result = mcp_dynamic_task_management(
            action="update_after_tool",
            tool_name="reasoning_agent",
            output_path="outputs/reasoning_agent_report.md",
            analysis="Generated comprehensive mapping strategy with 18 verified endpoints"
        )
        print(f"✅ Reasoning tool simulation: {result['message']}")
        print(f"   Generated {result['new_tasks_generated']} new tasks")
        
        # Test 3: Check task summary
        print("\n3. Checking task summary...")
        result = mcp_dynamic_task_management(action="get_task_summary")
        summary = result['summary']
        print(f"📊 Task Summary:")
        print(f"   Total Tasks: {summary['total_tasks']}")
        print(f"   Completed: {summary['completed_tasks']}")
        print(f"   Current: {summary['current_tasks']}")
        print(f"   New Generated: {summary['new_tasks']}")
        print(f"   Completion Rate: {summary['completion_rate']:.1%}")
        
        # Test 4: Get next task
        print("\n4. Getting next task...")
        result = mcp_dynamic_task_management(action="get_next_task")
        if result['next_task']:
            next_task = result['next_task']
            print(f"🎯 Next Task: {next_task['content']}")
        else:
            print("🎉 All tasks completed!")
        
        # Test 5: Get task list
        print("\n5. Getting task list...")
        result = mcp_dynamic_task_management(action="get_task_list")
        tasks = result['tasks']
        print(f"📋 Task List ({len(tasks)} tasks):")
        for i, task in enumerate(tasks[:5], 1):  # Show first 5 tasks
            status = "✅" if task['completed'] else "⏳"
            print(f"   {i}. {status} {task['content']}")
        if len(tasks) > 5:
            print(f"   ... and {len(tasks) - 5} more tasks")
        
        # Test 6: Mark a task as completed
        print("\n6. Marking a task as completed...")
        if tasks:
            first_task = tasks[0]
            result = mcp_dynamic_task_management(
                action="mark_task_completed",
                task_id=first_task['id']
            )
            print(f"✅ Marked task as completed: {result['message']}")
        
        # Test 7: Final summary
        print("\n7. Final task summary...")
        result = mcp_dynamic_task_management(action="get_task_summary")
        summary = result['summary']
        print(f"📊 Final Summary:")
        print(f"   Total Tasks: {summary['total_tasks']}")
        print(f"   Completed: {summary['completed_tasks']}")
        print(f"   Current: {summary['current_tasks']}")
        print(f"   Completion Rate: {summary['completion_rate']:.1%}")
        
        print("\n✅ All core functionality tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_task_templates():
    """Test task generation templates"""
    print("\n🧪 Testing Task Generation Templates")
    print("=" * 60)
    
    try:
        from tools.shared_utilities.task_update_templates import TaskUpdateTemplates
        
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
                tool, f"outputs/{tool}_result.json", f"Test analysis for {tool}"
            )
            print(f"   Generated {len(requirements)} requirements:")
            for i, req in enumerate(requirements, 1):
                print(f"   {i}. {req}")
        
        print("\n✅ Task generation templates test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Task templates test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_file_generation():
    """Test that task files are generated correctly"""
    print("\n📁 Testing Task File Generation")
    print("=" * 60)
    
    try:
        # Check if TASKS.md exists and has content
        if os.path.exists("TASKS.md"):
            with open("TASKS.md", "r") as f:
                content = f.read()
                print(f"✅ TASKS.md exists ({len(content)} characters)")
                
                # Check for key sections
                sections = [
                    "Dynamic Task Management System",
                    "Completed Tasks",
                    "Current Tasks", 
                    "Task Statistics"
                ]
                for section in sections:
                    if section in content:
                        print(f"   ✅ Contains: {section}")
                    else:
                        print(f"   ❌ Missing: {section}")
        else:
            print("❌ TASKS.md file not found")
            return False
        
        # Check if STATUS.md exists and has content
        if os.path.exists("STATUS.md"):
            with open("STATUS.md", "r") as f:
                content = f.read()
                print(f"✅ STATUS.md exists ({len(content)} characters)")
                
                # Check for key sections
                sections = [
                    "Workflow Status Dashboard",
                    "Last Tool Execution",
                    "Task Progress",
                    "Next Actions"
                ]
                for section in sections:
                    if section in content:
                        print(f"   ✅ Contains: {section}")
                    else:
                        print(f"   ❌ Missing: {section}")
        else:
            print("❌ STATUS.md file not found")
            return False
        
        print("\n✅ Task file generation test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ File generation test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("🚀 Dynamic Task Management - Simple Test Suite")
    print("=" * 70)
    
    all_tests_passed = True
    
    # Run all tests
    tests = [
        ("Core Functionality", test_core_functionality),
        ("Task Templates", test_task_templates),
        ("File Generation", test_file_generation)
    ]
    
    for test_name, test_func in tests:
        print(f"\n{'='*70}")
        print(f"Running {test_name}")
        print(f"{'='*70}")
        
        if not test_func():
            all_tests_passed = False
            print(f"❌ {test_name} failed")
        else:
            print(f"✅ {test_name} passed")
    
    # Final results
    print(f"\n{'='*70}")
    print("FINAL RESULTS")
    print(f"{'='*70}")
    
    if all_tests_passed:
        print("🎉 All tests passed successfully!")
        print("\n📋 MCP Tool Usage:")
        print("1. Use mcp_connector_mcp_dynamic_task_management() in your workflow")
        print("2. Available actions: update_after_tool, get_task_summary, add_manual_task")
        print("3. Check TASKS.md and STATUS.md for task updates")
        print("4. Tasks automatically update after each MCP tool execution")
        
        print("\n🎯 Example Usage:")
        print("""
# Update tasks after MCP tool execution
result = mcp_connector_mcp_dynamic_task_management(
    action="update_after_tool",
    tool_name="upload_api_specification",
    output_path="outputs/api_spec_uploaded.json",
    analysis="Successfully uploaded Flip API specification"
)

# Get task summary
result = mcp_connector_mcp_dynamic_task_management(action="get_task_summary")

# Add manual task
result = mcp_connector_mcp_dynamic_task_management(
    action="add_manual_task",
    task_content="Review generated code and fix issues"
)
        """)
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
