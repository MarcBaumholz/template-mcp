#!/usr/bin/env python3
"""Test the fixed MCP tools through the server interface."""

import sys
import tempfile
import os

# Add the project root to the Python path
sys.path.insert(0, '.')

def test_upload_learnings_document_mcp():
    """Test the upload_learnings_document MCP tool."""
    print("🧪 Testing upload_learnings_document MCP tool...")
    
    try:
        # Import the MCP tool function directly
        from server_fast import upload_learnings_document
        
        # Create a test learning document
        test_content = """# Test Learning Document

## Phase 2 Learnings

### ✅ Do's
- Always verify endpoints before mapping
- Use comprehensive analysis for complex APIs
- Query RAG collections with specific parameters

### ❌ Don'ts  
- Never skip verification steps
- Don't assume endpoint existence
- Don't use relative paths

## Phase 3 Learnings

### 🧭 How-Tos
- Generate clean, production-ready code
- Write comprehensive test suites
- Use security annotations in Kotlin code
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(test_content)
            test_file = f.name
        
        try:
            result = upload_learnings_document(
                file_path=test_file,
                collection_name="test_learnings_mcp",
                metadata={"test": True, "phase": ["2", "3"], "topics": ["mapping", "codegen"]}
            )
            print(f"✅ upload_learnings_document MCP result: {result}")
            return "✅" in result
        finally:
            os.unlink(test_file)
            
    except Exception as e:
        print(f"❌ upload_learnings_document MCP test failed: {e}")
        return False

def test_persist_phase_learnings_mcp():
    """Test the persist_phase_learnings MCP tool."""
    print("🧪 Testing persist_phase_learnings MCP tool...")
    
    try:
        # Import the MCP tool function directly
        from server_fast import persist_phase_learnings
        
        # Create test files with the fixed verification format
        phase2_content = '''# Phase 2 Mapping Report

## Field Mapping Analysis
- Source fields analyzed: employee_id, start_date, end_date
- Target endpoints identified: none (no endpoints claimed)
- Mapping strategy: Direct analysis approach

## Learnings
- Do: Always verify file accessibility first
- Don't: Skip environment validation
- How-to: Use read_multiple_files before upload_api_specification
'''

        # This is the key fix - verification with 0% rate but 0 total endpoints
        verification_content = '''# Endpoints Verification Report

## Verification Summary
Verification Rate: 0%
Total Endpoints Claimed: 0
✅ Verified: 0
❌ Potentially Hallucinated: 0

## Analysis
No endpoints were claimed during the mapping analysis phase.
This is a valid scenario when using direct analysis approaches
or when the source data doesn't require specific endpoint mapping.

✅ Verification successful - no endpoints to verify.
'''

        phase3_content = '''# Phase 3 Code Generation Report

## Generated Code
- Kotlin mapper: AbsenceMapper.kt
- Test suite: AbsenceMapperTest.kt
- Quality score: 95%

## Learnings
- Do: Use consolidated Phase 3 tools
- Don't: Skip quality auditing
- How-to: Run phase3_quality_suite after code generation
'''

        # Write to temporary files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(phase2_content)
            phase2_file = f.name
            
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(verification_content)
            verification_file = f.name
            
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(phase3_content)
            phase3_file = f.name

        # Create temp directory for output
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                result = persist_phase_learnings(
                    phase2_report_path=phase2_file,
                    verification_file_path=verification_file,
                    phase3_report_path=phase3_file,
                    phase3_verified=True,
                    collection_name='test_long_term_memory',
                    output_directory=temp_dir
                )
                print(f"✅ persist_phase_learnings MCP result: {result[:150]}...")
                return "✅" in result
            finally:
                # Clean up temp files
                os.unlink(phase2_file)
                os.unlink(verification_file)
                os.unlink(phase3_file)
                
    except Exception as e:
        print(f"❌ persist_phase_learnings MCP test failed: {e}")
        return False

def main():
    """Run all MCP tool tests."""
    print("🚀 Testing Fixed MCP Tools (Server Interface)")
    print("=" * 60)
    
    results = []
    
    # Test 1: upload_learnings_document MCP tool
    results.append(test_upload_learnings_document_mcp())
    
    print("-" * 60)
    
    # Test 2: persist_phase_learnings MCP tool
    results.append(test_persist_phase_learnings_mcp())
    
    print("=" * 60)
    print(f"📊 MCP Test Results: {sum(results)}/{len(results)} passed")
    
    if all(results):
        print("🎉 All MCP tools are now working correctly!")
        print("✅ upload_learnings_document: Fixed - EnhancedRAGSystem working")
        print("✅ persist_phase_learnings: Fixed - 0% verification rate with 0 endpoints handled")
    else:
        print("⚠️  Some MCP tools still have issues. Check the error messages above.")
    
    return all(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
