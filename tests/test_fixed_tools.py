#!/usr/bin/env python3
"""
Test the two fixed MCP tools:
1. upload_learnings_document
2. persist_phase_learnings
"""

import os
import sys
import json
import tempfile
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_upload_learnings_document():
    """Test the upload_learnings_document tool"""
    print("\n=== Testing upload_learnings_document ===")
    
    try:
        # Create a test markdown file
        test_content = """
# Test Learnings

## Do's
- Always test your code
- Use proper error handling

## Don'ts
- Don't ignore errors
- Don't skip tests

## How-Tos
- How to write good tests
- How to handle exceptions
"""
        
        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(test_content)
            temp_file = f.name
        
        try:
            from tools.phase1_data_extraction.rag_core import OptimizedRAGSystem
            from tools.phase1_data_extraction.rag_chunking import RAGChunkingMixin
            
            class EnhancedRAGSystem(OptimizedRAGSystem, RAGChunkingMixin):
                """Enhanced RAG system with chunking capabilities."""
                pass
            
            rag = EnhancedRAGSystem()
            result = rag.upload_markdown(temp_file, "test_learnings", {"test": "metadata"})
            print(f"✅ upload_learnings_document SUCCESS: {result[:100]}...")
            return True, result
        finally:
            # Clean up temp file
            os.unlink(temp_file)
            
    except Exception as e:
        print(f"❌ upload_learnings_document FAILED: {str(e)}")
        return False, str(e)

def test_persist_phase_learnings():
    """Test the persist_phase_learnings tool"""
    print("\n=== Testing persist_phase_learnings ===")
    
    try:
        # Create test files
        phase2_content = """
# Phase 2 Report

## Learnings
- Do: Always verify endpoints
- Don't: Skip validation steps
- How to: Use proper verification
"""
        
        verification_content = """
# Verification Report

✅ All claimed endpoints are found
Verification successful
"""
        
        phase3_content = """
# Phase 3 Report

## Code Generation
- Do: Write clean code
- Don't: Ignore security
- How to: Use proper patterns
"""
        
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
                from tools.shared_utilities.persist_phase_learnings import persist_learnings
                result = persist_learnings(
                    phase2_report_path=phase2_file,
                    verification_file_path=verification_file,
                    phase3_report_path=phase3_file,
                    phase3_verified=True,
                    collection_name="test_memory",
                    output_directory=temp_dir,
                    embed=False  # Skip embedding for test
                )
                print(f"✅ persist_phase_learnings SUCCESS: {result[:100]}...")
                return True, result
            finally:
                # Clean up temp files
                os.unlink(phase2_file)
                os.unlink(verification_file)
                os.unlink(phase3_file)
            
    except Exception as e:
        print(f"❌ persist_phase_learnings FAILED: {str(e)}")
        return False, str(e)

def run_fixed_tools_tests():
    """Run tests for the two fixed tools"""
    print("🚀 Testing Fixed MCP Tools")
    print("=" * 40)
    
    results = []
    
    # Test the fixed tools
    test_functions = [
        test_upload_learnings_document,
        test_persist_phase_learnings,
    ]
    
    for test_func in test_functions:
        success, result = test_func()
        results.append({
            'tool': test_func.__name__,
            'success': success,
            'result': result
        })
        
        if not success:
            print(f"🛑 Stopping at first failure: {test_func.__name__}")
            break
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 FIXED TOOLS TEST SUMMARY")
    print("=" * 40)
    
    passed = sum(1 for r in results if r['success'])
    total = len(results)
    
    for result in results:
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"{status} {result['tool']}")
    
    print(f"\nOverall: {passed}/{total} fixed tools working")
    
    return results

if __name__ == "__main__":
    run_fixed_tools_tests()