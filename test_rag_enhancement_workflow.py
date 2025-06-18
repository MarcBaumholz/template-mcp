#!/usr/bin/env python3
"""
End-to-end test for the RAG enhancement MCP tool.
"""
import sys
import os

# Ensure the project root is in the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.rag_tools import upload_openapi_spec_to_rag, enhance_csv_with_rag, delete_rag_collection
from tools.json_tools import flatten_json_file

def run_enhancement_test():
    """Runs a full test of the RAG enhancement workflow."""
    
    collection_name = "test_hr_api_spec"
    api_spec_path = "sample_data/sample_hr_api.json"
    json_payload_path = "sample_data/input_clean.json"
    
    print("🚀 Starting RAG Enhancement End-to-End Test")
    print("="*50)

    # --- Step 1: Flatten the test JSON to get a CSV ---
    print("\nSTEP 1: Flattening JSON to create a test CSV...")
    flatten_result = flatten_json_file(json_payload_path)
    # Extract the created CSV path from the result string
    try:
        csv_path = [line.split(": ")[1] for line in flatten_result.splitlines() if "Flattened data saved to" in line][0]
        print(f"✅ CSV created at: {csv_path}")
    except IndexError:
        print(f"❌ Failed to create or find CSV path from flatten result.")
        print(flatten_result)
        return

    # --- Step 2: Upload API Spec to RAG ---
    print("\nSTEP 2: Uploading API Specification to RAG collection...")
    # The tool will delete the collection if it exists and recreate it
    upload_result = upload_openapi_spec_to_rag(api_spec_path, collection_name)
    print(f"✅ Upload result: {upload_result}")
    
    # --- Step 3: Enhance the CSV with RAG ---
    print("\nSTEP 3: Running RAG enhancement on the CSV...")
    context_query = "Data for creating a new employee absence request"
    enhancement_result = enhance_csv_with_rag(
        csv_file_path=csv_path,
        collection_name=collection_name,
        context_query=context_query
    )
    print("\n--- RAG Enhancement Result ---")
    print(enhancement_result)
    
    # --- Step 4: Clean up ---
    print("\nSTEP 4: Cleaning up test RAG collection...")
    cleanup_result = delete_rag_collection(collection_name)
    print(f"✅ Cleanup result: {cleanup_result}")
    
    print("\n🏁 Test Complete!")

if __name__ == "__main__":
    run_enhancement_test() 