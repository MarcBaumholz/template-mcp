import asyncio
from pathlib import Path
import sys
import os

# Add the parent directory to the Python path so we can import from template-mcp
sys.path.append(str(Path(__file__).parent.parent))

from tools.reasoning_agent import run_end_to_end_mapping_agent

async def main():
    # Example paths - adjust these to your actual files
    source_analysis_path = "sample_data/source_analysis.md"  # Your source field analysis file
    api_spec_path = "sample_data/target_api.json"  # Your OpenAPI spec file
    output_directory = "reports"  # Where to save the mapping report
    
    # Optional: specify a RAG collection name
    target_collection_name = "my_api_collection"
    
    # Create the output directory if it doesn't exist
    os.makedirs(output_directory, exist_ok=True)
    
    print("🚀 Starting the reasoning agent...")
    
    result = await run_end_to_end_mapping_agent(
        source_analysis_path=source_analysis_path,
        api_spec_path=api_spec_path,
        output_directory=output_directory,
        target_collection_name=target_collection_name
    )
    
    print("\n📝 Agent Result:", result)

if __name__ == "__main__":
    asyncio.run(main()) 