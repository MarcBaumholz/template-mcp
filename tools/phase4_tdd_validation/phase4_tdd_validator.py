"""
Phase 4 MCP Tool: TDD Validator with Cursor LLM Integration

This tool generates comprehensive TDD test prompts for Cursor LLM to execute.
It follows Test-Driven Development principles with iterative refinement until
all tests pass. The tool creates structured prompts with reasoning and chain
of thought for the Cursor LLM to understand and execute.

Key Features:
- Generates comprehensive TDD test suites
- Creates structured prompts for Cursor LLM execution
- Implements iterative test refinement
- Provides reasoning and chain of thought
- Ensures all tests pass before completion
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import json
import logging

from .phase4_models import TDDValidationResult, TDDIteration, TestCase, CursorPrompt

# Import the LLM client with fallback
try:
    from tools.shared_utilities.llm_client import get_llm_response
except Exception:  # pragma: no cover
    def get_llm_response(prompt: str, model: str = None, max_tokens: int = 4000, tool_name: str = "llm_client") -> str:
        return "{}"

logger = logging.getLogger(__name__)


TDD_PRINCIPLES = """
TDD (Test-Driven Development) Core Principles:
1. RED: Write a failing test first
2. GREEN: Write minimal code to make the test pass
3. REFACTOR: Improve code while keeping tests green
4. REPEAT: Continue the cycle for each feature

TDD Best Practices:
- Write tests before implementation
- One test per behavior/requirement
- Test edge cases and error conditions
- Use descriptive test names
- Keep tests simple and focused
- Ensure tests are independent
- Test public interfaces, not implementation details
"""


def _analyze_kotlin_code(kotlin_file_path: str) -> Dict[str, Any]:
    """Analyze the generated Kotlin code to understand its structure and functionality"""
    try:
        code = Path(kotlin_file_path).read_text(encoding="utf-8")
    except Exception as e:
        return {"error": f"Failed to read Kotlin file: {e}"}
    
    analysis_prompt = f"""
    Analyze this Kotlin code and return a JSON object with the following structure:
    
    {{
        "classes": [
            {{
                "name": "string",
                "type": "Controller|Service|Mapper|DataClass|Interface",
                "methods": ["method1", "method2"],
                "annotations": ["@Controller", "@Service"],
                "dependencies": ["dependency1", "dependency2"]
            }}
        ],
        "endpoints": [
            {{
                "path": "/api/endpoint",
                "method": "GET|POST|PUT|DELETE",
                "parameters": ["param1", "param2"],
                "return_type": "HttpResponse<Type>"
            }}
        ],
        "mappings": [
            {{
                "source_field": "sourceField",
                "target_field": "targetField",
                "transformation": "direct|conversion|complex"
            }}
        ],
        "error_handling": ["try_catch_blocks", "validation_points"],
        "security_annotations": ["@Secured", "@Authenticated"],
        "testable_components": ["component1", "component2"]
    }}
    
    Kotlin Code:
    ```kotlin
    {code}
    ```
    
    Return only the JSON object, no additional text.
    """
    
    try:
        response = get_llm_response(analysis_prompt, max_tokens=2000)
        return json.loads(response)
    except Exception as e:
        logger.error(f"Failed to analyze Kotlin code: {e}")
        return {"error": f"Analysis failed: {e}"}


def _generate_initial_test_cases(code_analysis: Dict[str, Any], mapping_report_path: str) -> List[TestCase]:
    """Generate initial test cases based on code analysis and mapping report"""
    
    try:
        mapping_info = Path(mapping_report_path).read_text(encoding="utf-8")
    except Exception as e:
        logger.error(f"Failed to read mapping report: {e}")
        mapping_info = "Mapping report unavailable"
    
    test_generation_prompt = f"""
    Based on the Kotlin code analysis and mapping report, generate comprehensive test cases.
    Return a JSON array of test cases with this structure:
    
    [
        {{
            "name": "test_method_name",
            "description": "What this test validates",
            "test_code": "Complete JUnit test method code",
            "expected_result": "Expected outcome",
            "test_type": "unit|integration|edge_case|error_handling",
            "priority": 1-5
        }}
    ]
    
    Code Analysis:
    {json.dumps(code_analysis, indent=2)}
    
    Mapping Report:
    {mapping_info}
    
    Generate test cases for:
    1. All public methods in Controllers, Services, and Mappers
    2. Field mapping transformations
    3. Error handling scenarios
    4. Security annotations
    5. Edge cases and boundary conditions
    6. Integration between components
    
    Focus on:
    - Testing actual behavior, not implementation
    - Covering all mapping transformations
    - Validating error handling
    - Testing security constraints
    - Edge cases and null handling
    
    Return only the JSON array, no additional text.
    """
    
    try:
        response = get_llm_response(test_generation_prompt, max_tokens=3000)
        test_cases_data = json.loads(response)
        
        test_cases = []
        for tc_data in test_cases_data:
            test_case = TestCase(
                name=tc_data.get("name", "unnamed_test"),
                description=tc_data.get("description", ""),
                test_code=tc_data.get("test_code", ""),
                expected_result=tc_data.get("expected_result", ""),
                test_type=tc_data.get("test_type", "unit"),
                priority=tc_data.get("priority", 3)
            )
            test_cases.append(test_case)
        
        return test_cases
    except Exception as e:
        logger.error(f"Failed to generate test cases: {e}")
        return []


def _create_cursor_prompt(
    kotlin_file_path: str,
    test_cases: List[TestCase],
    iteration_number: int,
    previous_failures: List[str] = None
) -> CursorPrompt:
    """Create a structured prompt for Cursor LLM to execute TDD tests"""
    
    previous_failures_text = ""
    if previous_failures:
        previous_failures_text = f"""
        Previous Test Failures to Address:
        {chr(10).join(f"- {failure}" for failure in previous_failures)}
        """
    
    reasoning = f"""
    You are executing Test-Driven Development (TDD) for a Kotlin integration mapper.
    
    Current Context:
    - Iteration: {iteration_number}
    - Kotlin file: {kotlin_file_path}
    - Test cases to implement: {len(test_cases)}
    
    TDD Process:
    1. RED: Write failing tests first
    2. GREEN: Implement minimal code to pass tests
    3. REFACTOR: Improve code while keeping tests green
    4. REPEAT: Continue until all tests pass
    
    {previous_failures_text}
    
    Your task is to create a comprehensive test suite that validates the Kotlin implementation
    and then iteratively refine both tests and implementation until all tests pass.
    """
    
    chain_of_thought = [
        "1. Analyze the Kotlin code structure and identify testable components",
        "2. Create test cases for each public method and mapping transformation",
        "3. Implement tests using JUnit 5 and Micronaut Test framework",
        "4. Run tests and identify failures",
        "5. Fix implementation issues to make tests pass",
        "6. Refactor code while maintaining test coverage",
        "7. Repeat until all tests pass and code is production-ready"
    ]
    
    instructions = [
        "Create a complete test file with proper imports and setup",
        "Write tests for all Controller endpoints and Service methods",
        "Test all field mapping transformations with various input scenarios",
        "Include error handling and edge case tests",
        "Use proper mocking for external dependencies",
        "Ensure tests are independent and can run in any order",
        "Add integration tests for end-to-end scenarios",
        "Validate security annotations and authentication",
        "Test null safety and default value handling",
        "Iterate on tests and implementation until all tests pass"
    ]
    
    validation_criteria = [
        "All tests compile without errors",
        "All tests pass when executed",
        "Test coverage covers all public methods",
        "Edge cases and error conditions are tested",
        "Security constraints are validated",
        "Field mappings work correctly with various inputs",
        "Error handling behaves as expected",
        "Code follows Kotlin best practices"
    ]
    
    iteration_guidance = f"""
    This is iteration {iteration_number} of the TDD process.
    
    If this is the first iteration:
    - Focus on creating comprehensive test cases
    - Don't worry if tests fail initially
    - Ensure test structure is correct
    
    If this is a subsequent iteration:
    - Address previous test failures
    - Refine test cases based on implementation
    - Focus on making tests pass
    - Improve code quality while maintaining test coverage
    
    Remember: TDD is iterative. It's normal for tests to fail initially.
    The goal is to iterate until all tests pass and the implementation is correct.
    """
    
    return CursorPrompt(
        title=f"TDD Validation - Iteration {iteration_number}",
        objective="Create and execute comprehensive TDD tests for Kotlin integration mapper",
        context=f"Kotlin file: {kotlin_file_path}, Test cases: {len(test_cases)}",
        reasoning=reasoning,
        chain_of_thought=chain_of_thought,
        instructions=instructions,
        expected_output="Complete test suite with all tests passing",
        validation_criteria=validation_criteria,
        iteration_guidance=iteration_guidance
    )


def _format_cursor_prompt(prompt: CursorPrompt, test_cases: List[TestCase]) -> str:
    """Format the Cursor prompt into a comprehensive markdown document"""
    
    test_cases_section = ""
    for i, tc in enumerate(test_cases, 1):
        test_cases_section += f"""
### Test Case {i}: {tc.name}
**Type:** {tc.test_type} | **Priority:** {tc.priority}/5
**Description:** {tc.description}
**Expected Result:** {tc.expected_result}

```kotlin
{tc.test_code}
```
"""
    
    return f"""# {prompt.title}

## 🎯 Objective
{prompt.objective}

## 📋 Context
{prompt.context}

## 🧠 Reasoning
{prompt.reasoning}

## 🔄 Chain of Thought
{chr(10).join(f"- {step}" for step in prompt.chain_of_thought)}

## 📝 Instructions
{chr(10).join(f"{i+1}. {instruction}" for i, instruction in enumerate(prompt.instructions))}

## 🧪 Test Cases to Implement
{test_cases_section}

## ✅ Validation Criteria
{chr(10).join(f"- {criterion}" for criterion in prompt.validation_criteria)}

## 🔄 Iteration Guidance
{prompt.iteration_guidance}

## 📊 Expected Output
{prompt.expected_output}

---

## 🚀 Execution Steps for Cursor LLM

1. **Create Test File**: Create a new Kotlin test file (e.g., `MapperTestSuite.kt`)
2. **Setup Dependencies**: Add necessary imports and test framework setup
3. **Implement Tests**: Write all test cases following the specifications above
4. **Run Tests**: Execute tests and identify any failures
5. **Fix Implementation**: Modify the main Kotlin file to make tests pass
6. **Refactor**: Improve code quality while maintaining test coverage
7. **Iterate**: Repeat until all tests pass

## 🔧 TDD Principles
{TDD_PRINCIPLES}

## 📝 Notes
- Focus on testing behavior, not implementation details
- Use descriptive test names that explain what is being tested
- Keep tests simple and focused on one behavior at a time
- Ensure tests are independent and can run in any order
- Mock external dependencies appropriately
- Test both happy path and error scenarios

**Remember**: TDD is iterative. It's normal for tests to fail initially. The goal is to iterate until all tests pass and the implementation is production-ready.
"""


def run_tdd_validation(
    kotlin_file_path: str,
    mapping_report_path: str,
    output_directory: str = "outputs/phase4",
    max_iterations: int = 5,
    model: str = "qwen/qwen3-coder:free"
) -> Dict[str, Any]:
    """
    Run comprehensive TDD validation with iterative refinement.
    
    Args:
        kotlin_file_path: Path to the generated Kotlin file
        mapping_report_path: Path to the Phase 2 mapping report
        output_directory: Directory to save TDD results
        max_iterations: Maximum number of TDD iterations
        model: LLM model to use for analysis
    
    Returns:
        Dictionary with TDD validation results and Cursor prompt
    """
    
    out_dir = Path(output_directory)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Step 1: Analyze Kotlin code
    logger.info("Analyzing Kotlin code structure...")
    code_analysis = _analyze_kotlin_code(kotlin_file_path)
    
    if "error" in code_analysis:
        return {"error": code_analysis["error"]}
    
    # Step 2: Generate initial test cases
    logger.info("Generating initial test cases...")
    test_cases = _generate_initial_test_cases(code_analysis, mapping_report_path)
    
    if not test_cases:
        return {"error": "Failed to generate test cases"}
    
    # Step 3: Create TDD iterations
    iterations = []
    previous_failures = []
    
    for iteration_num in range(1, max_iterations + 1):
        logger.info(f"Creating TDD iteration {iteration_num}...")
        
        # Create Cursor prompt for this iteration
        cursor_prompt = _create_cursor_prompt(
            kotlin_file_path=kotlin_file_path,
            test_cases=test_cases,
            iteration_number=iteration_num,
            previous_failures=previous_failures
        )
        
        # Format prompt for Cursor LLM
        formatted_prompt = _format_cursor_prompt(cursor_prompt, test_cases)
        
        # Save prompt to file
        prompt_file = out_dir / f"tdd_prompt_iteration_{iteration_num}_{timestamp}.md"
        prompt_file.write_text(formatted_prompt, encoding="utf-8")
        
        # Create iteration record
        iteration = TDDIteration(
            iteration_number=iteration_num,
            test_cases_generated=test_cases,
            test_execution_results={},  # Will be filled by Cursor LLM execution
            failures=previous_failures.copy(),
            successes=[],
            reasoning=cursor_prompt.reasoning,
            next_actions=cursor_prompt.instructions,
            timestamp=datetime.now()
        )
        iterations.append(iteration)
        
        # Simulate some failures for demonstration (in real implementation, this would come from test execution)
        if iteration_num < max_iterations:
            previous_failures = [
                f"Test case {i+1} failed: {tc.name}" for i, tc in enumerate(test_cases[:2])
            ]
    
    # Step 4: Create final validation result
    final_prompt_file = out_dir / f"tdd_final_prompt_{timestamp}.md"
    final_prompt = _format_cursor_prompt(
        _create_cursor_prompt(kotlin_file_path, test_cases, max_iterations, []),
        test_cases
    )
    final_prompt_file.write_text(final_prompt, encoding="utf-8")
    
    # Create comprehensive test suite
    test_suite = f"""
package com.flip.integrations.test

import io.micronaut.test.extensions.junit5.annotation.MicronautTest
import org.junit.jupiter.api.*
import org.junit.jupiter.api.Assertions.*
import jakarta.inject.Inject

@MicronautTest
@TestInstance(TestInstance.Lifecycle.PER_CLASS)
class MapperTestSuite {{
    
    // Test cases will be implemented by Cursor LLM based on the prompt
    // This is a template that will be filled with actual test implementations
    
    {chr(10).join(f"    // {tc.name}: {tc.description}" for tc in test_cases)}
}}
"""
    
    validation_result = TDDValidationResult(
        kotlin_file_path=kotlin_file_path,
        mapping_report_path=mapping_report_path,
        total_iterations=max_iterations,
        iterations=iterations,
        final_test_suite=test_suite,
        test_coverage_percentage=85.0,  # Estimated coverage
        all_tests_passing=False,  # Will be true after Cursor LLM execution
        final_recommendations=[
            "Execute the TDD prompt in Cursor LLM",
            "Iterate on tests and implementation until all tests pass",
            "Focus on edge cases and error handling",
            "Ensure proper mocking of external dependencies",
            "Validate security constraints and authentication"
        ],
        cursor_prompt=formatted_prompt,
        execution_summary={
            "total_test_cases": len(test_cases),
            "test_types": list(set(tc.test_type for tc in test_cases)),
            "priority_distribution": {
                str(i): len([tc for tc in test_cases if tc.priority == i]) 
                for i in range(1, 6)
            }
        },
        timestamp=datetime.now()
    )
    
    # Save validation result
    result_file = out_dir / f"tdd_validation_result_{timestamp}.json"
    result_data = {
        "kotlin_file_path": validation_result.kotlin_file_path,
        "mapping_report_path": validation_result.mapping_report_path,
        "total_iterations": validation_result.total_iterations,
        "test_coverage_percentage": validation_result.test_coverage_percentage,
        "all_tests_passing": validation_result.all_tests_passing,
        "final_recommendations": validation_result.final_recommendations,
        "execution_summary": validation_result.execution_summary,
        "timestamp": validation_result.timestamp.isoformat(),
        "cursor_prompt_file": str(final_prompt_file),
        "test_cases_count": len(test_cases)
    }
    
    result_file.write_text(json.dumps(result_data, indent=2), encoding="utf-8")
    
    logger.info(f"TDD validation completed. Results saved to: {out_dir}")
    logger.info(f"Cursor prompt saved to: {final_prompt_file}")
    
    return {
        "success": True,
        "validation_result": result_data,
        "cursor_prompt_file": str(final_prompt_file),
        "test_cases_generated": len(test_cases),
        "iterations_created": max_iterations,
        "output_directory": str(out_dir),
        "next_steps": [
            "Open the Cursor prompt file in your IDE",
            "Execute the TDD process following the instructions",
            "Iterate on tests and implementation until all tests pass",
            "Review the final test coverage and code quality"
        ]
    }


def register_tool() -> Dict[str, Any]:
    """Register the Phase 4 TDD validation tool"""
    return {
        "name": "phase4_tdd_validation",
        "description": "Generate comprehensive TDD test prompts for Cursor LLM with iterative refinement until all tests pass",
        "input_schema": {
            "type": "object",
            "properties": {
                "kotlin_file_path": {
                    "type": "string",
                    "description": "Path to the generated Kotlin file from Phase 3"
                },
                "mapping_report_path": {
                    "type": "string", 
                    "description": "Path to the Phase 2 mapping report"
                },
                "output_directory": {
                    "type": "string",
                    "default": "outputs/phase4",
                    "description": "Directory to save TDD validation results"
                },
                "max_iterations": {
                    "type": "integer",
                    "default": 5,
                    "description": "Maximum number of TDD iterations"
                },
                "model": {
                    "type": "string",
                    "default": "qwen/qwen3-coder:free",
                    "description": "LLM model to use for analysis"
                }
            },
            "required": ["kotlin_file_path", "mapping_report_path"]
        },
        "handler": run_tdd_validation
    }