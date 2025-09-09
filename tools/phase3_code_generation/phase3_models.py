"""
Shared Pydantic models for Phase 3 code generation tools.

These models define the data structures used across all Phase 3 MCP tools
for Kotlin code generation, including direct mappings, type conversions,
complex logic, and TDD test generation.
"""

from typing import List, Dict, Optional, Any, Literal
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class MappingCategory(BaseModel):
    """Categorization of a field mapping."""
    category: Literal["direct", "type_conversion", "complex_logic"] = Field(
        description="Category of the mapping"
    )
    reason: str = Field(description="Reason for this categorization")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score")


class FieldMapping(BaseModel):
    """Represents a single field mapping from source to target."""
    source_field: str = Field(description="Source field path (e.g., 'user.profile.email')")
    target_field: str = Field(description="Target field path (e.g., 'employee.contactEmail')")
    source_type: str = Field(description="Source data type")
    target_type: str = Field(description="Target data type")
    category: MappingCategory = Field(description="Mapping category")
    transformation_notes: Optional[str] = Field(
        default=None, 
        description="Notes about required transformations"
    )
    null_safe: bool = Field(default=True, description="Whether to generate null-safe code")
    default_value: Optional[str] = Field(
        default=None, 
        description="Default value if source is null"
    )


class MappingReport(BaseModel):
    """Complete mapping report from Phase 2."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    source_system: str = Field(description="Source system name")
    target_system: str = Field(description="Target system name")
    mappings: List[FieldMapping] = Field(description="All field mappings")
    unmapped_fields: List[str] = Field(default=[], description="Fields that couldn't be mapped")
    verification_status: Dict[str, Any] = Field(
        default={}, 
        description="Endpoint verification results"
    )
    ground_truth_path: Optional[str] = Field(
        default=None, 
        description="Path to ground truth verification data"
    )
    timestamp: datetime = Field(default_factory=datetime.now)


class KotlinCodeRequest(BaseModel):
    """Request for Kotlin code generation."""
    mapping_report_path: str = Field(description="Path to the mapping report file")
    ground_truth_path: Optional[str] = Field(
        default=None, 
        description="Path to ground truth verification file"
    )
    output_directory: str = Field(
        default="outputs/phase3", 
        description="Directory to save generated code"
    )
    company_name: str = Field(default="flip", description="Company name for package")
    project_name: str = Field(default="integrations", description="Project name for package")
    backend_name: str = Field(default="stackone", description="Backend system name")


class DirectMappingCode(BaseModel):
    """Generated code for direct field mappings."""
    kotlin_code: str = Field(description="Generated Kotlin code for direct mappings")
    mapped_fields: List[str] = Field(description="List of successfully mapped fields")
    mapping_count: int = Field(description="Number of direct mappings generated")


class TypeConversionCode(BaseModel):
    """Generated code for type conversion mappings."""
    kotlin_code: str = Field(description="Generated Kotlin conversion functions")
    conversion_functions: List[str] = Field(
        description="List of generated conversion function names"
    )
    integrated_code: str = Field(
        description="Code with conversions integrated into mapper"
    )


class ComplexMappingCode(BaseModel):
    """Generated code for complex logic mappings."""
    kotlin_code: str = Field(description="Generated Kotlin functions for complex logic")
    function_names: List[str] = Field(description="List of generated function names")
    integration_points: Dict[str, str] = Field(
        description="Map of where to integrate each function"
    )


class TDDTestCase(BaseModel):
    """Represents a single test case."""
    name: str = Field(description="Test case name")
    description: str = Field(description="What this test verifies")
    test_type: Literal["unit", "integration", "edge_case"] = Field(
        description="Type of test"
    )
    input_data: Dict[str, Any] = Field(description="Input data for the test")
    expected_output: Dict[str, Any] = Field(description="Expected output")
    kotlin_code: str = Field(description="Generated Kotlin test code")


class TDDTestSuite(BaseModel):
    """Complete TDD test suite for mapper."""
    test_class_name: str = Field(description="Name of the test class")
    test_cases: List[TDDTestCase] = Field(description="All test cases")
    setup_code: str = Field(description="Test setup/initialization code")
    teardown_code: Optional[str] = Field(default=None, description="Test cleanup code")
    full_test_file: str = Field(description="Complete Kotlin test file")


class Phase3Result(BaseModel):
    """Combined result from all Phase 3 tools."""
    direct_mappings: Optional[DirectMappingCode] = Field(default=None)
    type_conversions: Optional[TypeConversionCode] = Field(default=None)
    complex_mappings: Optional[ComplexMappingCode] = Field(default=None)
    test_suite: Optional[TDDTestSuite] = Field(default=None)
    final_mapper_code: Optional[str] = Field(
        default=None, 
        description="Complete integrated mapper code"
    )
    controller_code: Optional[str] = Field(
        default=None, 
        description="Generated controller code"
    )
    service_code: Optional[str] = Field(
        default=None, 
        description="Generated service code"
    )
    generation_timestamp: datetime = Field(default_factory=datetime.now)
    errors: List[str] = Field(default=[], description="Any errors during generation")
