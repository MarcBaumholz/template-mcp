#!/usr/bin/env python3
"""
Simple test for get_direct_api_mapping_prompt function
Tests the function directly without MCP server dependencies
"""

import os
import sys
import json

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_direct_mapping():
    """Test the get_direct_api_mapping_prompt function directly"""
    print("🧪 Testing get_direct_api_mapping_prompt function...")
    
    try:
        from tools.api_spec_getter import get_direct_api_mapping_prompt
        
        # Test parameters from the error
        api_spec_path = "/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/test_temp_stackone/absences-stackone/backend/src/main/resources/openapi-definitions/stackone/api_stackone.json"
        analysis_md_path = "/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/stackone_temp_aug/clean_analysis_20250821_115102.md"
        
        print(f"📁 Testing with files:")
        print(f"   API spec: {api_spec_path}")
        print(f"   Analysis: {analysis_md_path}")
        
        # Check if files exist
        if not os.path.exists(api_spec_path):
            print(f"❌ API spec file not found")
            return False
            
        if not os.path.exists(analysis_md_path):
            print(f"❌ Analysis file not found")
            return False
        
        print(f"✅ Files exist")
        print(f"   API spec: {os.path.getsize(api_spec_path)} bytes")
        print(f"   Analysis: {os.path.getsize(analysis_md_path)} bytes")
        
        # Call the function
        print("🔄 Calling get_direct_api_mapping_prompt...")
        result = get_direct_api_mapping_prompt(api_spec_path, analysis_md_path)
        
        if result.startswith("❌"):
            print(f"❌ Function returned error: {result}")
            return False
        
        print(f"✅ Function call successful!")
        print(f"   Result length: {len(result)} characters")
        print(f"   First 200 chars: {result[:200]}...")
        
        # Save result to file for inspection
        output_file = "test_direct_mapping_result.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result)
        
        print(f"💾 Result saved to: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_error_handling():
    """Test error handling with invalid inputs"""
    print("\n🧪 Testing error handling...")
    
    try:
        from tools.api_spec_getter import get_direct_api_mapping_prompt
        
        # Test with non-existent files
        result = get_direct_api_mapping_prompt("nonexistent.json", "nonexistent.md")
        if not result.startswith("❌"):
            print(f"❌ Expected error for non-existent files")
            return False
        
        print("✅ Error handling works for non-existent files")
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def main():
    """Run the tests"""
    print("🚀 Testing get_direct_api_mapping_prompt function")
    print("=" * 50)
    
    # Test 1: Direct function call
    success1 = test_direct_mapping()
    
    # Test 2: Error handling
    success2 = test_error_handling()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS")
    print("=" * 50)
    print(f"Direct function call: {'✅ PASSED' if success1 else '❌ FAILED'}")
    print(f"Error handling: {'✅ PASSED' if success2 else '❌ FAILED'}")
    
    overall_success = success1 and success2
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    if overall_success:
        print("\n🎉 The function works correctly!")
        print("💡 The 'Connection closed' error is likely due to MCP server issues, not the function itself.")
        print("🔧 To fix the MCP server, ensure 'fastmcp' is installed: pip install fastmcp")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
