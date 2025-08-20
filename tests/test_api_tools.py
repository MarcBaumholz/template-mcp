#!/usr/bin/env python3
"""
Test script for API Tools
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_basic_functionality():
    """Test basic functionality."""
    print("🧪 Testing basic functionality...")
    
    try:
        # Test RAG system
        from tools.rag_tools import test_rag_system, list_rag_collections
        
        print("Testing RAG system...")
        rag_result = test_rag_system()
        print(f"RAG Result: {rag_result}")
        
        print("Testing collections...")
        collections = list_rag_collections()
        print(f"Collections: {collections}")
        
        print("✅ Basic functionality test passed")
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

def test_mcp_server():
    """Test MCP server startup."""
    print("🧪 Testing MCP server...")
    
    try:
        # Import server components
        from fastmcp import FastMCP
        
        # Create a test server
        mcp = FastMCP("Test Server")
        
        @mcp.tool()
        def test_tool() -> str:
            return "Test tool working"
        
        print("✅ MCP server test passed")
        return True
        
    except Exception as e:
        print(f"❌ MCP server test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 API Tools Test Script")
    print("="*40)
    
    success = True
    success &= test_basic_functionality()
    success &= test_mcp_server()
    
    if success:
        print("🎉 All tests passed!")
    else:
        print("❌ Some tests failed")
        sys.exit(1)
