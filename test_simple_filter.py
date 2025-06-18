#!/usr/bin/env python3
"""
A small test for the filter_relevant_fields_with_llm tool.
"""
import sys
import os

# Ensure the project root is in the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.json_tools import filter_relevant_fields_with_llm

def run_simple_test():
    """Runs a test on a small, simple JSON file."""
    
    json_file = "sample_data/simple_test.json"
    context = "A user profile update event"
    
    print(f"🚀 Testing MCP tool with a small file: {json_file}")
    print(f"🚀 Context: '{context}'")
    print("="*60)

    # Call the core function of the MCP tool
    result = filter_relevant_fields_with_llm(
        file_path=json_file,
        context=context,
        save_filtered=True
    )
    
    print("\n--- Test Result ---")
    print(result)
    print("\n🏁 Test Complete!")

if __name__ == "__main__":
    run_simple_test() 