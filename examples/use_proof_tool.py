import asyncio
from pathlib import Path
import sys
import os

# Add the parent directory to the Python path so we can import from template-mcp
sys.path.append(str(Path(__file__).parent.parent))

from tools.proof_tool import generate_proof_prompt

async def main():
    """
    Example usage of the proof_tool to generate a comprehensive prompt for Cursor.
    """
    
    # Example paths - adjust these to your actual files
    mapping_report_path = "reports/mapping_analysis_report.md"  # Your mapping analysis report
    api_spec_path = "sample_data/target_api.json"  # Your OpenAPI spec file
    current_path = "reports"  # Where to save the proof prompt
    collection_name = "flip_api_v2"  # RAG collection name
    
    # Create the output directory if it doesn't exist
    os.makedirs(current_path, exist_ok=True)
    
    print("🔍 Starting the Proof Tool...")
    print(f"📄 Mapping Report: {mapping_report_path}")
    print(f"📋 API Spec: {api_spec_path}")
    print(f"📁 Output Directory: {current_path}")
    print(f"🔗 Collection: {collection_name}")
    print("-" * 50)
    
    try:
        # Generate the proof prompt
        result = await generate_proof_prompt(
            mapping_report_path=mapping_report_path,
            api_spec_path=api_spec_path,
            current_path=current_path,
            collection_name=collection_name
        )
        
        print("\n✅ Proof Tool completed successfully!")
        print(f"📝 Generated prompt saved to: {current_path}")
        print("\n🎯 Next Steps:")
        print("1. Copy the generated prompt to Cursor")
        print("2. Run the verification and analysis tasks")
        print("3. Implement the suggested solutions")
        print("4. Update your mapping report with findings")
        
        # Show a preview of the generated prompt
        print(f"\n📖 Prompt Preview (first 500 characters):")
        print("=" * 50)
        print(result[:500] + "..." if len(result) > 500 else result)
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("Please check your file paths and try again.")

if __name__ == "__main__":
    asyncio.run(main()) 