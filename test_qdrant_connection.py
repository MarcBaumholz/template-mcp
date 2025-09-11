#!/usr/bin/env python3
"""
Test script to verify Qdrant connection and authentication
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def test_qdrant_connection():
    """Test Qdrant connection and authentication"""
    print("🔍 Testing Qdrant connection...")
    
    # Check environment variables
    qdrant_url = os.getenv('QDRANT_URL')
    qdrant_api_key = os.getenv('QDRANT_API_KEY')
    
    print(f"QDRANT_URL: {qdrant_url}")
    print(f"QDRANT_API_KEY: {'*' * 20 if qdrant_api_key else 'NOT SET'}")
    
    if not qdrant_url or not qdrant_api_key:
        print("❌ Qdrant environment variables not set!")
        return False
    
    try:
        from qdrant_client import QdrantClient
        
        # Test connection
        print("🔄 Connecting to Qdrant...")
        client = QdrantClient(
            url=qdrant_url,
            api_key=qdrant_api_key
        )
        
        # Test API call
        print("🔄 Testing API call...")
        collections = client.get_collections()
        print(f"✅ Connection successful! Found {len(collections.collections)} collections")
        
        # List collections
        for collection in collections.collections:
            print(f"  - {collection.name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_rag_system():
    """Test the RAG system initialization"""
    print("\n🔍 Testing RAG system...")
    
    try:
        from tools.phase1_data_extraction.analyze_fields_tool import EnhancedRAGSystem
        
        print("🔄 Initializing Enhanced RAG system...")
        rag = EnhancedRAGSystem()
        print("✅ Enhanced RAG system initialized successfully!")
        
        # Test a simple query
        print("🔄 Testing simple query...")
        results = rag.enhanced_query("test query", "flip_api_v2", limit=1)
        print(f"✅ Query successful! Got {len(results)} results")
        
        return True
        
    except Exception as e:
        print(f"❌ RAG system test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Qdrant Connection Test")
    print("=" * 50)
    
    # Test Qdrant connection
    qdrant_ok = test_qdrant_connection()
    
    # Test RAG system
    rag_ok = test_rag_system()
    
    print("\n" + "=" * 50)
    if qdrant_ok and rag_ok:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
        sys.exit(1)
