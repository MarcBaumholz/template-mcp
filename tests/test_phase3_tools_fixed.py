#!/usr/bin/env python3
"""
Test script for Phase 3 MCP Tools (Fixed Import Issues)
Tests all 4 Phase 3 tools to ensure they work properly
"""

import json
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_phase3_direct_mappings():
    """Test phase3_generate_direct_mappings tool"""
    print("🧪 Testing phase3_generate_direct_mappings (Fixed)")
    print("=" * 60)
    
    try:
        from tools.phase3.phase3_direct_mapper import generate_direct_mappings
        
        # Test parameters
        mapping_report_path = str(project_root / "sample_mapping_report.md")
        ground_truth_path = str(project_root / "sample_data" / "clean.json")
        output_directory = str(project_root / "outputs" / "phase3")
        
        # Check if files exist
        if not Path(mapping_report_path).exists():
            print(f"❌ Mapping report not found: {mapping_report_path}")
            return False
            
        if not Path(ground_truth_path).exists():
            print(f"❌ Ground truth not found: {ground_truth_path}")
            return False
            
        print("✅ All input files exist")
        
        # Test the function
        result = generate_direct_mappings(
            mapping_report_path=mapping_report_path,
            ground_truth_path=ground_truth_path,
            output_directory=output_directory
        )
        
        print(f"✅ Direct Mappings test completed successfully!")
        print(f"📊 Result: {str(result)[:200]}...")
        return True
        
    except Exception as e:
        print(f"❌ Direct Mappings test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_phase3_type_conversions():
    """Test phase3_generate_type_conversions tool"""
    print("\n🧪 Testing phase3_generate_type_conversions (Fixed)")
    print("=" * 60)
    
    try:
        from tools.phase3.phase3_type_converter import generate_type_conversions
        
        # Test parameters
        mapping_report_path = "/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/mcp-personal-server-py/connector-mcp/outputs/mapping_report_20250122_220000.md"
        ground_truth_path = "/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/mcp-personal-server-py/connector-mcp/sample_data/clean.json"
        output_directory = "/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/mcp-personal-server-py/connector-mcp/outputs/phase3"
        
        # Test the function
        result = generate_type_conversions(
            mapping_report_path=mapping_report_path,
            ground_truth_path=ground_truth_path,
            output_directory=output_directory
        )
        
        print(f"✅ Type Conversions test completed successfully!")
        print(f"📊 Result: {str(result)[:200]}...")
        return True
        
    except Exception as e:
        print(f"❌ Type Conversions test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_phase3_complex_mappings():
    """Test phase3_generate_complex_mappings tool"""
    print("\n🧪 Testing phase3_generate_complex_mappings (Fixed)")
    print("=" * 60)
    
    try:
        from tools.phase3.phase3_complex_mapper import generate_complex_mappings
        
        # Test parameters
        mapping_report_path = "/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/mcp-personal-server-py/connector-mcp/outputs/mapping_report_20250122_220000.md"
        ground_truth_path = "/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/mcp-personal-server-py/connector-mcp/sample_data/clean.json"
        output_directory = "/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/mcp-personal-server-py/connector-mcp/outputs/phase3"
        
        # Test the function
        result = generate_complex_mappings(
            mapping_report_path=mapping_report_path,
            ground_truth_path=ground_truth_path,
            output_directory=output_directory
        )
        
        print(f"✅ Complex Mappings test completed successfully!")
        print(f"📊 Result: {str(result)[:200]}...")
        return True
        
    except Exception as e:
        print(f"❌ Complex Mappings test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_phase3_tdd_tests():
    """Test phase3_generate_tdd_tests tool"""
    print("\n🧪 Testing phase3_generate_tdd_tests (Fixed)")
    print("=" * 60)
    
    try:
        from tools.phase3.phase3_tdd_generator import generate_tdd_tests
        
        # Test parameters
        mapping_report_path = "/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/mcp-personal-server-py/connector-mcp/outputs/mapping_report_20250122_220000.md"
        mapper_code_path = "/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/mcp-personal-server-py/connector-mcp/outputs/phase3/DirectMapper_20250122_220000.kt"
        output_directory = "/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/mcp-personal-server-py/connector-mcp/outputs/phase3/tests"
        test_all_scenarios = True
        
        # Test the function
        result = generate_tdd_tests(
            mapping_report_path=mapping_report_path,
            mapper_code_path=mapper_code_path,
            output_directory=output_directory,
            test_all_scenarios=test_all_scenarios
        )
        
        print(f"✅ TDD Tests test completed successfully!")
        print(f"📊 Result: {str(result)[:200]}...")
        return True
        
    except Exception as e:
        print(f"❌ TDD Tests test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all Phase 3 tool tests"""
    print("🚀 Phase 3 MCP Tools Testing (Fixed Import Issues)")
    print("=" * 80)
    
    # Test all Phase 3 tools
    results = []
    
    results.append(test_phase3_direct_mappings())
    results.append(test_phase3_type_conversions())
    results.append(test_phase3_complex_mappings())
    results.append(test_phase3_tdd_tests())
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 PHASE 3 TOOLS TESTING SUMMARY")
    print("=" * 80)
    
    tool_names = [
        "phase3_generate_direct_mappings",
        "phase3_generate_type_conversions", 
        "phase3_generate_complex_mappings",
        "phase3_generate_tdd_tests"
    ]
    
    for i, (tool_name, result) in enumerate(zip(tool_names, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{i+1}. {tool_name}: {status}")
    
    success_count = sum(results)
    total_count = len(results)
    
    print(f"\n🎯 Overall Results: {success_count}/{total_count} tools working ({success_count/total_count*100:.1f}%)")
    
    if success_count == total_count:
        print("🎉 ALL PHASE 3 TOOLS ARE NOW WORKING!")
        print("✅ Import issues have been resolved")
        print("✅ MCP tools can be called properly")
    else:
        print("⚠️  Some tools still have issues")
        print("🔧 Additional fixes may be needed")

if __name__ == "__main__":
    main()
