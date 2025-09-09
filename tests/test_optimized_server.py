#!/usr/bin/env python3
"""
Test script for the optimized MCP server with enhanced RAG tools
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_rag_system():
    """Test the optimized RAG system"""
    print("🧪 Testing Optimized RAG System...")
    try:
        from tools.rag_tools import test_rag_system as test_rag
        result = test_rag()
        print(f"✅ RAG Test Result: {result}")
        return True
    except Exception as e:
        print(f"❌ RAG Test Failed: {e}")
        return False

def test_server_tools():
    """Test server tool imports"""
    print("\n🔧 Testing Server Tool Imports...")
    
    try:
        # Test RAG tools import
        from tools.rag_tools import (
            test_rag_system,
            list_rag_collections,
            upload_openapi_spec_to_rag,
            retrieve_from_rag,
            delete_rag_collection,
            analyze_fields_with_rag_and_llm
        )
        print("✅ RAG tools imported successfully")
        
        # Test other tools
        from tools.reasoning_agent import reasoning_agent
        print("✅ Reasoning agent imported successfully")
        
        from tools.json_tool.combined_analysis_agent import CombinedFieldAnalysisAgent
        print("✅ Combined analysis agent imported successfully")
        
        from tools.codingtool.biggerprompt import generate_enhanced_prompt
        print("✅ Coding tool imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Tool Import Failed: {e}")
        return False

def test_enhanced_features():
    """Test enhanced RAG features"""
    print("\n🚀 Testing Enhanced RAG Features...")
    
    try:
        from tools.rag_tools import get_rag_system
        
        # Test RAG system initialization
        rag = get_rag_system()
        print("✅ Optimized RAG system initialized")
        
        # Test collection listing
        collections = rag.list_collections()
        print(f"✅ Collections found: {len(collections)}")
        
        # Test enhanced query method exists
        if hasattr(rag, 'enhanced_query'):
            print("✅ Enhanced query method available")
        else:
            print("❌ Enhanced query method not found")
            return False
        
        # Test comprehensive content extraction
        if hasattr(rag, '_extract_comprehensive_api_content'):
            print("✅ Comprehensive content extraction available")
        else:
            print("❌ Comprehensive content extraction not found")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced Features Test Failed: {e}")
        return False

async def test_combined_analysis():
    """Test combined JSON analysis"""
    print("\n🔄 Testing Combined JSON Analysis...")
    
    try:
        from tools.json_tool.combined_analysis_agent import CombinedFieldAnalysisAgent
        
        # Create test JSON data
        test_data = {
            "employee": {
                "id": "12345",
                "name": "John Doe",
                "email": "john@example.com",
                "department": "Engineering",
                "start_date": "2023-01-15",
                "status": "active"
            },
            "request_type": "absence",
            "timestamp": "2024-01-20T10:30:00Z"
        }
        
        # Initialize agent
        agent = CombinedFieldAnalysisAgent()
        
        # Test processing
        result = await agent.process_json_with_combined_analysis(
            json_data=test_data,
            json_file_path="/test/path.json",
            current_directory="./test_output",
            collection_name="test_collection"
        )
        
        print(f"✅ Combined analysis completed: {result.status}")
        print(f"   Extracted fields: {len(result.result.extracted_fields)}")
        print(f"   Confidence: {result.result.confidence_score:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Combined Analysis Test Failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Starting Optimized Server Tests...\n")
    
    # Test 1: RAG System
    rag_ok = test_rag_system()
    
    # Test 2: Server Tools
    tools_ok = test_server_tools()
    
    # Test 3: Enhanced Features
    features_ok = test_enhanced_features()
    
    # Test 4: Combined Analysis
    analysis_ok = asyncio.run(test_combined_analysis())
    
    # Summary
    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)
    print(f"RAG System: {'✅ PASS' if rag_ok else '❌ FAIL'}")
    print(f"Server Tools: {'✅ PASS' if tools_ok else '❌ FAIL'}")
    print(f"Enhanced Features: {'✅ PASS' if features_ok else '❌ FAIL'}")
    print(f"Combined Analysis: {'✅ PASS' if analysis_ok else '❌ FAIL'}")
    
    all_passed = rag_ok and tools_ok and features_ok and analysis_ok
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED! Server is ready to run.")
        print("\n🚀 To start the server:")
        print("   cd mcp-personal-server-py/connector-mcp")
        print("   source venv/bin/activate")
        print("   python server_fast.py")
        print("\n🌐 For public access:")
        print("   ngrok http 8080")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 