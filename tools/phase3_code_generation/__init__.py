"""
Phase 3 Code Generation Tools for API Integration

This package contains MCP tools for generating Kotlin code from Phase 2 mapping reports:
- Consolidated mapper generation (orchestrator)
- Quality suite (audit + TDD tests)
- Consistency selector (USC-style)
- Enhanced prompt generation
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

# Only import modules that still exist
try:
    from .phase3_tdd_generator import (
        generate_tdd_tests,
        TDDTestGenerator
    )
    TDD_AVAILABLE = True
except ImportError:
    TDD_AVAILABLE = False

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
]

# Add TDD functions if available
if TDD_AVAILABLE:
    __all__.extend([
        'generate_tdd_tests',
        'TDDTestGenerator'
    ])
