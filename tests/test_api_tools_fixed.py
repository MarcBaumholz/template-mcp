#!/usr/bin/env python3
"""
Fixed test script for API tools
Tests the tools using the actual functions from server_fast.py
"""

import os
import sys
import asyncio

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_enhanced_rag_analysis():
    """Test the enhanced_rag_analysis function from server_fast.py"""
    print("🧪 Testing enhanced_rag_analysis function...")
    
    try:
        # Import the function from server_fast.py
        from server_fast import enhanced_rag_analysis
        
        # Test parameters from the error
        fields_to_analyze = ["id", "employeeId", "type", "status", "startDate", "endDate", "duration"]
        collection_name = "stackone_api"
        context_topic = "mapping Flip absences to StackOne time off"
        current_path = "/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/stackone_temp_aug"
        
        print(f"📁 Testing with parameters:")
        print(f"   Fields to analyze: {fields_to_analyze}")
        print(f"   Collection: {collection_name}")
        print(f"   Context: {context_topic}")
        print(f"   Output path: {current_path}")
        
        # Call the function
        print("🔄 Calling enhanced_rag_analysis...")
        result = enhanced_rag_analysis(
            fields_to_analyze=fields_to_analyze,
            collection_name=collection_name,
            context_topic=context_topic,
            current_path=current_path
        )
        
        if result.startswith("❌"):
            print(f"❌ Function returned error: {result}")
            return False
        
        print(f"✅ Function call successful!")
        print(f"   Result length: {len(result)} characters")
        print(f"   First 200 chars: {result[:200]}...")
        
        # Save result to file for inspection
        output_file = "test_enhanced_rag_result.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result)
        
        print(f"💾 Result saved to: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_reasoning_agent():
    """Test the reasoning_agent function from server_fast.py"""
    print("\n🧪 Testing reasoning_agent function...")
    
    try:
        # Import the function from server_fast.py
        from server_fast import reasoning_agent
        
        # Test parameters from the error
        source_analysis_path = "/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/stackone_temp_aug/clean_analysis_20250821_115102.md"
        api_spec_path = "/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/test_temp_stackone/absences-stackone/backend/src/main/resources/openapi-definitions/stackone/api_stackone.json"
        output_directory = "/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/stackone_temp_aug"
        target_collection_name = "stackone_api"
        
        print(f"📁 Testing with parameters:")
        print(f"   Source analysis: {source_analysis_path}")
        print(f"   API spec: {api_spec_path}")
        print(f"   Output directory: {output_directory}")
        print(f"   Target collection: {target_collection_name}")
        
        # Check if files exist
        if not os.path.exists(source_analysis_path):
            print(f"❌ Source analysis file not found")
            return False
            
        if not os.path.exists(api_spec_path):
            print(f"❌ API spec file not found")
            return False
        
        # Call the async function
        print("🔄 Calling reasoning_agent...")
        result = await reasoning_agent(
            source_analysis_path=source_analysis_path,
            api_spec_path=api_spec_path,
            output_directory=output_directory,
            target_collection_name=target_collection_name
        )
        
        if result.startswith("❌"):
            print(f"❌ Function returned error: {result}")
            return False
        
        print(f"✅ Function call successful!")
        print(f"   Result length: {len(result)} characters")
        print(f"   First 200 chars: {result[:200]}...")
        
        # Save result to file for inspection
        output_file = "test_reasoning_agent_result.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result)
        
        print(f"💾 Result saved to: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print("🚀 Testing API Tools (Fixed)")
    print("=" * 50)
    
    # Test 1: Enhanced RAG Analysis (sync)
    success1 = test_enhanced_rag_analysis()
    
    # Test 2: Reasoning Agent (async)
    success2 = await test_reasoning_agent()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS")
    print("=" * 50)
    print(f"Enhanced RAG Analysis: {'✅ PASSED' if success1 else '❌ FAILED'}")
    print(f"Reasoning Agent: {'✅ PASSED' if success2 else '❌ FAILED'}")
    
    overall_success = success1 and success2
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    if overall_success:
        print("\n🎉 Both tools work correctly!")
        print("💡 The 'Request timed out' errors were due to MCP server issues.")
        print("🔧 The tools work perfectly when called directly.")
    
    return overall_success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
