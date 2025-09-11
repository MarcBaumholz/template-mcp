#!/usr/bin/env python3
"""
Debug script to check environment variable loading
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_env_loading():
    """Test environment variable loading"""
    print("🔍 Testing environment variable loading...")
    
    # Test direct loading
    print(f"Direct OPENROUTER_API_KEY: {os.getenv('OPENROUTER_API_KEY')}")
    print(f"Direct OPENROUTER_MODEL: {os.getenv('OPENROUTER_MODEL')}")
    
    # Test dotenv loading
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print(f"After dotenv load - OPENROUTER_API_KEY: {os.getenv('OPENROUTER_API_KEY')}")
        print(f"After dotenv load - OPENROUTER_MODEL: {os.getenv('OPENROUTER_MODEL')}")
    except Exception as e:
        print(f"Dotenv loading failed: {e}")
    
    # Test LLM client loading
    try:
        from tools.shared_utilities.llm_client import get_llm_response
        print("✅ LLM client imported successfully")
        
        # Check what the client sees
        print(f"LLM client sees OPENROUTER_API_KEY: {os.getenv('OPENROUTER_API_KEY')}")
        print(f"LLM client sees OPENROUTER_MODEL: {os.getenv('OPENROUTER_MODEL')}")
        
    except Exception as e:
        print(f"❌ LLM client import failed: {e}")

if __name__ == "__main__":
    test_env_loading()
