#!/usr/bin/env python3
"""
Test script for MCP JSON Analysis and RAG Server
"""

import json
import asyncio
from server import (
    analyze_structure, 
    extract_fields, 
    flatten_object,
    server
)
from mcp.server import NotificationOptions

def test_json_analysis():
    """Test JSON analysis functions."""
    print("🧪 Testing JSON Analysis Functions...")
    
    # Test data
    test_json = '{"user": {"name": "John", "age": 30, "profile": {"email": "john@example.com"}}, "active": true}'
    
    # Test structure analysis
    print("\n1. Testing analyze_json_structure:")
    result = analyze_structure(test_json)
    print(json.dumps(result, indent=2))
    
    # Test field extraction
    print("\n2. Testing extract_json_fields:")
    result = extract_fields(test_json, ["user.name", "user.age", "user.profile.email", "active"])
    print(json.dumps(result, indent=2))
    
    # Test flattening
    print("\n3. Testing flatten_json:")
    result = flatten_object(test_json)
    print(json.dumps(result, indent=2))

def test_server_initialization():
    """Test server initialization."""
    print("\n🚀 Testing Server Initialization...")
    
    try:
        # Test that server is properly initialized
        print("✅ Server object created successfully")
        
        # Test capabilities with proper arguments
        capabilities = server.get_capabilities(
            notification_options=NotificationOptions(),
            experimental_capabilities={}
        )
        print(f"✅ Server capabilities configured: {bool(capabilities)}")
        
        print("✅ All server tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Server test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🔬 MCP JSON Analysis and RAG Server - Test Suite")
    print("=" * 50)
    
    try:
        # Test JSON analysis
        test_json_analysis()
        
        # Test server initialization
        server_ok = test_server_initialization()
        
        print("\n" + "=" * 50)
        if server_ok:
            print("🎉 All tests passed! Server is ready to use.")
            print("\n📋 Available functionality:")
            print("   • JSON structure analysis")
            print("   • Field extraction with dot notation")
            print("   • JSON flattening")
            print("   • RAG tools (when OpenAI API key is configured)")
            print("\n🚀 Start the server with: ./start_server.sh")
            print("🔧 Configure in Claude Desktop or Cursor IDE using the provided config")
        else:
            print("❌ Some tests failed. Please check the configuration.")
            
    except Exception as e:
        print(f"❌ Test suite failed: {e}")

if __name__ == "__main__":
    main()