#!/usr/bin/env python3
"""
Test script for the SSE MCP server
"""

import requests
import json
import time

def test_server():
    """Test the SSE MCP server endpoints."""
    base_url = "http://localhost:8080"
    
    print("🧪 Testing HR API Mapping SSE Server")
    print("=" * 50)
    
    # Test 1: Check if server is running
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"✅ Server is running (Status: {response.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"❌ Server not accessible: {e}")
        return
    
    # Test 2: Check SSE endpoint
    try:
        response = requests.get(f"{base_url}/sse/", timeout=5)
        print(f"✅ SSE endpoint accessible (Status: {response.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"❌ SSE endpoint not accessible: {e}")
    
    # Test 3: Check ngrok URL (if accessible)
    ngrok_url = "https://9e7b4aa28520.ngrok-free.app"
    try:
        response = requests.get(ngrok_url, timeout=10)
        print(f"✅ Ngrok tunnel working (Status: {response.status_code})")
        print(f"🌐 Public URL: {ngrok_url}/sse/")
    except requests.exceptions.RequestException as e:
        print(f"⚠️  Ngrok tunnel not accessible: {e}")
    
    print("\n📋 MCP Client Configuration:")
    print('"hr_api_mapping_server": {')
    print('  "transport": "sse",')
    print(f'  "url": "{ngrok_url}/sse/"')
    print('}')
    
    print("\n🛠️  Available Tools:")
    tools = [
        "analyze_json_fields_with_rag",
        "reasoning_agent_orchestrator", 
        "generate_kotlin_mapping_code",
        "upload_api_specification",
        "query_api_specification",
        "list_available_api_specs",
        "delete_api_specification",
        "get_direct_api_mapping_prompt",
        "test_rag_system_and_llm"
    ]
    
    for i, tool in enumerate(tools, 1):
        print(f"   {i}. {tool}")
    
    print(f"\n✅ Server test completed!")

if __name__ == "__main__":
    test_server()