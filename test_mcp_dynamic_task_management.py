#!/usr/bin/env python3
"""
Test MCP Dynamic Task Management Tool
Tests the MCP tool integration for dynamic task management
"""

import sys
import os
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_mcp_dynamic_task_management():
    """Test the MCP dynamic task management tool"""
    print("🧪 Testing MCP Dynamic Task Management Tool")
    print("=" * 50)
    
    try:
        # Import the MCP tool
        from tools.phase0_bootstrap.dynamic_task_management_tool import mcp_dynamic_task_management
        print("✅ Successfully imported MCP tool")
        
        # Test 1: Get task summary
        print("\n1. Testing get_task_summary...")
        result = mcp_dynamic_task_management(action="get_task_summary")
        print(f"Result: {json.dumps(result, indent=2)}")
        
        # Test 2: Add manual task
        print("\n2. Testing add_manual_task...")
        result = mcp_dynamic_task_management(
            action="add_manual_task",
            task_content="Test manual task from MCP tool",
            priority="normal"
        )
        print(f"Result: {json.dumps(result, indent=2)}")
        
        # Test 3: Get task list
        print("\n3. Testing get_task_list...")
        result = mcp_dynamic_task_management(action="get_task_list")
        print(f"Result: {json.dumps(result, indent=2)}")
        
        # Test 4: Update after tool execution
        print("\n4. Testing update_after_tool...")
        result = mcp_dynamic_task_management(
            action="update_after_tool",
            tool_name="test_mcp_tool",
            output_path="outputs/test_result.json",
            analysis="Test tool execution completed successfully"
        )
        print(f"Result: {json.dumps(result, indent=2)}")
        
        # Test 5: Generate tasks from tool
        print("\n5. Testing generate_tasks_from_tool...")
        result = mcp_dynamic_task_management(
            action="generate_tasks_from_tool",
            tool_name="upload_api_specification",
            output_path="outputs/api_spec_uploaded.json",
            analysis="Successfully uploaded Flip API specification"
        )
        print(f"Result: {json.dumps(result, indent=2)}")
        
        # Test 6: Get next task
        print("\n6. Testing get_next_task...")
        result = mcp_dynamic_task_management(action="get_next_task")
        print(f"Result: {json.dumps(result, indent=2)}")
        
        # Test 7: Get final task summary
        print("\n7. Testing final get_task_summary...")
        result = mcp_dynamic_task_management(action="get_task_summary")
        print(f"Result: {json.dumps(result, indent=2)}")
        
        print("\n✅ All MCP tool tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def test_server_integration():
    """Test the server integration"""
    print("\n🔧 Testing Server Integration")
    print("=" * 50)
    
    try:
        # Test the server_fast.py integration
        from server_fast import get_dynamic_task_management_tool, auto_update_tasks_after_tool
        
        # Test tool import
        tool = get_dynamic_task_management_tool()
        print("✅ Successfully imported tool from server")
        
        # Test auto update function
        auto_update_tasks_after_tool(
            tool_name="test_server_tool",
            result='{"output_path": "test_output.json", "analysis": "Test server integration"}'
        )
        print("✅ Successfully called auto_update_tasks_after_tool")
        
        print("\n✅ Server integration tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Server integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def test_task_file_generation():
    """Test that task files are generated correctly"""
    print("\n📁 Testing Task File Generation")
    print("=" * 50)
    
    try:
        # Check if TASKS.md exists
        if os.path.exists("TASKS.md"):
            print("✅ TASKS.md file exists")
            with open("TASKS.md", "r") as f:
                content = f.read()
                print(f"File size: {len(content)} characters")
                print(f"Contains task sections: {'✅ Completed Tasks' in content}")
        else:
            print("❌ TASKS.md file not found")
            return False
        
        # Check if STATUS.md exists
        if os.path.exists("STATUS.md"):
            print("✅ STATUS.md file exists")
            with open("STATUS.md", "r") as f:
                content = f.read()
                print(f"File size: {len(content)} characters")
                print(f"Contains status sections: {'Last Tool Execution' in content}")
        else:
            print("❌ STATUS.md file not found")
            return False
        
        print("\n✅ Task file generation tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Task file generation test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def main():
    """Main test function"""
    print("🚀 MCP Dynamic Task Management Test Suite")
    print("=" * 60)
    
    all_tests_passed = True
    
    # Run all tests
    tests = [
        ("MCP Tool Tests", test_mcp_dynamic_task_management),
        ("Server Integration Tests", test_server_integration),
        ("Task File Generation Tests", test_task_file_generation)
    ]
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"Running {test_name}")
        print(f"{'='*60}")
        
        if not test_func():
            all_tests_passed = False
            print(f"❌ {test_name} failed")
        else:
            print(f"✅ {test_name} passed")
    
    # Final results
    print(f"\n{'='*60}")
    print("FINAL RESULTS")
    print(f"{'='*60}")
    
    if all_tests_passed:
        print("🎉 All tests passed successfully!")
        print("\n📋 Next Steps:")
        print("1. Use the dynamic_task_management MCP tool in your workflow")
        print("2. Check TASKS.md and STATUS.md for task updates")
        print("3. Integrate with your existing MCP tools")
        print("4. Monitor task progress and completion rates")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
