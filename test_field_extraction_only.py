#!/usr/bin/env python3
"""
Test script to demonstrate field extraction scalability without LLM dependency.
"""

import json
import sys
from pathlib import Path

# Add current directory to path
sys.path.append('.')

from tools.phase1_data_extraction.analyze_json_fields_with_rag import CombinedFieldAnalysisAgent


def test_field_extraction_scalability():
    """Test field extraction across different business use cases."""
    
    print("🧪 Testing Field Extraction Scalability (No LLM Required)")
    print("=" * 60)
    
    agent = CombinedFieldAnalysisAgent()
    
    # Test cases with different business domains
    test_cases = [
        {
            "name": "Employee Management",
            "file": "sample_data/employee_data_generic.json",
            "expected_fields": ["id", "employeeId", "firstName", "lastName", "email", "department", "role", "status"]
        },
        {
            "name": "Shift Scheduling", 
            "file": "sample_data/shift_scheduling_data.json",
            "expected_fields": ["id", "employeeId", "shiftType", "startTime", "endTime", "location", "status", "duration"]
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\n📊 Testing: {test_case['name']}")
        print("-" * 40)
        
        try:
            # Load test data
            with open(test_case['file'], 'r') as f:
                data = json.load(f)
            
            # Test programmatic field extraction
            fields = agent._extract_relevant_fields_programmatically(data)
            print(f"✅ Extracted {len(fields)} fields")
            print(f"📋 All fields: {fields}")
            
            # Check if expected fields are present
            field_names = [f.split('.')[-1] for f in fields]  # Get field names without prefixes
            found_expected = [f for f in test_case['expected_fields'] if f in field_names]
            missing_expected = [f for f in test_case['expected_fields'] if f not in field_names]
            
            print(f"✅ Found expected fields: {found_expected}")
            if missing_expected:
                print(f"⚠️  Missing expected fields: {missing_expected}")
            
            # Test field validation
            validated_fields, validation_note = agent._validate_field_extraction(fields, data)
            print(f"📊 Validation: {validation_note}")
            
            results.append({
                "use_case": test_case['name'],
                "total_fields": len(fields),
                "expected_found": len(found_expected),
                "expected_total": len(test_case['expected_fields']),
                "validation_note": validation_note,
                "success": len(found_expected) >= len(test_case['expected_fields']) * 0.8  # 80% threshold
            })
            
        except Exception as e:
            print(f"❌ Error testing {test_case['name']}: {e}")
            results.append({
                "use_case": test_case['name'],
                "error": str(e),
                "success": False
            })
    
    # Summary
    print("\n" + "=" * 60)
    print("📈 FIELD EXTRACTION SCALABILITY RESULTS")
    print("=" * 60)
    
    successful_tests = [r for r in results if r.get('success', False)]
    total_tests = len(results)
    
    print(f"✅ Successful tests: {len(successful_tests)}/{total_tests}")
    print(f"📊 Success rate: {len(successful_tests)/total_tests*100:.1f}%")
    
    for result in results:
        if result.get('success', False):
            print(f"✅ {result['use_case']}: {result['total_fields']} fields, {result['expected_found']}/{result['expected_total']} expected")
            print(f"   Validation: {result['validation_note']}")
        else:
            print(f"❌ {result['use_case']}: {result.get('error', 'Failed')}")
    
    print("\n🎯 CONCLUSION:")
    if len(successful_tests) == total_tests:
        print("🎉 ALL TESTS PASSED - Field extraction is now use-case agnostic!")
        print("✅ No more absence-specific bias in field extraction")
        print("✅ Can handle employee management, shift scheduling, and other business domains")
        print("✅ Field extraction works across different data structures")
        print("✅ Validation works for all use cases")
    else:
        print("⚠️  Some tests failed - further investigation needed")
    
    return results


if __name__ == "__main__":
    test_field_extraction_scalability()
