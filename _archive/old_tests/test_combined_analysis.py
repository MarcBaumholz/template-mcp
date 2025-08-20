#!/usr/bin/env python3
"""
Test script for the new combined JSON analysis tool
"""

import json
import asyncio
import tempfile
import os
from pathlib import Path

# Test JSON data for HR/Absence Management
test_json_data = {
    "employee": {
        "id": "EMP001",
        "firstName": "Max",
        "lastName": "Mustermann",
        "email": "max.mustermann@company.com",
        "department": "Engineering"
    },
    "absence": {
        "id": "ABS001",
        "type": "vacation",
        "startDate": "2025-01-15",
        "endDate": "2025-01-25",
        "status": "approved",
        "reason": "Annual vacation",
        "totalDays": 10
    },
    "request": {
        "submittedBy": "EMP001",
        "submittedAt": "2025-01-01T10:00:00Z",
        "approvedBy": "MGR001",
        "approvedAt": "2025-01-02T14:30:00Z"
    },
    "metadata": {
        "source": "HRIS_System",
        "version": "1.0",
        "timestamp": "2025-01-22T11:38:00Z"
    }
}

async def test_combined_analysis():
    """Test the combined JSON analysis tool."""
    
    # Create temporary JSON file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_json_data, f, indent=2)
        temp_json_path = f.name
    
    try:
        print("🧪 Testing combined JSON analysis tool")
        print(f"📄 Test JSON file: {temp_json_path}")
        print("-" * 60)
        
        # Import the tool
        from tools.json_tool.combined_analysis_agent import CombinedFieldAnalysisAgent
        
        # Create agent
        agent = CombinedFieldAnalysisAgent()
        print("✅ Agent successfully created")
        
        # Execute combined analysis
        result = await agent.process_json_with_combined_analysis(
            json_data=test_json_data,
            json_file_path=temp_json_path,
            current_directory=os.getcwd(),
            collection_name="flip_api_v2"
        )
        
        print(f"📊 Analysis status: {result.status}")
        print(f"🤖 Agent: {result.agent_name}")
        
        if result.status == "error":
            print(f"❌ Error: {result.error}")
        else:
            print(f"✅ Success!")
            print(f"📋 Extracted fields: {len(result.result.extracted_fields)}")
            print(f"🎯 Confidence: {result.result.confidence_score:.2f}")
            print(f"📝 Status: {result.result.validation_status}")
            
            print("\n🔍 Extracted fields:")
            # extracted_fields is now a dictionary
            field_items = list(result.result.extracted_fields.items())[:10]  # First 10 fields
            for i, (field_name, field_value) in enumerate(field_items, 1):
                print(f"  {i}. {field_name}: {str(field_value)[:50]}...")
            
            if len(result.result.extracted_fields) > 10:
                print(f"  ... and {len(result.result.extracted_fields) - 10} more")
            
            print(f"\n📄 Complete analysis:\n{result.result.context[:500]}...")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        try:
            os.unlink(temp_json_path)
            print(f"🧹 Temporary file deleted: {temp_json_path}")
        except:
            pass

def test_field_extraction():
    """Test only field extraction - DEACTIVATED as it's now orchestrated."""
    print("\n🧪 Testing field extraction separately - SKIPPED")
    print("-" * 60)
    print("ℹ️  Field extraction is now orchestrated via existing tools")
    print("✅ Test skipped - use the full test instead")

async def main():
    """Main test function."""
    print("🚀 Starting tests for combined JSON analysis tool")
    print("=" * 60)
    
    # Test 1: Field extraction
    test_field_extraction()
    
    # Test 2: Complete analysis (if RAG is available)
    try:
        await test_combined_analysis()
    except Exception as e:
        print(f"⚠️ Complete test skipped (RAG possibly not available): {e}")
    
    print("\n🎉 Tests completed!")

if __name__ == "__main__":
    asyncio.run(main()) 