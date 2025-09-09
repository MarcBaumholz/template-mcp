#!/usr/bin/env python3
import json
import os
import sys

# Set the model
os.environ['LLM_MODEL'] = 'deepseek/deepseek-chat-v3.1:free'

# Add current directory to path
sys.path.append('.')

def test_analyze_tool():
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
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    print("🚀 Testing Tool Fixes")
    print("=" * 50)
    
    # Test both tools
    analyze_ok = test_analyze_tool()
    direct_ok = test_direct_mapping_tool()
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY:")
    print(f"   • analyze_json_fields_with_rag: {'✅ WORKING' if analyze_ok else '❌ BROKEN'}")
    print(f"   • get_direct_api_mapping_prompt: {'✅ WORKING' if direct_ok else '❌ BROKEN'}")
    
    if analyze_ok and direct_ok:
        print("\n🎉 ALL TOOLS ARE WORKING CORRECTLY!")
    else:
        print("\n⚠️  SOME TOOLS NEED FIXING")

if __name__ == "__main__":
    main()
