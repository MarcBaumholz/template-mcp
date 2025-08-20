#!/usr/bin/env python3
"""
Test script for the Iterative Mapping System with Feedback Loop
"""

import sys
import os
import json
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tools.iterative_mapping import iterative_field_mapping, test_iterative_mapping
from tools.rag_tools import get_rag_system, upload_openapi_spec_to_rag


def test_basic_iterative_mapping():
    """Test basic iterative mapping functionality."""
    print("🧪 Testing Basic Iterative Mapping...")
    
    try:
        # Test with sample fields
        source_fields = ["employee_id", "start_date", "status", "department"]
        target_collection = "test_hr_api"
        api_spec_path = "sample_data/sample_hr_api.json"
        
        print(f"📋 Source Fields: {source_fields}")
        print(f"🎯 Target Collection: {target_collection}")
        print(f"📄 API Spec: {api_spec_path}")
        
        # Check if API spec exists
        if not os.path.exists(api_spec_path):
            print(f"⚠️ API spec not found: {api_spec_path}")
            print("Creating sample API spec for testing...")
            create_sample_api_spec(api_spec_path)
        
        # Perform iterative mapping
        result = iterative_field_mapping(
            source_fields=source_fields,
            target_collection=target_collection,
            api_spec_path=api_spec_path,
            output_path="./test_outputs"
        )
        
        print("\n" + "="*50)
        print("📊 ITERATIVE MAPPING RESULTS")
        print("="*50)
        print(result)
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def test_rag_integration():
    """Test RAG integration with iterative mapping."""
    print("\n🧪 Testing RAG Integration...")
    
    try:
        # Initialize RAG system
        rag_system = get_rag_system()
        
        # Create test collection
        collection_name = "test_iterative_collection"
        rag_system.create_collection(collection_name)
        
        # Upload sample API spec to RAG
        sample_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "Sample HR API",
                "version": "1.0.0"
            },
            "paths": {
                "/employees": {
                    "get": {
                        "summary": "Get employees",
                        "parameters": [
                            {"name": "employee_id", "in": "query", "schema": {"type": "string"}},
                            {"name": "start_date", "in": "query", "schema": {"type": "string"}},
                            {"name": "status", "in": "query", "schema": {"type": "string"}}
                        ]
                    },
                    "post": {
                        "summary": "Create employee",
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "employee_id": {"type": "string"},
                                            "start_date": {"type": "string"},
                                            "status": {"type": "string"},
                                            "department": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        
        # Save sample spec to file
        spec_path = "sample_data/test_spec.json"
        os.makedirs(os.path.dirname(spec_path), exist_ok=True)
        with open(spec_path, 'w') as f:
            json.dump(sample_spec, f, indent=2)
        
        # Upload to RAG
        upload_result = upload_openapi_spec_to_rag(spec_path, collection_name)
        print(f"📤 RAG Upload Result: {upload_result}")
        
        # Test iterative mapping with RAG
        source_fields = ["emp_id", "hire_date", "active_status"]
        result = iterative_field_mapping(
            source_fields=source_fields,
            target_collection=collection_name,
            api_spec_path=spec_path,
            output_path="./test_outputs"
        )
        
        print("\n" + "="*50)
        print("📊 RAG INTEGRATION RESULTS")
        print("="*50)
        print(result)
        
        return True
        
    except Exception as e:
        print(f"❌ RAG integration test failed: {e}")
        return False


def test_live_validation():
    """Test live API validation functionality."""
    print("\n🧪 Testing Live API Validation...")
    
    try:
        # Create a mock API spec for testing
        mock_api_spec = {
            "openapi": "3.0.0",
            "info": {"title": "Mock API", "version": "1.0.0"},
            "servers": [{"url": "http://localhost:8080"}],
            "paths": {
                "/test/employee": {
                    "post": {
                        "summary": "Test employee endpoint",
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "employee_id": {"type": "string"},
                                            "start_date": {"type": "string"},
                                            "status": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        
        # Save mock spec
        mock_spec_path = "sample_data/mock_api.json"
        os.makedirs(os.path.dirname(mock_spec_path), exist_ok=True)
        with open(mock_spec_path, 'w') as f:
            json.dump(mock_api_spec, f, indent=2)
        
        # Test with mock API (will fail but test the validation logic)
        source_fields = ["test_field"]
        result = iterative_field_mapping(
            source_fields=source_fields,
            target_collection="mock_collection",
            api_spec_path=mock_spec_path,
            output_path="./test_outputs"
        )
        
        print("\n" + "="*50)
        print("📊 LIVE VALIDATION TEST RESULTS")
        print("="*50)
        print(result)
        
        return True
        
    except Exception as e:
        print(f"❌ Live validation test failed: {e}")
        return False


def create_sample_api_spec(filepath: str):
    """Create a sample API specification for testing."""
    sample_spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "Sample HR API",
            "version": "1.0.0",
            "description": "A sample HR API for testing iterative mapping"
        },
        "servers": [
            {"url": "http://localhost:8080", "description": "Development server"}
        ],
        "paths": {
            "/employees": {
                "get": {
                    "summary": "Get all employees",
                    "description": "Retrieve a list of all employees",
                    "parameters": [
                        {
                            "name": "employee_id",
                            "in": "query",
                            "description": "Filter by employee ID",
                            "schema": {"type": "string"}
                        },
                        {
                            "name": "start_date",
                            "in": "query",
                            "description": "Filter by start date",
                            "schema": {"type": "string", "format": "date"}
                        },
                        {
                            "name": "status",
                            "in": "query",
                            "description": "Filter by employment status",
                            "schema": {"type": "string", "enum": ["active", "inactive"]}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Successful response",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "employee_id": {"type": "string"},
                                                "start_date": {"type": "string"},
                                                "status": {"type": "string"},
                                                "department": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "post": {
                    "summary": "Create new employee",
                    "description": "Create a new employee record",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["employee_id", "start_date"],
                                    "properties": {
                                        "employee_id": {
                                            "type": "string",
                                            "description": "Unique employee identifier"
                                        },
                                        "start_date": {
                                            "type": "string",
                                            "format": "date",
                                            "description": "Employee start date"
                                        },
                                        "status": {
                                            "type": "string",
                                            "enum": ["active", "inactive"],
                                            "default": "active",
                                            "description": "Employment status"
                                        },
                                        "department": {
                                            "type": "string",
                                            "description": "Employee department"
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Employee created successfully"
                        },
                        "400": {
                            "description": "Bad request - invalid data"
                        }
                    }
                }
            },
            "/employees/{employee_id}": {
                "get": {
                    "summary": "Get employee by ID",
                    "parameters": [
                        {
                            "name": "employee_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Employee found"
                        },
                        "404": {
                            "description": "Employee not found"
                        }
                    }
                }
            }
        }
    }
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # Save the spec
    with open(filepath, 'w') as f:
        json.dump(sample_spec, f, indent=2)
    
    print(f"✅ Created sample API spec: {filepath}")


def main():
    """Run all tests."""
    print("🚀 Starting Iterative Mapping System Tests")
    print("="*60)
    
    # Create output directory
    os.makedirs("./test_outputs", exist_ok=True)
    
    # Run tests
    tests = [
        ("Basic Iterative Mapping", test_basic_iterative_mapping),
        ("RAG Integration", test_rag_integration),
        ("Live Validation", test_live_validation)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Iterative mapping system is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
    
    return passed == len(results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 