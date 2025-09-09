"""
Phase 3 Code Generation Tools for API Integration

This package contains MCP tools for generating Kotlin code from Phase 2 mapping reports:
- Direct field mappings (1:1)
- Data type conversions
- Complex logic mappings
- TDD test generation
"""

from .phase3_models import (
    MappingCategory,
    FieldMapping,
    MappingReport,
    KotlinCodeRequest,
    DirectMappingCode,
    TypeConversionCode,
    ComplexMappingCode,
    TDDTestCase,
    TDDTestSuite,
    Phase3Result
)

from .phase3_direct_mapper import (
    generate_direct_mappings,
    DirectMappingGenerator
)

from .phase3_type_converter import (
    generate_type_conversions,
    TypeConversionGenerator
)

from .phase3_complex_mapper import (
    generate_complex_mappings,
    ComplexLogicGenerator
)

from .phase3_tdd_generator import (
    generate_tdd_tests,
    TDDTestGenerator
)

__all__ = [
    # Models
    'MappingCategory',
    'FieldMapping',
    'MappingReport',
    'KotlinCodeRequest',
    'DirectMappingCode',
    'TypeConversionCode',
    'ComplexMappingCode',
    'TDDTestCase',
    'TDDTestSuite',
    'Phase3Result',
    
    # MCP Tool Functions
    'generate_direct_mappings',
    'generate_type_conversions',
    'generate_complex_mappings',
    'generate_tdd_tests',
    
    # Generator Classes
    'DirectMappingGenerator',
    'TypeConversionGenerator',
    'ComplexLogicGenerator',
    'TDDTestGenerator'
]
