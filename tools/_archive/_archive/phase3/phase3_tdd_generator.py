"""
Phase 3 MCP Tool: TDD Test Generator

This tool generates comprehensive test cases for all mapper scenarios
using Test-Driven Development principles. It creates tests for direct mappings,
type conversions, complex logic, edge cases, and error conditions.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from pydantic import BaseModel, Field
from .phase3_models import (
    MappingReport, FieldMapping, TDDTestSuite, TDDTestCase,
    KotlinCodeRequest
)

# Import the LLM client with fallback
try:
    from ..llm_client import get_llm_response
except ImportError:
    try:
        import sys
        sys.path.append(str(Path(__file__).parent.parent))
        from llm_client import get_llm_response
    except ImportError:
        # Fallback for when imported as standalone module
        def get_llm_response(prompt: str, model: str = None, max_tokens: int = 2000, tool_name: str = "llm_client") -> str:
            """Fallback LLM response function"""
            return f"Mock LLM response for: {prompt[:100]}..."

logger = logging.getLogger(__name__)


class TDDTestGenerator:
    """Generates comprehensive Kotlin test cases following TDD principles."""
    
    def __init__(self):
        self.model = "qwen/qwen3-coder:free"  # Free model from OpenRouter
        self.test_patterns = self._load_test_patterns()
    
    def _load_test_patterns(self) -> Dict[str, List[str]]:
        """Load common test patterns for different scenarios."""
        return {
            "direct": [
                "Test direct field mapping",
                "Test null source field",
                "Test default value application"
            ],
            "type_conversion": [
                "Test successful conversion",
                "Test conversion with invalid input",
                "Test conversion with null input",
                "Test boundary values",
                "Test format variations"
            ],
            "complex_logic": [
                "Test happy path logic",
                "Test edge cases",
                "Test error conditions",
                "Test with missing dependencies",
                "Test business rule validation"
            ],
            "integration": [
                "Test full mapping flow",
                "Test with real-world data",
                "Test performance with large datasets"
            ]
        }
    
    def generate_test_case(
        self,
        mapping: FieldMapping,
        test_type: str,
        test_description: str
    ) -> TDDTestCase:
        """Generate a single test case for a mapping."""
        
        # Create test name
        test_name = f"test_{self._to_snake_case(mapping.target_field)}_{test_type}"
        
        prompt = f"""You are a senior Kotlin test developer with TDD expertise. Generate a test case.

Mapping to Test:
- Source Field: {mapping.source_field} ({mapping.source_type})
- Target Field: {mapping.target_field} ({mapping.target_type})
- Category: {mapping.category.category}
- Transformation: {mapping.transformation_notes or "Direct mapping"}

Test Details:
- Test Type: {test_type}
- Test Description: {test_description}
- Test Name: {test_name}

Requirements:
1. Use JUnit 5 and Kotlin test conventions
2. Include meaningful assertions
3. Use descriptive test data
4. Follow AAA pattern (Arrange, Act, Assert)
5. Add @Test and @DisplayName annotations
6. Use mockk for mocking if needed
7. Make the test self-documenting

Generate ONLY the Kotlin test method:

Example format:
```kotlin
@Test
@DisplayName("Should handle specific scenario")
fun {test_name}() {{
    // Arrange
    val input = ...
    
    // Act
    val result = ...
    
    // Assert
    assertEquals(expected, result)
}}
```

Output the complete test method:"""

        try:
            response = get_llm_response(prompt, model=self.model, max_tokens=800)
            # Clean up response
            code = response.strip()
            if code.startswith("```kotlin"):
                code = code[9:]
            if code.endswith("```"):
                code = code[:-3]
            
            # Create sample test data (would be extracted from generated code in production)
            input_data = {mapping.source_field: f"test_{mapping.source_field}_value"}
            expected_output = {mapping.target_field: f"expected_{mapping.target_field}_value"}
            
            return TDDTestCase(
                name=test_name,
                description=test_description,
                test_type=test_type,
                input_data=input_data,
                expected_output=expected_output,
                kotlin_code=code.strip()
            )
            
        except Exception as e:
            logger.error(f"Error generating test case: {e}")
            return self._generate_todo_test(test_name, test_description, test_type)
    
    def _generate_todo_test(
        self,
        test_name: str,
        test_description: str,
        test_type: str
    ) -> TDDTestCase:
        """Generate a TODO placeholder test."""
        code = f"""
@Test
@DisplayName("{test_description}")
fun {test_name}() {{
    TODO("Implement test: {test_description}")
}}"""
        
        return TDDTestCase(
            name=test_name,
            description=test_description,
            test_type=test_type,
            input_data={},
            expected_output={},
            kotlin_code=code
        )
    
    def _to_snake_case(self, field_path: str) -> str:
        """Convert field path to snake_case."""
        import re
        # Convert camelCase to snake_case
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', field_path)
        s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
        return s2.lower().replace(".", "_").replace("-", "_")
    
    def generate_test_suite_for_mapping(
        self,
        mapping: FieldMapping
    ) -> List[TDDTestCase]:
        """Generate all test cases for a single mapping."""
        
        test_cases = []
        category = mapping.category.category
        
        # Get test patterns for this category
        patterns = self.test_patterns.get(category, self.test_patterns["direct"])
        
        # Generate test for each pattern
        for pattern in patterns:
            # Determine test type
            if "null" in pattern.lower() or "edge" in pattern.lower():
                test_type = "edge_case"
            elif "integration" in pattern.lower() or "full" in pattern.lower():
                test_type = "integration"
            else:
                test_type = "unit"
            
            test_case = self.generate_test_case(
                mapping,
                test_type,
                pattern
            )
            test_cases.append(test_case)
        
        return test_cases
    
    def generate_setup_code(self, mappings: List[FieldMapping]) -> str:
        """Generate test setup/initialization code."""
        
        prompt = f"""You are a senior Kotlin test developer. Generate test setup code.

Mappings to Test:
{json.dumps([{
    "source": m.source_field,
    "target": m.target_field,
    "category": m.category.category
} for m in mappings[:5]], indent=2)}  # First 5 for context

Generate test class setup including:
1. Class declaration with @TestInstance annotation
2. Mock dependencies using mockk
3. System under test initialization
4. Common test data setup
5. Helper methods for creating test objects

Output ONLY the setup code (class declaration, properties, @BeforeEach):"""

        try:
            response = get_llm_response(prompt, model=self.model, max_tokens=1000)
            # Clean up response
            code = response.strip()
            if code.startswith("```kotlin"):
                code = code[9:]
            if code.endswith("```"):
                code = code[:-3]
            return code.strip()
        except Exception as e:
            logger.error(f"Error generating setup code: {e}")
            return self._get_default_setup_code()
    
    def _get_default_setup_code(self) -> str:
        """Get default test setup code."""
        return """
@TestInstance(TestInstance.Lifecycle.PER_CLASS)
class MapperTest {
    
    private lateinit var mapper: CompleteMapper
    private val mockClient = mockk<FacadeClient>()
    
    @BeforeEach
    fun setup() {
        mapper = CompleteMapper()
        clearAllMocks()
    }
    
    // Helper methods
    private fun createTestSource() = SourceDTO(
        // Add test data
    )
    
    private fun createExpectedTarget() = TargetDTO(
        // Add expected data
    )"""
    
    def create_complete_test_file(
        self,
        test_suite: TDDTestSuite,
        package_name: str = "com.flip.integrations.test"
    ) -> str:
        """Create a complete Kotlin test file."""
        
        # Organize tests by type
        unit_tests = [t for t in test_suite.test_cases if t.test_type == "unit"]
        integration_tests = [t for t in test_suite.test_cases if t.test_type == "integration"]
        edge_case_tests = [t for t in test_suite.test_cases if t.test_type == "edge_case"]
        
        prompt = f"""You are a senior Kotlin test developer. Create a complete test file.

Package: {package_name}
Test Class: {test_suite.test_class_name}

Setup Code:
{test_suite.setup_code}

Unit Tests ({len(unit_tests)} tests):
{chr(10).join([t.kotlin_code for t in unit_tests[:3]])}  # First 3 for context

Edge Case Tests ({len(edge_case_tests)} tests):
{chr(10).join([t.kotlin_code for t in edge_case_tests[:2]])}  # First 2 for context

Integration Tests ({len(integration_tests)} tests):
{chr(10).join([t.kotlin_code for t in integration_tests[:2]])}  # First 2 for context

Generate a complete, well-organized Kotlin test file with:
1. Package declaration and imports
2. Class with setup
3. All test methods organized by type
4. Proper annotations and documentation
5. Helper methods as needed

Output ONLY the complete Kotlin test file:"""

        try:
            response = get_llm_response(prompt, model=self.model, max_tokens=4000)
            # Clean up response
            code = response.strip()
            if code.startswith("```kotlin"):
                code = code[9:]
            if code.endswith("```"):
                code = code[:-3]
            return code.strip()
        except Exception as e:
            logger.error(f"Error creating complete test file: {e}")
            return self._create_default_test_file(test_suite, package_name)
    
    def _create_default_test_file(
        self,
        test_suite: TDDTestSuite,
        package_name: str
    ) -> str:
        """Create a default test file structure."""
        
        # Combine all test methods
        all_tests = "\n\n".join([tc.kotlin_code for tc in test_suite.test_cases])
        
        return f"""package {package_name}

import org.junit.jupiter.api.*
import org.junit.jupiter.api.Assertions.*
import io.mockk.*
import kotlin.test.assertNotNull

/**
 * Test suite for mapper implementations
 * Generated using TDD principles
 */
{test_suite.setup_code}

    // ========== Unit Tests ==========
    
{all_tests}

    // ========== Helper Methods ==========
    
    private fun assertMappingValid(source: Any, target: Any) {{
        assertNotNull(target, "Target should not be null")
        // Add more validation
    }}
}}"""


def generate_tdd_tests(
    mapping_report_path: str,
    mapper_code_path: Optional[str] = None,
    output_directory: str = "outputs/phase3/tests",
    test_all_scenarios: bool = True,
    **kwargs
) -> TDDTestSuite:
    """
    MCP Tool Entry Point: Generate comprehensive TDD tests for mapper.
    
    Args:
        mapping_report_path: Path to the mapping report from Phase 2
        mapper_code_path: Optional path to generated mapper code
        output_directory: Directory to save test files
        test_all_scenarios: Whether to generate tests for all scenarios
        **kwargs: Additional configuration
    
    Returns:
        TDDTestSuite with all generated tests
    """
    logger.info(f"Starting TDD test generation from: {mapping_report_path}")
    
    # Load the mapping report
    try:
        with open(mapping_report_path, 'r') as f:
            report_content = f.read()
        
        # Parse the report to extract mappings
        report = _parse_mapping_report(report_content)
        
    except Exception as e:
        logger.error(f"Failed to load mapping report: {e}")
        return TDDTestSuite(
            test_class_name="MapperTest",
            test_cases=[],
            setup_code="// Error loading report",
            full_test_file=f"// Error: {str(e)}"
        )
    
    # Initialize generator
    generator = TDDTestGenerator()
    
    # Generate test cases for all mappings
    all_test_cases = []
    
    for mapping in report.mappings:
        if test_all_scenarios or mapping.category.confidence < 0.9:
            # Generate more tests for less confident mappings
            test_cases = generator.generate_test_suite_for_mapping(mapping)
            all_test_cases.extend(test_cases)
    
    # Add integration tests
    if test_all_scenarios:
        integration_test = TDDTestCase(
            name="test_complete_mapping_flow",
            description="Test complete mapping from source to target",
            test_type="integration",
            input_data={"complete": "source_object"},
            expected_output={"complete": "target_object"},
            kotlin_code="""
    @Test
    @DisplayName("Should successfully map complete source to target")
    fun test_complete_mapping_flow() {
        // Arrange
        val source = createCompleteTestSource()
        val expected = createExpectedCompleteTarget()
        
        // Act
        val result = mapper.mapComplete(source)
        
        // Assert
        assertEquals(expected, result)
        assertAllFieldsMapped(result)
    }"""
        )
        all_test_cases.append(integration_test)
    
    # Generate setup code
    setup_code = generator.generate_setup_code(report.mappings)
    
    # Create test suite
    test_suite = TDDTestSuite(
        test_class_name="MapperTestSuite",
        test_cases=all_test_cases,
        setup_code=setup_code,
        teardown_code="""
    @AfterEach
    fun teardown() {
        clearAllMocks()
    }
    
    @AfterAll
    fun cleanup() {
        // Clean up resources if needed
    }""",
        full_test_file=""  # Will be generated next
    )
    
    # Generate complete test file
    package_name = kwargs.get("package_name", "com.flip.integrations.test")
    complete_file = generator.create_complete_test_file(test_suite, package_name)
    test_suite.full_test_file = complete_file
    
    # Save test file
    output_path = Path(output_directory)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_file = output_path / f"MapperTestSuite_{timestamp}.kt"
    
    with open(test_file, 'w') as f:
        f.write(complete_file)
    
    # Save individual test cases for reference
    cases_file = output_path / f"TDDTestCases_{timestamp}.json"
    with open(cases_file, 'w') as f:
        cases_data = [
            {
                "name": tc.name,
                "description": tc.description,
                "type": tc.test_type,
                "input": tc.input_data,
                "expected": tc.expected_output
            }
            for tc in all_test_cases
        ]
        json.dump(cases_data, f, indent=2)
    
    logger.info(f"Generated test suite saved to: {test_file}")
    logger.info(f"Test cases metadata saved to: {cases_file}")
    logger.info(f"Total test cases generated: {len(all_test_cases)}")
    
    # Log test coverage summary
    test_types = {}
    for tc in all_test_cases:
        test_types[tc.test_type] = test_types.get(tc.test_type, 0) + 1
    
    logger.info("Test coverage by type:")
    for test_type, count in test_types.items():
        logger.info(f"  - {test_type}: {count} tests")
    
    return test_suite


def _parse_mapping_report(content: str) -> MappingReport:
    """
    Parse the mapping report from markdown/text format.
    This is a simplified parser - implement based on actual report format.
    """
    from .phase3_models import MappingCategory
    
    # Mock data for testing - replace with actual parsing
    return MappingReport(
        source_system="source",
        target_system="target",
        mappings=[
            FieldMapping(
                source_field="employee.id",
                target_field="employeeId",
                source_type="string",
                target_type="string",
                category=MappingCategory(
                    category="direct",
                    reason="Direct mapping",
                    confidence=1.0
                )
            ),
            FieldMapping(
                source_field="employee.startDate",
                target_field="hireDate",
                source_type="string",
                target_type="LocalDate",
                category=MappingCategory(
                    category="type_conversion",
                    reason="String to date conversion",
                    confidence=0.9
                )
            ),
            FieldMapping(
                source_field="employee.firstName",
                target_field="fullName",
                source_type="string",
                target_type="string",
                category=MappingCategory(
                    category="complex_logic",
                    reason="Concatenation required",
                    confidence=0.85
                ),
                transformation_notes="Combine firstName and lastName"
            )
        ]
    )


# MCP Tool Registration
def register_tool():
    """Register this tool with the MCP server."""
    return {
        "name": "phase3_generate_tdd_tests",
        "description": "Generate comprehensive TDD test suite for mapper implementations",
        "input_schema": {
            "type": "object",
            "properties": {
                "mapping_report_path": {
                    "type": "string",
                    "description": "Path to the mapping report file"
                },
                "mapper_code_path": {
                    "type": "string",
                    "description": "Optional path to generated mapper code"
                },
                "output_directory": {
                    "type": "string",
                    "description": "Directory to save test files",
                    "default": "outputs/phase3/tests"
                },
                "test_all_scenarios": {
                    "type": "boolean",
                    "description": "Generate tests for all scenarios",
                    "default": True
                },
                "package_name": {
                    "type": "string",
                    "description": "Package name for test class",
                    "default": "com.flip.integrations.test"
                }
            },
            "required": ["mapping_report_path"]
        },
        "handler": generate_tdd_tests
    }
