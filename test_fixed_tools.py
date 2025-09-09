#!/usr/bin/env python3
"""Test the fixed upload_learnings_document and persist_phase_learnings tools."""

import sys
import tempfile
import os
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, '.')

def test_upload_learnings_document():
    """Test the upload_learnings_document tool."""
    print("🧪 Testing upload_learnings_document...")
    
    try:
        from tools.phase1_data_extraction.rag_chunking import RAGChunkingMixin
        from tools.phase1_data_extraction.rag_core import OptimizedRAGSystem
        
        class EnhancedRAGSystem(OptimizedRAGSystem, RAGChunkingMixin):
            """Enhanced RAG system with chunking capabilities."""
            pass
        
        # Create a test markdown file
        test_content = """# Test Learning Document

## Phase 2 Learnings

### ✅ Do's
- Always verify endpoints before mapping
- Use comprehensive analysis for complex APIs

### ❌ Don'ts  
- Never skip verification steps
- Don't assume endpoint existence

## Phase 3 Learnings

### 🧭 How-Tos
- Generate clean, production-ready code
- Write comprehensive test suites
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(test_content)
            test_file = f.name
        
        try:
            rag = EnhancedRAGSystem()
            result = rag.upload_markdown(test_file, "test_learnings", {"test": True})
            print(f"✅ upload_learnings_document test result: {result}")
            return True
        finally:
            os.unlink(test_file)
            
    except Exception as e:
        print(f"❌ upload_learnings_document test failed: {e}")
        return False

def test_persist_phase_learnings():
    """Test the persist_phase_learnings tool with the fixed verification logic."""
    print("🧪 Testing persist_phase_learnings...")
    
    try:
        from tools.shared_utilities.persist_phase_learnings import persist_learnings
        
        # Create test files
        phase2_content = '''# Phase 2 Report
## Learnings
- Do: Always verify endpoints
- Don't: Skip validation steps
'''

        verification_content = '''# Verification Report
Verification Rate: 0%
Total Endpoints Claimed: 0
✅ Verified: 0
❌ Potentially Hallucinated: 0

## Summary
No endpoints were claimed in the mapping analysis, so verification is complete.
'''

        phase3_content = '''# Phase 3 Report
## Code Generation
- Do: Write clean code
- Don't: Ignore security
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
                result = persist_learnings(
                    phase2_report_path=phase2_file,
                    verification_file_path=verification_file,
                    phase3_report_path=phase3_file,
                    phase3_verified=True,
                    collection_name='test_memory',
                    output_directory=temp_dir,
                    embed=False  # Skip embedding for test
                )
                print(f"✅ persist_phase_learnings test result: {result[:100]}...")
                return True
            finally:
                # Clean up temp files
                os.unlink(phase2_file)
                os.unlink(verification_file)
                os.unlink(phase3_file)
                
    except Exception as e:
        print(f"❌ persist_phase_learnings test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Testing Fixed MCP Tools")
    print("=" * 50)
    
    results = []
    
    # Test 1: upload_learnings_document
    results.append(test_upload_learnings_document())
    
    # Test 2: persist_phase_learnings  
    results.append(test_persist_phase_learnings())
    
    print("=" * 50)
    print(f"📊 Test Results: {sum(results)}/{len(results)} passed")
    
    if all(results):
        print("🎉 All tests passed! Both tools are now working.")
    else:
        print("⚠️  Some tests failed. Check the error messages above.")
    
    return all(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
