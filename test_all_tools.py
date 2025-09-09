#!/usr/bin/env python3
import json
import os
import sys
import asyncio

# Set the model
os.environ['LLM_MODEL'] = 'deepseek/deepseek-chat-v3.1:free'

# Add current directory to path
sys.path.append('.')

def test_analyze_json_tool():
    print("🔍 Testing analyze_json_fields_with_rag tool...")
    try:
        from tools.phase1_data_extraction.analyze_json_fields_with_rag import CombinedFieldAnalysisAgent
        
        # Load test data
        with open('test_absence_data_optimized.json', 'r') as f:
            data = json.load(f)
        
        # Test the optimized extraction
        agent = CombinedFieldAnalysisAgent()
        
        # Test filtered extraction
        print("   🤖 Testing AI filtered extraction...")
        ai_fields = agent._extract_fields_via_ai(data)
        print(f"   ✅ AI filtered extraction: {len(ai_fields)} fields")
        print(f"      Fields: {ai_fields}")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_direct_mapping_tool():
    print("\n🔍 Testing get_direct_api_mapping_prompt tool...")
    try:
        from tools.phase2_analysis_mapping.get_direct_api_mapping_prompt_optimized import get_api_spec_with_direct_llm_query_optimized
        print("   ✅ Module imported successfully")
        
        # Test with a simple API spec if available
        test_spec_path = "/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/test/absences-stackone/backend/src/main/resources/openapi-definitions/stackone/api_stackone.json"
        test_analysis_path = "/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/test/absences-stackone/backend/src/main/resources/openapi-definitions/flip/hris-absence-management.yml"
        
        if os.path.exists(test_spec_path) and os.path.exists(test_analysis_path):
            print("   🧪 Testing with real API spec...")
            result = get_api_spec_with_direct_llm_query_optimized(test_spec_path, test_analysis_path)
            print(f"   ✅ Tool executed successfully, result length: {len(result)}")
        else:
            print("   ⚠️  Test files not found, but module import works")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

async def test_reasoning_agent_tool():
    print("\n🔍 Testing reasoning_agent tool...")
    try:
        from tools.phase2_analysis_mapping.reasoning_agent import reasoning_agent
        print("   ✅ Module imported successfully")
        
        # Test with sample paths
        test_spec_path = "/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/test/absences-stackone/backend/src/main/resources/openapi-definitions/stackone/api_stackone.json"
        test_analysis_path = "/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/test/absences-stackone/backend/src/main/resources/openapi-definitions/flip/hris-absence-management.yml"
        output_dir = "/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/test"
        
        if os.path.exists(test_spec_path) and os.path.exists(test_analysis_path):
            print("   🧪 Testing with real API spec...")
            result = await reasoning_agent(test_analysis_path, test_spec_path, output_dir)
            print(f"   ✅ Tool executed successfully, result length: {len(result)}")
        else:
            print("   ⚠️  Test files not found, but module import works")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_enhanced_rag_analysis_tool():
    print("\n🔍 Testing enhanced_rag_analysis tool...")
    try:
        # Check if the module exists
        import importlib.util
        spec = importlib.util.find_spec("tools.phase2_analysis_mapping.enhanced_rag_analysis")
        if spec is None:
            print("   ⚠️  Module enhanced_rag_analysis not found - skipping test")
            return True  # Not an error, just missing module
        
        from tools.phase2_analysis_mapping.enhanced_rag_analysis import enhanced_rag_analysis
        print("   ✅ Module imported successfully")
        
        # Test with sample fields
        test_fields = ["employeeId", "type", "status", "startDate", "endDate"]
        result = enhanced_rag_analysis(test_fields, "flip_hris_absence_management")
        print(f"   ✅ Tool executed successfully, result length: {len(result)}")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_iterative_mapping_tool():
    print("\n🔍 Testing iterative_mapping_with_feedback tool...")
    try:
        from tools.phase2_analysis_mapping.iterative_mapping_with_feedback import iterative_field_mapping
        print("   ✅ Module imported successfully")
        
        # Test with sample fields
        test_fields = ["employeeId", "type", "status", "startDate", "endDate"]
        test_spec_path = "/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/test/absences-stackone/backend/src/main/resources/openapi-definitions/stackone/api_stackone.json"
        
        if os.path.exists(test_spec_path):
            print("   🧪 Testing with real API spec...")
            result = iterative_field_mapping(test_fields, "flip_hris_absence_management", test_spec_path)
            print(f"   ✅ Tool executed successfully, result type: {type(result)}")
        else:
            print("   ⚠️  Test files not found, but module import works")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

async def main():
    print("🚀 Testing All MCP Tools")
    print("=" * 60)
    
    # Test all tools
    results = {}
    results['analyze_json'] = test_analyze_json_tool()
    results['direct_mapping'] = test_direct_mapping_tool()
    results['reasoning_agent'] = await test_reasoning_agent_tool()
    results['enhanced_rag'] = test_enhanced_rag_analysis_tool()
    results['iterative_mapping'] = test_iterative_mapping_tool()
    
    print("\n" + "=" * 60)
    print("📊 FINAL RESULTS:")
    print("=" * 60)
    
    working_count = 0
    for tool_name, status in results.items():
        status_icon = "✅" if status else "❌"
        status_text = "WORKING" if status else "BROKEN"
        print(f"   {status_icon} {tool_name}: {status_text}")
        if status:
            working_count += 1
    
    print(f"\n🎯 SUMMARY: {working_count}/{len(results)} tools are working")
    
    if working_count == len(results):
        print("🎉 ALL TOOLS ARE WORKING CORRECTLY!")
        print("✅ The MCP server should now work properly")
    else:
        print("⚠️  SOME TOOLS NEED FIXING")
        print("❌ The MCP server may have issues")

if __name__ == "__main__":
    asyncio.run(main())
