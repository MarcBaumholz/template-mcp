"""
Phase 4 TDD Validation Models

Data models for TDD validation results and test generation.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TestCase:
    """Individual test case definition"""
    name: str
    description: str
    test_code: str
    expected_result: str
    test_type: str  # "unit", "integration", "edge_case", "error_handling"
    priority: int  # 1-5, where 5 is highest priority


@dataclass
class TDDIteration:
    """Single TDD iteration result"""
    iteration_number: int
    test_cases_generated: List[TestCase]
    test_execution_results: Dict[str, Any]
    failures: List[str]
    successes: List[str]
    reasoning: str
    next_actions: List[str]
    timestamp: datetime


@dataclass
class TDDValidationResult:
    """Complete TDD validation result"""
    kotlin_file_path: str
    mapping_report_path: str
    total_iterations: int
    iterations: List[TDDIteration]
    final_test_suite: str
    test_coverage_percentage: float
    all_tests_passing: bool
    final_recommendations: List[str]
    cursor_prompt: str
    execution_summary: Dict[str, Any]
    timestamp: datetime


@dataclass
class CursorPrompt:
    """Structured prompt for Cursor LLM execution"""
    title: str
    objective: str
    context: str
    reasoning: str
    chain_of_thought: List[str]
    instructions: List[str]
    expected_output: str
    validation_criteria: List[str]
    iteration_guidance: str