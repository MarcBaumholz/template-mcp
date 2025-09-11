#!/usr/bin/env python3
"""
Test script for the fixed enhanced_rag_analysis tool
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_enhanced_rag_analysis():
    """Test the enhanced_rag_analysis function directly"""
    print("🧪 Testing enhanced_rag_analysis function...")
    
    try:
        from tools.phase1_data_extraction.analyze_fields_tool import analyze_fields_with_rag_and_llm
        
        # Test fields from the image
        test_fields = [
            "employee_external_id",
            "absence_type_external_id", 
            "status",
            "start_date",
            "end_date",
            "start_half_day",
            "end_half_day",
            "amount",
            "unit",
            "employee_note"
        ]
        
        print(f"🔄 Calling enhanced_rag_analysis with {len(test_fields)} fields...")
        result = analyze_fields_with_rag_and_llm(
            fields=test_fields,
            collection_name="flip_api_v2",
            context_topic="absence creation request mapping",
            current_path="/tmp/test_enhanced_analysis"
        )
        
        print("✅ Enhanced RAG analysis completed successfully!")
        print(f"📊 Result length: {len(result)} characters")
        print(f"📄 Result preview: {result[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced RAG analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_server_tool():
    """Test the enhanced_rag_analysis tool through the server"""
    print("\n🧪 Testing enhanced_rag_analysis through server...")
    
    try:
        from server_fast import enhanced_rag_analysis
        
        # Test fields from the image
        test_fields = [
            "employee_external_id",
            "absence_type_external_id", 
            "status",
            "start_date",
            "end_date",
            "start_half_day",
            "end_half_day",
            "amount",
            "unit",
            "employee_note"
        ]
        
        print(f"🔄 Calling server enhanced_rag_analysis with {len(test_fields)} fields...")
        result = enhanced_rag_analysis(
            fields_to_analyze=test_fields,
            collection_name="flip_api_v2",
            context_topic="absence creation request mapping",
            current_path="/tmp/test_enhanced_analysis"
        )
        
        print("✅ Server enhanced_rag_analysis completed successfully!")
        print(f"📊 Result length: {len(result)} characters")
        print(f"📄 Result preview: {result[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Server enhanced_rag_analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Enhanced RAG Analysis Test")
    print("=" * 50)
    
    # Test direct function
    success1 = test_enhanced_rag_analysis()
    
    # Test server tool
    success2 = test_server_tool()
    
    print("\n" + "=" * 50)
    if success1 and success2:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
        sys.exit(1)
