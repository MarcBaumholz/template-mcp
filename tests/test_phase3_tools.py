"""
Comprehensive tests for Phase 3 code generation MCP tools.

Tests all four tools:
- Direct field mapper
- Type converter
- Complex logic mapper
- TDD test generator
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

# Add tools directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from phase3.phase3_models import (
    MappingCategory,
    FieldMapping,
    MappingReport,
    KotlinCodeRequest,
    DirectMappingCode,
    TypeConversionCode,
    ComplexMappingCode,
    TDDTestCase,
    TDDTestSuite
)

from phase3.phase3_direct_mapper import (
    generate_direct_mappings,
    DirectMappingGenerator
)

from phase3.phase3_type_converter import (
    generate_type_conversions,
    TypeConversionGenerator
)

from phase3.phase3_complex_mapper import (
    generate_complex_mappings,
    ComplexLogicGenerator
)

from phase3.phase3_tdd_generator import (
    generate_tdd_tests,
    TDDTestGenerator
)


class TestPhase3Models:
    """Test the Pydantic models."""
    
    def test_mapping_category_creation(self):
        """Test MappingCategory model creation."""
        category = MappingCategory(
            category="direct",
            reason="Simple 1:1 mapping",
            confidence=0.95
        )
        assert category.category == "direct"
        assert category.confidence == 0.95
    
    def test_field_mapping_creation(self):
        """Test FieldMapping model creation."""
        category = MappingCategory(
            category="type_conversion",
            reason="Needs type conversion",
            confidence=0.8
        )
        mapping = FieldMapping(
            source_field="user.email",
            target_field="contactEmail",
            source_type="string",
            target_type="Email",
            category=category,
            transformation_notes="Validate email format",
            null_safe=True,
            default_value="noreply@example.com"
        )
        assert mapping.source_field == "user.email"
        assert mapping.category.category == "type_conversion"
        assert mapping.null_safe is True
    
    def test_mapping_report_creation(self):
        """Test MappingReport model creation."""
        mappings = [
            FieldMapping(
                source_field="id",
                target_field="employeeId",
                source_type="string",
                target_type="string",
                category=MappingCategory(
                    category="direct",
                    reason="Direct mapping",
                    confidence=1.0
                )
            )
        ]
        report = MappingReport(
            source_system="HR System",
            target_system="Payroll System",
            mappings=mappings,
            unmapped_fields=["custom_field"],
            verification_status={"verified": True}
        )
        assert report.source_system == "HR System"
        assert len(report.mappings) == 1
        assert len(report.unmapped_fields) == 1


class TestDirectMapper:
    """Test the direct field mapper tool."""
    
    def test_categorize_mappings(self):
        """Test mapping categorization."""
        generator = DirectMappingGenerator()
        
        # Create test mappings
        direct = FieldMapping(
            source_field="id",
            target_field="id",
            source_type="string",
            target_type="string",
            category=MappingCategory(category="direct", reason="1:1", confidence=1.0)
        )
        conversion = FieldMapping(
            source_field="date",
            target_field="date",
            source_type="string",
            target_type="Date",
            category=MappingCategory(category="type_conversion", reason="Type", confidence=0.9)
        )
        complex_logic = FieldMapping(
            source_field="name",
            target_field="fullName",
            source_type="string",
            target_type="string",
            category=MappingCategory(category="complex_logic", reason="Complex", confidence=0.8)
        )
        
        report = MappingReport(
            source_system="test",
            target_system="test",
            mappings=[direct, conversion, complex_logic]
        )
        
        direct_list, conv_list, complex_list = generator.categorize_mappings(report)
        
        assert len(direct_list) == 1
        assert len(conv_list) == 1
        assert len(complex_list) == 1
        assert direct_list[0].source_field == "id"
    
    @patch('phase3.phase3_direct_mapper.get_llm_response')
    def test_generate_direct_mapping_code(self, mock_llm):
        """Test direct mapping code generation."""
        mock_llm.return_value = "employeeId = source.id,\nemail = source.email"
        
        generator = DirectMappingGenerator()
        mappings = [
            FieldMapping(
                source_field="id",
                target_field="employeeId",
                source_type="string",
                target_type="string",
                category=MappingCategory(category="direct", reason="1:1", confidence=1.0)
            )
        ]
        request = KotlinCodeRequest(
            mapping_report_path="test.md",
            output_directory="test_output"
        )
        
        code = generator.generate_direct_mapping_code(mappings, request)
        assert "employeeId = source.id" in code
    
    @patch('phase3.phase3_direct_mapper.get_llm_response')
    def test_generate_direct_mappings_mcp_tool(self, mock_llm):
        """Test the MCP tool entry point."""
        mock_llm.return_value = "id = source.id"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a mock mapping report
            report_path = Path(temp_dir) / "mapping_report.md"
            report_path.write_text("# Mapping Report\nDirect Mappings:\n- id -> employeeId")
            
            result = generate_direct_mappings(
                mapping_report_path=str(report_path),
                output_directory=temp_dir
            )
            
            assert isinstance(result, DirectMappingCode)
            assert result.mapping_count >= 0
            assert result.kotlin_code != ""


class TestTypeConverter:
    """Test the type converter tool."""
    
    def test_identify_conversion_type(self):
        """Test conversion type identification."""
        generator = TypeConversionGenerator()
        
        assert generator.identify_conversion_type("string", "int") == "string_to_int"
        assert generator.identify_conversion_type("string", "boolean") == "string_to_boolean"
        assert generator.identify_conversion_type("StatusEnum", "string") == "enum_conversion"
        assert generator.identify_conversion_type("date", "string") == "date_to_string"
    
    @patch('phase3.phase3_type_converter.get_llm_response')
    def test_generate_conversion_function(self, mock_llm):
        """Test conversion function generation."""
        mock_llm.return_value = """
fun String.toLocalDate(): LocalDate {
    return LocalDate.parse(this)
}"""
        
        generator = TypeConversionGenerator()
        mapping = FieldMapping(
            source_field="startDate",
            target_field="hireDate",
            source_type="string",
            target_type="LocalDate",
            category=MappingCategory(category="type_conversion", reason="Type", confidence=0.9)
        )
        
        code = generator.generate_conversion_function(mapping)
        assert "toLocalDate" in code
        assert "LocalDate" in code
    
    @patch('phase3.phase3_type_converter.get_llm_response')
    def test_generate_type_conversions_mcp_tool(self, mock_llm):
        """Test the MCP tool entry point."""
        mock_llm.return_value = "fun String.toInt(): Int = this.toIntOrNull() ?: 0"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = Path(temp_dir) / "mapping_report.md"
            report_path.write_text("# Mapping Report\nType Conversions:\n- salary: string -> int")
            
            result = generate_type_conversions(
                mapping_report_path=str(report_path),
                output_directory=temp_dir
            )
            
            assert isinstance(result, TypeConversionCode)
            assert len(result.conversion_functions) >= 0


class TestComplexMapper:
    """Test the complex logic mapper tool."""
    
    def test_analyze_complexity(self):
        """Test complexity analysis."""
        generator = ComplexLogicGenerator()
        
        mapping = FieldMapping(
            source_field="firstName",
            target_field="fullName",
            source_type="string",
            target_type="string",
            category=MappingCategory(category="complex_logic", reason="Complex", confidence=0.8),
            transformation_notes="Concatenate firstName and lastName with space"
        )
        
        complexity = generator.analyze_complexity(mapping)
        assert "concatenation" in complexity["logic_types"]
        assert complexity["multi_field_dependency"] is True
    
    def test_to_camel_case(self):
        """Test camelCase conversion."""
        generator = ComplexLogicGenerator()
        
        assert generator._to_camel_case("employee_id") == "EmployeeId"
        assert generator._to_camel_case("user.profile.email") == "UserProfileEmail"
        assert generator._to_camel_case("start-date") == "StartDate"
    
    @patch('phase3.phase3_complex_mapper.get_llm_response')
    def test_generate_complex_function(self, mock_llm):
        """Test complex function generation."""
        mock_llm.return_value = """
fun mapFirstNameToFullName(source: Employee): String {
    return "${source.firstName} ${source.lastName}"
}"""
        
        generator = ComplexLogicGenerator()
        mapping = FieldMapping(
            source_field="firstName",
            target_field="fullName",
            source_type="string",
            target_type="string",
            category=MappingCategory(category="complex_logic", reason="Complex", confidence=0.8),
            transformation_notes="Concatenate names"
        )
        
        complexity = generator.analyze_complexity(mapping)
        code, func_name = generator.generate_complex_function(mapping, complexity)
        
        assert "mapFirstnameToFullname" in func_name
        assert "firstName" in code
    
    @patch('phase3.phase3_complex_mapper.get_llm_response')
    def test_generate_complex_mappings_mcp_tool(self, mock_llm):
        """Test the MCP tool entry point."""
        mock_llm.return_value = "fun calculateAge(birthDate: String): Int { return 30 }"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = Path(temp_dir) / "mapping_report.md"
            report_path.write_text("# Mapping Report\nComplex Logic:\n- birthDate -> age (calculate)")
            
            result = generate_complex_mappings(
                mapping_report_path=str(report_path),
                output_directory=temp_dir
            )
            
            assert isinstance(result, ComplexMappingCode)
            assert result.kotlin_code != ""


class TestTDDGenerator:
    """Test the TDD test generator tool."""
    
    def test_to_snake_case(self):
        """Test snake_case conversion."""
        generator = TDDTestGenerator()
        
        assert generator._to_snake_case("employeeId") == "employee_id"
        assert generator._to_snake_case("FullName") == "full_name"
        assert generator._to_snake_case("user.profile.Email") == "user_profile__email"
    
    @patch('phase3.phase3_tdd_generator.get_llm_response')
    def test_generate_test_case(self, mock_llm):
        """Test single test case generation."""
        mock_llm.return_value = """
@Test
@DisplayName("Should map employee ID correctly")
fun test_employee_id_direct() {
    val source = Employee(id = "123")
    val result = mapper.map(source)
    assertEquals("123", result.employeeId)
}"""
        
        generator = TDDTestGenerator()
        mapping = FieldMapping(
            source_field="id",
            target_field="employeeId",
            source_type="string",
            target_type="string",
            category=MappingCategory(category="direct", reason="Direct", confidence=1.0)
        )
        
        test_case = generator.generate_test_case(
            mapping,
            "unit",
            "Test direct field mapping"
        )
        
        assert test_case.name == "test_employee_id_unit"
        assert test_case.test_type == "unit"
        assert "@Test" in test_case.kotlin_code
    
    def test_generate_test_suite_for_mapping(self):
        """Test test suite generation for a mapping."""
        generator = TDDTestGenerator()
        
        mapping = FieldMapping(
            source_field="salary",
            target_field="compensation",
            source_type="string",
            target_type="double",
            category=MappingCategory(category="type_conversion", reason="Type", confidence=0.9)
        )
        
        with patch.object(generator, 'generate_test_case') as mock_gen:
            mock_gen.return_value = TDDTestCase(
                name="test_salary",
                description="Test salary conversion",
                test_type="unit",
                input_data={"salary": "50000"},
                expected_output={"compensation": 50000.0},
                kotlin_code="// test code"
            )
            
            test_cases = generator.generate_test_suite_for_mapping(mapping)
            
            assert len(test_cases) > 0
            assert all(isinstance(tc, TDDTestCase) for tc in test_cases)
    
    @patch('phase3.phase3_tdd_generator.get_llm_response')
    def test_generate_tdd_tests_mcp_tool(self, mock_llm):
        """Test the MCP tool entry point."""
        mock_llm.return_value = """
@Test
fun testMapping() {
    // test implementation
}"""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = Path(temp_dir) / "mapping_report.md"
            report_path.write_text("# Mapping Report\nMappings:\n- id -> employeeId")
            
            result = generate_tdd_tests(
                mapping_report_path=str(report_path),
                output_directory=temp_dir,
                test_all_scenarios=False
            )
            
            assert isinstance(result, TDDTestSuite)
            assert result.test_class_name == "MapperTestSuite"
            assert result.full_test_file != ""


class TestIntegration:
    """Integration tests for all Phase 3 tools working together."""
    
    @patch('phase3.phase3_direct_mapper.get_llm_response')
    @patch('phase3.phase3_type_converter.get_llm_response')
    @patch('phase3.phase3_complex_mapper.get_llm_response')
    @patch('phase3.phase3_tdd_generator.get_llm_response')
    def test_full_workflow(self, mock_tdd, mock_complex, mock_type, mock_direct):
        """Test the complete Phase 3 workflow."""
        # Mock LLM responses
        mock_direct.return_value = "id = source.id"
        mock_type.return_value = "fun String.toDate(): Date = Date.parse(this)"
        mock_complex.return_value = "fun mapFullName(s: Employee): String = s.firstName + s.lastName"
        mock_tdd.return_value = "@Test fun test() { assert(true) }"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mock mapping report
            report_path = Path(temp_dir) / "mapping_report.md"
            report_path.write_text("""
# Mapping Report
Direct: id -> employeeId
Type Conversion: startDate -> hireDate
Complex: firstName + lastName -> fullName
""")
            
            # Run all tools
            direct_result = generate_direct_mappings(
                mapping_report_path=str(report_path),
                output_directory=temp_dir
            )
            
            type_result = generate_type_conversions(
                mapping_report_path=str(report_path),
                output_directory=temp_dir
            )
            
            complex_result = generate_complex_mappings(
                mapping_report_path=str(report_path),
                output_directory=temp_dir
            )
            
            test_result = generate_tdd_tests(
                mapping_report_path=str(report_path),
                output_directory=temp_dir
            )
            
            # Verify all results
            assert isinstance(direct_result, DirectMappingCode)
            assert isinstance(type_result, TypeConversionCode)
            assert isinstance(complex_result, ComplexMappingCode)
            assert isinstance(test_result, TDDTestSuite)
            
            # Check that files were created
            output_files = list(Path(temp_dir).glob("*.kt"))
            assert len(output_files) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
