#!/usr/bin/env python3
"""
Test script for Qdrant Cloud Integration
Tests all RAG tools with cloud storage
"""

import os
import sys
import json
import tempfile
from pathlib import Path

# Add the tools directory to Python path
sys.path.append(str(Path(__file__).parent / "tools"))

def test_qdrant_connection():
    """Test basic Qdrant cloud connection."""
    print("🔍 Testing Qdrant Cloud Connection...")
    
    try:
        from tools.rag_tools import get_rag_system
        
        rag = get_rag_system()
        storage_info = rag.get_storage_info()
        print(f"✅ Storage Info: {storage_info}")
        
        # Test listing collections
        collections = rag.list_collections()
        print(f"✅ Collections found: {collections}")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_collection_operations():
    """Test collection creation and management."""
    print("\n🔍 Testing Collection Operations...")
    
    try:
        from tools.rag_tools import get_rag_system
        
        rag = get_rag_system()
        test_collection = "test_collection_cloud"
        
        # Create collection
        rag.create_collection(test_collection)
        print(f"✅ Created collection: {test_collection}")
        
        # List collections
        collections = rag.list_collections()
        if test_collection in collections:
            print(f"✅ Collection listed: {test_collection}")
        else:
            print(f"❌ Collection not found in list: {collections}")
            return False
        
        # Delete collection
        result = rag.delete_collection(test_collection)
        print(f"✅ Delete result: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Collection operations failed: {e}")
        return False

def create_test_api_spec():
    """Create a simple test API specification."""
    test_spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "Test API",
            "version": "1.0.0",
            "description": "Test API for Qdrant cloud testing"
        },
        "paths": {
            "/users": {
                "get": {
                    "summary": "Get users",
                    "operationId": "getUsers",
                    "responses": {
                        "200": {
                            "description": "Successful response",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/UserList"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "components": {
            "schemas": {
                "User": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "integer",
                            "description": "User ID"
                        },
                        "name": {
                            "type": "string",
                            "description": "User name"
                        },
                        "email": {
                            "type": "string",
                            "description": "User email"
                        },
                        "created_at": {
                            "type": "string",
                            "format": "date-time",
                            "description": "Creation timestamp"
                        }
                    },
                    "required": ["id", "name", "email"]
                },
                "UserList": {
                    "type": "array",
                    "items": {
                        "$ref": "#/components/schemas/User"
                    }
                }
            }
        }
    }
    
    return test_spec

def test_upload_and_query():
    """Test uploading API spec and querying."""
    print("\n🔍 Testing Upload and Query...")
    
    try:
        from tools.rag_tools import get_rag_system, upload_openapi_spec_to_rag, retrieve_from_rag
        
        rag = get_rag_system()
        test_collection = "test_api_cloud"
        
        # Create test API spec file
        test_spec = create_test_api_spec()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_spec, f)
            temp_file = f.name
        
        try:
            # Upload spec
            print("📤 Uploading test API spec...")
            upload_result = upload_openapi_spec_to_rag(temp_file, test_collection)
            print(f"✅ Upload result: {upload_result}")
            
            # Test query
            print("🔍 Testing query...")
            query_result = retrieve_from_rag("user properties", test_collection, limit=3)
            print(f"✅ Query result: {query_result[:200]}...")
            
            # Test field analysis
            print("🔍 Testing field analysis...")
            from tools.rag_tools import analyze_fields_with_rag_and_llm
            analysis_result = analyze_fields_with_rag_and_llm(
                ["id", "name", "email"], 
                test_collection, 
                "user management"
            )
            print(f"✅ Analysis result: {analysis_result[:200]}...")
            
            return True
            
        finally:
            # Cleanup
            os.unlink(temp_file)
            rag.delete_collection(test_collection)
            print(f"🧹 Cleaned up test collection: {test_collection}")
        
    except Exception as e:
        print(f"❌ Upload and query failed: {e}")
        return False

def test_environment_variables():
    """Test environment variable configuration."""
    print("\n🔍 Testing Environment Variables...")
    
    required_vars = ['QDRANT_URL', 'QDRANT_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask the API key for security
            if 'API_KEY' in var:
                masked_value = value[:10] + "..." + value[-4:]
                print(f"✅ {var}: {masked_value}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: Not set")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Missing environment variables: {missing_vars}")
        return False
    
    return True

def test_llm_integration():
    """Test LLM integration for field analysis."""
    print("\n🔍 Testing LLM Integration...")
    
    try:
        from tools.llm_client import get_llm_response
        
        test_prompt = "What is the purpose of an 'id' field in an API?"
        response = get_llm_response(test_prompt, max_tokens=100)
        
        if response and len(response) > 10:
            print(f"✅ LLM response received: {response[:100]}...")
            return True
        else:
            print(f"❌ LLM response too short: {response}")
            return False
            
    except Exception as e:
        print(f"❌ LLM integration failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Starting Qdrant Cloud Integration Tests\n")
    
    tests = [
        ("Environment Variables", test_environment_variables),
        ("Qdrant Connection", test_qdrant_connection),
        ("Collection Operations", test_collection_operations),
        ("LLM Integration", test_llm_integration),
        ("Upload and Query", test_upload_and_query),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print(f"{'='*50}")
        
        try:
            success = test_func()
            results.append((test_name, success))
            
            if success:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
                
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print(f"{'='*50}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Qdrant Cloud integration is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    exit(main())
