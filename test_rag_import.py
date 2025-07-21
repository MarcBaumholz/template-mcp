#!/usr/bin/env python3
"""
Test script to verify RAG tools imports work correctly
"""

import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_rag_imports():
    """Test that all RAG tool imports work correctly."""
    try:
        # Test individual function imports
        from tools.rag_tools import test_rag_system
        print("✅ test_rag_system imported successfully")
        
        from tools.rag_tools import list_rag_collections
        print("✅ list_rag_collections imported successfully")
        
        from tools.rag_tools import upload_openapi_spec_to_rag
        print("✅ upload_openapi_spec_to_rag imported successfully")
        
        from tools.rag_tools import retrieve_from_rag
        print("✅ retrieve_from_rag imported successfully")
        
        from tools.rag_tools import delete_rag_collection
        print("✅ delete_rag_collection imported successfully")
        
        from tools.rag_tools import analyze_fields_with_rag_and_llm
        print("✅ analyze_fields_with_rag_and_llm imported successfully")
        
        # Test RAGTools class import
        from tools.rag_tools import RAGTools
        print("✅ RAGTools class imported successfully")
        
        # Test instantiation
        rag_tools = RAGTools()
        print("✅ RAGTools instance created successfully")
        
        print("\n🎉 All RAG tool imports working correctly!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_server_imports():
    """Test that server imports work correctly."""
    try:
        # Test server import
        import server_fast
        print("✅ server_fast imported successfully")
        
        # Test specific functions exist
        assert hasattr(server_fast, 'test_rag_system')
        print("✅ test_rag_system function exists in server_fast")
        
        assert hasattr(server_fast, 'list_available_api_specs')
        print("✅ list_available_api_specs function exists in server_fast")
        
        assert hasattr(server_fast, 'upload_api_specification')
        print("✅ upload_api_specification function exists in server_fast")
        
        print("\n🎉 Server imports working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Server import error: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing RAG tool imports...")
    print("=" * 50)
    
    rag_success = test_rag_imports()
    print("\n" + "=" * 50)
    
    server_success = test_server_imports()
    print("\n" + "=" * 50)
    
    if rag_success and server_success:
        print("✅ All tests passed! The RAG tools are working correctly.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1) 