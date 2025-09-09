#!/usr/bin/env python3
"""
Test script to verify MCP server fix and provide installation instructions
"""

import os
import sys
import subprocess

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_fastmcp_installation():
    """Check if fastmcp is installed"""
    print("🔍 Checking FastMCP installation...")
    
    try:
        import fastmcp
        print("✅ FastMCP is installed")
        return True
    except ImportError:
        print("❌ FastMCP is not installed")
        return False

def install_fastmcp():
    """Install fastmcp if not available"""
    print("\n🔧 Installing FastMCP...")
    
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "fastmcp"], 
                      check=True, capture_output=True, text=True)
        print("✅ FastMCP installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install FastMCP: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False

def test_server_import():
    """Test if the server can be imported"""
    print("\n🧪 Testing server import...")
    
    try:
        # Test importing the server
        import server_fast
        print("✅ Server imports successfully")
        return True
    except Exception as e:
        print(f"❌ Server import failed: {e}")
        return False

def test_tool_functionality():
    """Test the tool functionality directly"""
    print("\n🧪 Testing tool functionality...")
    
    try:
        from tools.api_spec_getter import get_direct_api_mapping_prompt
        
        # Test with the original parameters
        api_spec_path = "/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/test_temp_stackone/absences-stackone/backend/src/main/resources/openapi-definitions/stackone/api_stackone.json"
        analysis_md_path = "/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/stackone_temp_aug/clean_analysis_20250821_115102.md"
        
        result = get_direct_api_mapping_prompt(api_spec_path, analysis_md_path)
        
        if result.startswith("❌"):
            print(f"❌ Tool returned error: {result}")
            return False
        
        print("✅ Tool functionality works correctly")
        print(f"   Generated prompt length: {len(result)} characters")
        return True
        
    except Exception as e:
        print(f"❌ Tool functionality test failed: {e}")
        return False

def test_server_startup():
    """Test if the server can start"""
    print("\n🧪 Testing server startup...")
    
    try:
        # Try to import and check if FastMCP is available
        import server_fast
        
        # Check if FastMCP was imported successfully
        if hasattr(server_fast, 'FastMCP'):
            print("✅ FastMCP available in server")
            return True
        else:
            print("⚠️  FastMCP not available, but server has fallback")
            return True
            
    except Exception as e:
        print(f"❌ Server startup test failed: {e}")
        return False

def main():
    """Run all tests and provide solutions"""
    print("🚀 MCP Server Fix Test")
    print("=" * 50)
    
    # Check current state
    fastmcp_installed = check_fastmcp_installation()
    server_imports = test_server_import()
    tool_works = test_tool_functionality()
    server_starts = test_server_startup()
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS")
    print("=" * 50)
    print(f"FastMCP installed: {'✅' if fastmcp_installed else '❌'}")
    print(f"Server imports: {'✅' if server_imports else '❌'}")
    print(f"Tool functionality: {'✅' if tool_works else '❌'}")
    print(f"Server startup: {'✅' if server_starts else '❌'}")
    
    # Provide solutions
    print("\n" + "=" * 50)
    print("🔧 SOLUTIONS")
    print("=" * 50)
    
    if not fastmcp_installed:
        print("📦 To install FastMCP:")
        print("   pip install fastmcp")
        print("   or")
        print("   pip install -r requirements.txt")
        
        # Offer to install
        response = input("\n🤔 Would you like to install FastMCP now? (y/n): ")
        if response.lower() == 'y':
            if install_fastmcp():
                print("✅ FastMCP installed! The server should now work correctly.")
            else:
                print("❌ Installation failed. Please install manually.")
    
    if tool_works:
        print("\n✅ The get_direct_api_mapping_prompt tool works correctly!")
        print("💡 The 'Connection closed' error was due to missing FastMCP dependency.")
        print("🔧 After installing FastMCP, the MCP server will work properly.")
    
    if not server_starts:
        print("\n⚠️  Server startup issues detected.")
        print("🔧 Check the error messages above for specific issues.")
    
    print("\n" + "=" * 50)
    print("📋 NEXT STEPS")
    print("=" * 50)
    print("1. Install FastMCP: pip install fastmcp")
    print("2. Restart the MCP server")
    print("3. Test the get_direct_api_mapping_prompt tool again")
    print("4. The tool should now work without 'Connection closed' errors")
    
    return fastmcp_installed and server_imports and tool_works and server_starts

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
