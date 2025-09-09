"""
Phase 4 TDD Validation Tools

This module provides comprehensive Test-Driven Development validation tools
for generated Kotlin code, including:
- TDD test generation with reasoning and chain of thought
- Iterative test refinement until all tests pass
- Integration with Cursor LLM for test execution
- Comprehensive test coverage analysis
"""

from .phase4_tdd_validator import register_tool

__all__ = ["register_tool"]