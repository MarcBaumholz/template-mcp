#!/usr/bin/env python3
"""
Systematic testing of all MCP tools
Tests each tool one by one to identify and fix issues
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_tool_1_test_rag_system():
    """Test the first MCP tool: test_rag_system"""
    print("\n=== Testing Tool 1: test_rag_system ===")
    
    try:
        from tools.phase1_data_extraction.test_rag_tool import test_rag_system
        result = test_rag_system()
        print(f"✅ test_rag_system SUCCESS: {result[:100]}...")
        return True, result
    except Exception as e:
        print(f"❌ test_rag_system FAILED: {str(e)}")
        return False, str(e)

def test_tool_2_list_available_api_specs():
    """Test the second MCP tool: list_available_api_specs"""
    print("\n=== Testing Tool 2: list_available_api_specs ===")
    
    try:
        from tools.phase1_data_extraction.rag_core import get_rag_system
        rag = get_rag_system()
        collections = rag.list_collections()
        
        if not collections:
            result = "No collections found. Upload an API spec first."
        else:
            # Get detailed collection information
            collection_info = []
            total_points = 0
            
            for name in collections:
                try:
                    info = rag.client.get_collection(name)
                    points_count = info.points_count
                    total_points += points_count
                    collection_info.append(f"• {name} ({points_count:,} points)")
                except Exception as e:
                    collection_info.append(f"• {name} (metadata unavailable)")
            
            result = f"📊 Available API Collections ({len(collections)}):\n"
            result += "\n".join(collection_info)
            result += f"\n\n📈 Total Points: {total_points:,}"
        
        print(f"✅ list_available_api_specs SUCCESS: {result[:100]}...")
        return True, result
        
    except Exception as e:
        print(f"❌ list_available_api_specs FAILED: {str(e)}")
        return False, str(e)

def test_tool_3_upload_api_specification():
    """Test the third MCP tool: upload_api_specification"""
    print("\n=== Testing Tool 3: upload_api_specification ===")
    
    try:
        # Create a minimal test OpenAPI spec
        test_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "Test API",
                "version": "1.0.0"
            },
            "paths": {
                "/test": {
                    "get": {
                        "responses": {
                            "200": {
                                "description": "Success",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "id": {"type": "string"},
                                                "name": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        
        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_spec, f, indent=2)
            temp_file = f.name
        
        try:
            from tools.phase1_data_extraction.upload_api_spec_tool import upload_openapi_spec_to_rag
            result = upload_openapi_spec_to_rag(temp_file, "test_collection", {"test": "metadata"})
            print(f"✅ upload_api_specification SUCCESS: {result[:100]}...")
            return True, result
        finally:
            # Clean up temp file
            os.unlink(temp_file)
            
    except Exception as e:
        print(f"❌ upload_api_specification FAILED: {str(e)}")
        return False, str(e)

def test_tool_4_query_api_specification():
    """Test the fourth MCP tool: query_api_specification"""
    print("\n=== Testing Tool 4: query_api_specification ===")
    
    try:
        from tools.phase1_data_extraction.query_api_spec_tool import retrieve_from_rag
        result = retrieve_from_rag("test query", "test_collection", limit=3, score_threshold=0.5)
        print(f"✅ query_api_specification SUCCESS: {result[:100]}...")
        return True, result
    except Exception as e:
        print(f"❌ query_api_specification FAILED: {str(e)}")
        return False, str(e)

def test_tool_5_delete_api_specification():
    """Test the fifth MCP tool: delete_api_specification"""
    print("\n=== Testing Tool 5: delete_api_specification ===")
    
    try:
        from tools.phase1_data_extraction.delete_api_spec_tool import delete_rag_collection
        result = delete_rag_collection("test_collection")
        print(f"✅ delete_api_specification SUCCESS: {result[:100]}...")
        return True, result
    except Exception as e:
        print(f"❌ delete_api_specification FAILED: {str(e)}")
        return False, str(e)

def test_tool_6_copy_rules_to_working_directory():
    """Test the sixth MCP tool: copy_rules_to_working_directory"""
    print("\n=== Testing Tool 6: copy_rules_to_working_directory ===")
    
    try:
        from tools.shared_utilities.copy_rules_to_working_directory import copy_rules_to_working_directory
        result = copy_rules_to_working_directory("")
        print(f"✅ copy_rules_to_working_directory SUCCESS: {result[:100]}...")
        return True, result
    except Exception as e:
        print(f"❌ copy_rules_to_working_directory FAILED: {str(e)}")
        return False, str(e)

def test_tool_7_generate_kotlin_mapping_code():
    """Test the seventh MCP tool: generate_kotlin_mapping_code"""
    print("\n=== Testing Tool 7: generate_kotlin_mapping_code ===")
    
    try:
        # Create a minimal test mapping report
        test_report = """
# Mapping Report (Test)

## Direct Mappings
- employee.id -> employeeId (string -> string)
- employee.name -> fullName (string -> string)

## Type Conversions
- startDate (string) -> LocalDate

## Complex Mappings
- fullName = firstName + " " + lastName
"""
        
        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(test_report)
            temp_file = f.name
        
        try:
            from tools.phase3_code_generation.generate_kotlin_mapping_code import generate_enhanced_prompt
            # Read the template
            template_path = project_root / "tools" / "phase3_code_generation" / "template.kt"
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()
            
            result = generate_enhanced_prompt(test_report, template)
            print(f"✅ generate_kotlin_mapping_code SUCCESS: {result[:100]}...")
            return True, result
        finally:
            # Clean up temp file
            os.unlink(temp_file)
            
    except Exception as e:
        print(f"❌ generate_kotlin_mapping_code FAILED: {str(e)}")
        return False, str(e)

def test_tool_8_phase3_generate_mapper():
    """Test the eighth MCP tool: phase3_generate_mapper"""
    print("\n=== Testing Tool 8: phase3_generate_mapper ===")
    
    try:
        # Create a minimal test mapping report
        test_report = """
# Mapping Report (Test)

## Direct Mappings
- employee.id -> employeeId (string -> string)
"""
        
        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(test_report)
            temp_file = f.name
        
        # Create temp directory for output
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                from tools.phase3_code_generation.phase3_orchestrator import generate_mapper
                result = generate_mapper(
                    mapping_report_path=temp_file,
                    output_directory=temp_dir,
                    company_name="test",
                    project_name="test",
                    backend_name="test"
                )
                print(f"✅ phase3_generate_mapper SUCCESS: {result.final_mapper_code[:100] if result.final_mapper_code else 'No code generated'}...")
                return True, result.final_mapper_code or "No code generated"
            finally:
                # Clean up temp file
                os.unlink(temp_file)
            
    except Exception as e:
        print(f"❌ phase3_generate_mapper FAILED: {str(e)}")
        return False, str(e)

def test_tool_9_phase3_quality_suite():
    """Test the ninth MCP tool: phase3_quality_suite"""
    print("\n=== Testing Tool 9: phase3_quality_suite ===")
    
    try:
        # Create a minimal test Kotlin file
        test_kotlin = """
package com.test
import io.micronaut.http.*
import io.micronaut.http.annotation.*
import io.micronaut.security.annotation.*
import io.micronaut.security.rules.SecurityRule

@Controller("/api")
@Secured(SecurityRule.IS_AUTHENTICATED)
class TestController {
    @Get
    fun test(): String = "test"
}
"""
        
        # Create a minimal test mapping report
        test_report = """
# Mapping Report (Test)

## Direct Mappings
- employee.id -> employeeId (string -> string)
"""
        
        # Write to temporary files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.kt', delete=False) as f:
            f.write(test_kotlin)
            kotlin_file = f.name
            
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(test_report)
            report_file = f.name
        
        # Create temp directory for output
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                from tools.phase3_code_generation.phase3_quality_suite import run_quality_suite
                result = run_quality_suite(
                    kotlin_file_path=kotlin_file,
                    mapping_report_path=report_file,
                    output_directory=temp_dir
                )
                print(f"✅ phase3_quality_suite SUCCESS: {str(result)[:100]}...")
                return True, str(result)
            finally:
                # Clean up temp files
                os.unlink(kotlin_file)
                os.unlink(report_file)
            
    except Exception as e:
        print(f"❌ phase3_quality_suite FAILED: {str(e)}")
        return False, str(e)

def test_tool_10_phase3_select_best_candidate():
    """Test the tenth MCP tool: phase3_select_best_candidate"""
    print("\n=== Testing Tool 10: phase3_select_best_candidate ===")
    
    try:
        # Create two test Kotlin files
        test_kotlin1 = """
package com.test
class TestController1 {
    fun test(): String = "test1"
}
"""
        
        test_kotlin2 = """
package com.test
import io.micronaut.http.*
import io.micronaut.http.annotation.*
import io.micronaut.security.annotation.*
import io.micronaut.security.rules.SecurityRule

@Controller("/api")
@Secured(SecurityRule.IS_AUTHENTICATED)
class TestController2 {
    @Get
    fun test(): String = "test2"
}
"""
        
        # Create a minimal test mapping report
        test_report = """
# Mapping Report (Test)

## Direct Mappings
- employee.id -> employeeId (string -> string)
"""
        
        # Write to temporary files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.kt', delete=False) as f:
            f.write(test_kotlin1)
            kotlin_file1 = f.name
            
        with tempfile.NamedTemporaryFile(mode='w', suffix='.kt', delete=False) as f:
            f.write(test_kotlin2)
            kotlin_file2 = f.name
            
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(test_report)
            report_file = f.name
        
        try:
            from tools.phase3_code_generation.phase3_selector import select_best_candidate
            result = select_best_candidate(
                kotlin_files=[kotlin_file1, kotlin_file2],
                mapping_report_path=report_file
            )
            print(f"✅ phase3_select_best_candidate SUCCESS: {str(result)[:100]}...")
            return True, str(result)
        finally:
            # Clean up temp files
            os.unlink(kotlin_file1)
            os.unlink(kotlin_file2)
            os.unlink(report_file)
            
    except Exception as e:
        print(f"❌ phase3_select_best_candidate FAILED: {str(e)}")
        return False, str(e)

def test_tool_11_get_direct_api_mapping_prompt():
    """Test the eleventh MCP tool: get_direct_api_mapping_prompt"""
    print("\n=== Testing Tool 11: get_direct_api_mapping_prompt ===")
    
    try:
        # Create a minimal test API spec
        test_api_spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/employees": {
                    "get": {
                        "responses": {
                            "200": {
                                "description": "Success",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "id": {"type": "string"},
                                                "name": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        
        # Create a minimal test analysis
        test_analysis = """
# Field Analysis

## Source Fields
- employee.id
- employee.name
"""
        
        # Write to temporary files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_api_spec, f, indent=2)
            api_spec_file = f.name
            
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(test_analysis)
            analysis_file = f.name
        
        try:
            from tools.phase2_analysis_mapping.get_direct_api_mapping_prompt import get_api_spec_with_direct_llm_query
            result = get_api_spec_with_direct_llm_query(api_spec_file, analysis_file)
            print(f"✅ get_direct_api_mapping_prompt SUCCESS: {result[:100]}...")
            return True, result
        finally:
            # Clean up temp files
            os.unlink(api_spec_file)
            os.unlink(analysis_file)
            
    except Exception as e:
        print(f"❌ get_direct_api_mapping_prompt FAILED: {str(e)}")
        return False, str(e)

def test_tool_12_enhanced_rag_analysis():
    """Test the twelfth MCP tool: enhanced_rag_analysis"""
    print("\n=== Testing Tool 12: enhanced_rag_analysis ===")
    
    try:
        from tools.phase1_data_extraction.analyze_fields_tool import analyze_fields_with_rag_and_llm as enhanced_analyze
        result = enhanced_analyze(
            fields=["employee.id", "employee.name"],
            collection_name="test_collection",
            context_topic="HR integration",
            current_path=None
        )
        print(f"✅ enhanced_rag_analysis SUCCESS: {result[:100]}...")
        return True, result
    except Exception as e:
        print(f"❌ enhanced_rag_analysis FAILED: {str(e)}")
        return False, str(e)

def run_systematic_tests():
    """Run all MCP tool tests systematically"""
    print("🚀 Starting Systematic MCP Tool Testing")
    print("=" * 50)
    
    results = []
    
    # Test tools one by one
    test_functions = [
        test_tool_1_test_rag_system,
        test_tool_2_list_available_api_specs,
        test_tool_3_upload_api_specification,
        test_tool_4_query_api_specification,
        test_tool_5_delete_api_specification,
        test_tool_6_copy_rules_to_working_directory,
        test_tool_7_generate_kotlin_mapping_code,
        test_tool_8_phase3_generate_mapper,
        test_tool_9_phase3_quality_suite,
        test_tool_10_phase3_select_best_candidate,
        test_tool_11_get_direct_api_mapping_prompt,
        test_tool_12_enhanced_rag_analysis,
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
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for r in results if r['success'])
    total = len(results)
    
    for result in results:
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"{status} {result['tool']}")
    
    print(f"\nOverall: {passed}/{total} tools working")
    
    return results

if __name__ == "__main__":
    run_systematic_tests()
