#!/usr/bin/env python3
"""
Test script for API Specification Verifier MCP Tool
Demonstrates usage with real examples and different verification types
"""

import json
import os
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tools.api_spec_verifier import verify_api_specification


def test_fast_verification():
    """Test fast verification (pattern matching only)."""
    print("🧪 Testing Fast Verification (Pattern Matching Only)")
    print("=" * 60)
    
    # Sample field mappings to verify
    field_mappings = {
        "employee_id": "employeeId",
        "start_date": "startDate",
        "end_date": "endDate",
        "status": "status",
        "type": "type",
        "duration": "duration"
    }
    
    # Example API spec path (you would replace this with your actual spec)
    api_spec_path = "sample_data/sample_hr_api.json"
    
    try:
        result = verify_api_specification(
            api_spec_path=api_spec_path,
            field_mappings=json.dumps(field_mappings),
            verification_type="fast",
            output_format="markdown"
        )
        
        print("✅ Fast verification completed successfully!")
        print("\n📊 Results:")
        print(result)
        
    except Exception as e:
        print(f"❌ Fast verification failed: {e}")
        print("💡 Make sure the API spec file exists and is valid JSON/YAML")


def test_semantic_verification():
    """Test semantic verification (RAG-enhanced)."""
    print("\n🧪 Testing Semantic Verification (RAG-enhanced)")
    print("=" * 60)
    
    # Unknown field mappings to discover
    unknown_mappings = {
        "worker_identifier": "?",
        "absence_start": "?",
        "absence_end": "?",
        "leave_category": "?",
        "approval_workflow": "?"
    }
    
    api_spec_path = "sample_data/sample_hr_api.json"
    
    try:
        result = verify_api_specification(
            api_spec_path=api_spec_path,
            field_mappings=json.dumps(unknown_mappings),
            verification_type="semantic",
            output_format="markdown"
        )
        
        print("✅ Semantic verification completed successfully!")
        print("\n📊 Results:")
        print(result)
        
    except Exception as e:
        print(f"❌ Semantic verification failed: {e}")
        print("💡 Make sure RAG system is set up and API spec is available")


def test_comprehensive_verification():
    """Test comprehensive verification (both pattern and semantic)."""
    print("\n🧪 Testing Comprehensive Verification (Pattern + Semantic)")
    print("=" * 60)
    
    # Mixed field mappings
    comprehensive_mappings = {
        "employee_id": "employeeId",
        "start_date": "startDate",
        "end_date": "endDate",
        "status": "status",
        "type": "type",
        "duration": "duration",
        "created_date": "createdDate",
        "updated_date": "updatedDate",
        "approver_id": "approverId",
        "reason": "reason",
        "worker_identifier": "?",  # Unknown field for semantic discovery
        "absence_start": "?"       # Unknown field for semantic discovery
    }
    
    api_spec_path = "sample_data/sample_hr_api.json"
    
    try:
        result = verify_api_specification(
            api_spec_path=api_spec_path,
            field_mappings=json.dumps(comprehensive_mappings),
            verification_type="comprehensive",
            output_format="json"
        )
        
        print("✅ Comprehensive verification completed successfully!")
        print("\n📊 Results (JSON format):")
        
        # Parse and display key metrics
        try:
            data = json.loads(result)
            print(f"📈 Total Fields: {data.get('total_fields', 'N/A')}")
            print(f"✅ Verified Fields: {data.get('verified_fields', 'N/A')}")
            print(f"❌ Unverified Fields: {data.get('unverified_fields', 'N/A')}")
            print(f"🎯 Confidence Score: {data.get('confidence_score', 'N/A'):.2f}")
            
            if 'recommendations' in data:
                print("\n💡 Recommendations:")
                for rec in data['recommendations']:
                    print(f"  - {rec}")
                    
        except json.JSONDecodeError:
            print(result)  # Display raw result if not JSON
            
    except Exception as e:
        print(f"❌ Comprehensive verification failed: {e}")


def test_json_output_format():
    """Test JSON output format for programmatic processing."""
    print("\n🧪 Testing JSON Output Format")
    print("=" * 60)
    
    field_mappings = {
        "employee_id": "employeeId",
        "start_date": "startDate",
        "end_date": "endDate",
        "status": "status",
        "type": "type"
    }
    
    api_spec_path = "sample_data/sample_hr_api.json"
    
    try:
        result = verify_api_specification(
            api_spec_path=api_spec_path,
            field_mappings=json.dumps(field_mappings),
            verification_type="fast",
            output_format="json"
        )
        
        print("✅ JSON output format test completed!")
        
        # Parse and validate JSON structure
        data = json.loads(result)
        required_fields = ['timestamp', 'total_fields', 'verified_fields', 'confidence_score']
        
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            print(f"❌ Missing required fields: {missing_fields}")
        else:
            print("✅ JSON structure is valid")
            print(f"📊 Success rate: {data['verified_fields']}/{data['total_fields']} ({data['verified_fields']/data['total_fields']*100:.1f}%)")
            
    except Exception as e:
        print(f"❌ JSON output test failed: {e}")


def test_field_normalization():
    """Test field normalization capabilities."""
    print("\n🧪 Testing Field Normalization")
    print("=" * 60)
    
    # Fields that should be normalized to common patterns
    normalized_mappings = {
        "worker_identifier": "?",      # Should match employee_id
        "absence_start": "?",          # Should match start_date
        "absence_end": "?",            # Should match end_date
        "leave_category": "?",         # Should match type
        "approval_workflow": "?",      # Should match status
        "time_span": "?",              # Should match duration
        "created_at": "?",             # Should match created_date
        "modified_at": "?"             # Should match updated_date
    }
    
    api_spec_path = "sample_data/sample_hr_api.json"
    
    try:
        result = verify_api_specification(
            api_spec_path=api_spec_path,
            field_mappings=json.dumps(normalized_mappings),
            verification_type="comprehensive",
            output_format="markdown"
        )
        
        print("✅ Field normalization test completed!")
        print("\n📊 Results:")
        print(result)
        
    except Exception as e:
        print(f"❌ Field normalization test failed: {e}")


def test_error_handling():
    """Test error handling for invalid inputs."""
    print("\n🧪 Testing Error Handling")
    print("=" * 60)
    
    # Test with non-existent API spec
    print("Testing with non-existent API spec...")
    try:
        result = verify_api_specification(
            api_spec_path="/path/to/nonexistent/api.json",
            field_mappings=json.dumps({"test": "test"}),
            verification_type="fast"
        )
        print(f"Result: {result}")
    except Exception as e:
        print(f"✅ Correctly handled missing file: {e}")
    
    # Test with invalid JSON
    print("\nTesting with invalid JSON...")
    try:
        result = verify_api_specification(
            api_spec_path="sample_data/sample_hr_api.json",
            field_mappings="invalid json string",
            verification_type="fast"
        )
        print(f"Result: {result}")
    except Exception as e:
        print(f"✅ Correctly handled invalid JSON: {e}")


def create_sample_api_spec():
    """Create a sample API spec for testing if it doesn't exist."""
    sample_spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "Sample HR API",
            "version": "1.0.0"
        },
        "paths": {
            "/unified/hris/time_off": {
                "get": {
                    "operationId": "hris_list_time_off_requests",
                    "parameters": [
                        {
                            "name": "x-account-id",
                            "in": "header",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ]
                }
            }
        },
        "components": {
            "schemas": {
                "TimeOff": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "string",
                            "description": "Unique identifier"
                        },
                        "employee_id": {
                            "type": "string",
                            "description": "The employee ID"
                        },
                        "start_date": {
                            "type": "string",
                            "format": "date-time",
                            "description": "The start date of the time off request"
                        },
                        "end_date": {
                            "type": "string",
                            "format": "date-time",
                            "description": "The end date of the time off request"
                        },
                        "status": {
                            "type": "object",
                            "description": "The status of the time off request"
                        },
                        "type": {
                            "type": "object",
                            "description": "The type of the time off request"
                        },
                        "duration": {
                            "type": "string",
                            "description": "The duration of the time off request"
                        },
                        "created_date": {
                            "type": "string",
                            "format": "date-time",
                            "description": "The created date of the time off request"
                        },
                        "updated_date": {
                            "type": "string",
                            "format": "date-time",
                            "description": "The updated date of the time off request"
                        },
                        "approver_id": {
                            "type": "string",
                            "description": "The approver ID"
                        },
                        "reason": {
                            "type": "string",
                            "description": "The reason for the time off request"
                        }
                    },
                    "required": ["employee_id", "start_date", "end_date"]
                }
            }
        }
    }
    
    # Create sample_data directory if it doesn't exist
    sample_data_dir = Path("sample_data")
    sample_data_dir.mkdir(exist_ok=True)
    
    # Write sample API spec
    spec_path = sample_data_dir / "sample_hr_api.json"
    with open(spec_path, 'w') as f:
        json.dump(sample_spec, f, indent=2)
    
    print(f"✅ Created sample API spec at: {spec_path}")
    return str(spec_path)


def main():
    """Run all tests."""
    print("🚀 API Specification Verifier MCP Tool - Test Suite")
    print("=" * 80)
    
    # Create sample API spec if it doesn't exist
    if not Path("sample_data/sample_hr_api.json").exists():
        print("📝 Creating sample API spec for testing...")
        create_sample_api_spec()
    
    # Run all tests
    test_fast_verification()
    test_semantic_verification()
    test_comprehensive_verification()
    test_json_output_format()
    test_field_normalization()
    test_error_handling()
    
    print("\n🎉 All tests completed!")
    print("\n📚 Next Steps:")
    print("1. Review the test results above")
    print("2. Check the generated reports for accuracy")
    print("3. Integrate the tool into your MCP workflow")
    print("4. Use the tool for real API specification verification")


if __name__ == "__main__":
    main()
