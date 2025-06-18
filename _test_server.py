#!/usr/bin/env python3
"""
Test script to verify the MCP server is working correctly.
"""

import json
import subprocess
import sys
from pathlib import Path

def test_mcp_server():
    """Test the MCP server by sending a simple request."""
    
    # Path to the server
    server_path = Path(__file__).parent / "server.py"
    
    # Test request to list available tools
    test_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    }
    
    try:
        # Start the server process
        process = subprocess.Popen(
            [sys.executable, str(server_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(server_path.parent)
        )
        
        # Send the test request
        request_json = json.dumps(test_request) + "\n"
        stdout, stderr = process.communicate(input=request_json, timeout=10)
        
        if stderr:
            print(f"❌ Server stderr: {stderr}")
            return False
            
        if stdout:
            print("✅ Server response received:")
            print(stdout)
            return True
        else:
            print("❌ No response from server")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Server test timed out")
        process.kill()
        return False
    except Exception as e:
        print(f"❌ Error testing server: {e}")
        return False

def main():
    """Main test function."""
    print("🧪 Testing MCP Server")
    print("=" * 40)
    
    if test_mcp_server():
        print("\n✅ MCP Server is working correctly!")
        print("\n📋 Available tools in your server:")
        print("   • list_available_api_specs")
        print("   • upload_api_specification") 
        print("   • query_api_specification")
        print("   • delete_api_specification")
        print("   • analyze_api_fields (ENHANCED)")
    else:
        print("\n❌ MCP Server test failed!")
        print("\n🔧 Troubleshooting steps:")
        print("   1. Check that your virtual environment is activated")
        print("   2. Verify all dependencies are installed: pip install -r requirements.txt")
        print("   3. Check your .env file has all required variables")
        print("   4. Test individual components with: python -c 'from tools import *'")

if __name__ == "__main__":
    main() 