#!/usr/bin/env python3
"""
Direct test of the schema mapping tool
"""
import asyncio
import os
from dotenv import load_dotenv
from tools.mapping import SchemaMappingTool
from tools.mapping_models import SchemaMappingRequest
from tools.report_generator import MarkdownReportGenerator

# Load environment variables
load_dotenv()

async def test_mapping():
    """Test the schema mapping functionality"""
    print(f"🔑 OpenRouter API Key loaded: {'✅' if os.getenv('OPENROUTER_API_KEY') else '❌'}")
    
    # Create request object
    request = SchemaMappingRequest(
        source_json_path='examples/sample_employee_data.json',
        source_analysis_md_path='examples/sample_employee_analysis.md',
        target_collection_name='stackone_api',
        mapping_context='Employee time off and absence management system',
        max_matches_per_field=3
    )
    
    tool = SchemaMappingTool()
    
    try:
        print("🔄 Starting schema mapping...")
        
        # Perform the mapping
        report = await tool.map_schema(request)
        
        print('✅ Mapping completed successfully!')
        print(f'🔍 Total fields analyzed: {report.summary_statistics.get("total_fields", 0)}')
        print(f'🎯 Fields with matches: {report.summary_statistics.get("fields_with_matches", 0)}')
        print(f'⏱️ Processing time: {report.processing_time_seconds:.2f} seconds')
        
        # Generate Markdown report
        report_generator = MarkdownReportGenerator()
        markdown_content = report_generator.generate_report(report, 'test_mapping_report.md')
        
        print(f'📄 Report saved to: test_mapping_report.md')
        print(f'📝 Report preview (first 500 chars):\n{markdown_content[:500]}...')
        
        return True
        
    except Exception as e:
        print(f'❌ Error during mapping: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_mapping())
    if success:
        print("\n🎉 Schema mapping test completed successfully!")
    else:
        print("\n💥 Schema mapping test failed!") 