#!/usr/bin/env python3
"""
Test script for the fixed analyze_json_fields_with_rag tool
"""

import sys
import json
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_analyze_json_fields():
    """Test the analyze_json_fields_with_rag function via server"""
    print("🧪 Testing analyze_json_fields_with_rag function via server...")
    
    try:
        # Create a test JSON file
        test_json = {
            "employee_external_id": "EMP001",
            "absence_type_external_id": "VACATION",
            "status": "approved",
            "start_date": "2024-01-15",
            "end_date": "2024-01-20",
            "start_half_day": False,
            "end_half_day": False,
            "amount": 5,
            "unit": "days",
            "employee_note": "Family vacation"
        }
        
        test_file = "/tmp/test_webhook.json"
        with open(test_file, 'w') as f:
            json.dump(test_json, f, indent=2)
        
        print(f"🔄 Created test JSON file: {test_file}")
        print("✅ Test setup completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_combined_agent_directly():
    """Test the CombinedFieldAnalysisAgent directly"""
    print("\n🧪 Testing CombinedFieldAnalysisAgent directly...")
    
    try:
        from tools.phase1_data_extraction.analyze_json_fields_with_rag import CombinedFieldAnalysisAgent
        
        # Create test JSON data
        test_json = {
            "employee_external_id": "EMP001",
            "absence_type_external_id": "VACATION",
            "status": "approved",
            "start_date": "2024-01-15",
            "end_date": "2024-01-20"
        }
        
        print("🔄 Initializing CombinedFieldAnalysisAgent...")
        agent = CombinedFieldAnalysisAgent()
        print("✅ Agent initialized successfully!")
        
        print("🔄 Testing field extraction...")
        fields = agent._extract_relevant_fields_programmatically(test_json)
        print(f"✅ Extracted {len(fields)} fields: {fields}")
        
        print("🔄 Testing field description...")
        analysis = agent._describe_fields_via_ai(test_json, fields)
        print(f"✅ Field description completed: {len(analysis)} fields analyzed")
        
        return True
        
    except Exception as e:
        print(f"❌ CombinedFieldAnalysisAgent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Analyze JSON Fields with RAG Test")
    print("=" * 50)
    
    # Test direct agent
    success1 = test_combined_agent_directly()
    
    # Test main function
    success2 = test_analyze_json_fields()
    
    print("\n" + "=" * 50)
    if success1 and success2:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
        sys.exit(1)
