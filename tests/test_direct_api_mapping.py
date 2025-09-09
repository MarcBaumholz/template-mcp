#!/usr/bin/env python3
"""
Test script for get_direct_api_mapping_prompt tool
Tests both direct function call and MCP server integration
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_direct_function_call():
    """Test the function directly without MCP server"""
    print("🧪 Testing direct function call...")
    
    try:
        from tools.api_spec_getter import get_direct_api_mapping_prompt
        
        # Test parameters from the error
        api_spec_path = "/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/test_temp_stackone/absences-stackone/backend/src/main/resources/openapi-definitions/stackone/api_stackone.json"
        analysis_md_path = "/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/stackone_temp_aug/clean_analysis_20250821_115102.md"
        
        # Check if files exist
        if not os.path.exists(api_spec_path):
            print(f"❌ API spec file not found: {api_spec_path}")
            return False
            
        if not os.path.exists(analysis_md_path):
            print(f"❌ Analysis file not found: {analysis_md_path}")
            return False
        
        print(f"✅ Files exist")
        print(f"   API spec: {os.path.getsize(api_spec_path)} bytes")
        print(f"   Analysis: {os.path.getsize(analysis_md_path)} bytes")
        
        # Call the function
        result = get_direct_api_mapping_prompt(api_spec_path, analysis_md_path)
        
        if result.startswith("❌"):
            print(f"❌ Function returned error: {result}")
            return False
        
        print(f"✅ Direct function call successful")
        print(f"   Result length: {len(result)} characters")
        print(f"   First 200 chars: {result[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Direct function call failed: {e}")
        return False

def test_mcp_server_integration():
    """Test the MCP server integration"""
    print("\n🧪 Testing MCP server integration...")
    
    try:
        # Start the server in background
        print("Starting MCP server...")
        server_process = subprocess.Popen(
            [sys.executable, "server_fast.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for server to start
        time.sleep(3)
        
        # Check if server is running
        if server_process.poll() is not None:
            stdout, stderr = server_process.communicate()
            print(f"❌ Server failed to start")
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            return False
        
        print("✅ Server started successfully")
        
        # Test the MCP tool call
        test_data = {
            "api_spec_path": "/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/test_temp_stackone/absences-stackone/backend/src/main/resources/openapi-definitions/stackone/api_stackone.json",
            "analysis_md_path": "/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/stackone_temp_aug/clean_analysis_20250821_115102.md"
        }
        
        print("Testing MCP tool call...")
        
        # Import and test the MCP tool
        from server_fast import get_direct_api_mapping_prompt
        
        result = get_direct_api_mapping_prompt(
            test_data["api_spec_path"],
            test_data["analysis_md_path"]
        )
        
        if result.startswith("❌"):
            print(f"❌ MCP tool returned error: {result}")
            server_process.terminate()
            return False
        
        print(f"✅ MCP tool call successful")
        print(f"   Result length: {len(result)} characters")
        
        # Clean up
        server_process.terminate()
        server_process.wait()
        
        return True
        
    except Exception as e:
        print(f"❌ MCP server integration failed: {e}")
        return False

def test_file_content_analysis():
    """Analyze the content of the files to identify potential issues"""
    print("\n🔍 Analyzing file content...")
    
    try:
        api_spec_path = "/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/test_temp_stackone/absences-stackone/backend/src/main/resources/openapi-definitions/stackone/api_stackone.json"
        analysis_md_path = "/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/stackone_temp_aug/clean_analysis_20250821_115102.md"
        
        # Read and analyze API spec
        with open(api_spec_path, 'r', encoding='utf-8') as f:
            api_spec_content = f.read()
        
        # Read and analyze analysis file
        with open(analysis_md_path, 'r', encoding='utf-8') as f:
            analysis_content = f.read()
        
        total_chars = len(api_spec_content) + len(analysis_content)
        limit = 800000  # From the code
        
        print(f"📊 File Analysis:")
        print(f"   API spec: {len(api_spec_content)} characters")
        print(f"   Analysis: {len(analysis_content)} characters")
        print(f"   Total: {total_chars} characters")
        print(f"   Limit: {limit} characters")
        print(f"   Within limit: {'✅' if total_chars <= limit else '❌'}")
        
        # Check for potential encoding issues
        print(f"\n🔍 Content Analysis:")
        print(f"   API spec starts with: {api_spec_content[:100]}...")
        print(f"   Analysis starts with: {analysis_content[:100]}...")
        
        # Check for JSON validity
        try:
            json.loads(api_spec_content)
            print(f"   API spec JSON: ✅ Valid")
        except json.JSONDecodeError as e:
            print(f"   API spec JSON: ❌ Invalid - {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ File content analysis failed: {e}")
        return False

def test_improved_error_handling():
    """Test improved error handling in the tool"""
    print("\n🔧 Testing improved error handling...")
    
    try:
        from tools.api_spec_getter import get_direct_api_mapping_prompt
        
        # Test with non-existent files
        result = get_direct_api_mapping_prompt("nonexistent.json", "nonexistent.md")
        if not result.startswith("❌"):
            print(f"❌ Expected error for non-existent files, got: {result[:100]}...")
            return False
        
        print("✅ Error handling for non-existent files works")
        
        # Test with valid files
        api_spec_path = "/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/test_temp_stackone/absences-stackone/backend/src/main/resources/openapi-definitions/stackone/api_stackone.json"
        analysis_md_path = "/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/stackone_temp_aug/clean_analysis_20250821_115102.md"
        
        result = get_direct_api_mapping_prompt(api_spec_path, analysis_md_path)
        if result.startswith("❌"):
            print(f"❌ Unexpected error with valid files: {result}")
            return False
        
        print("✅ Error handling for valid files works")
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting comprehensive test for get_direct_api_mapping_prompt")
    print("=" * 60)
    
    tests = [
        ("File Content Analysis", test_file_content_analysis),
        ("Direct Function Call", test_direct_function_call),
        ("Improved Error Handling", test_improved_error_handling),
        ("MCP Server Integration", test_mcp_server_integration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
            print(f"{'✅ PASSED' if result else '❌ FAILED'}: {test_name}")
        except Exception as e:
            print(f"❌ ERROR in {test_name}: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The tool should work correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
