"""
Phase 3 MCP Tool: Complex Logic Mapper

This tool handles fields that require additional logic, transformations,
business rules, or multi-field combinations to map correctly.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from pydantic import BaseModel, Field
from .phase3_models import (
    MappingReport, FieldMapping, ComplexMappingCode,
    KotlinCodeRequest
)

# Import the LLM client with fallback
try:
    from tools.shared_utilities.llm_client import get_llm_response
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


class ComplexLogicGenerator:
    """Generates Kotlin code for complex field mappings requiring custom logic."""
    
    def __init__(self):
        self.model = "qwen/qwen3-coder:free"  # Free model from OpenRouter
        self.logic_patterns = self._load_logic_patterns()
    
    def _load_logic_patterns(self) -> Dict[str, str]:
        """Load common complex logic patterns."""
        return {
            "concatenation": "Combine multiple fields",
            "calculation": "Mathematical operations on fields",
            "conditional": "If-else logic based on field values",
            "lookup": "Map values using lookup tables",
            "transformation": "Complex data transformation",
            "validation": "Business rule validation",
            "aggregation": "Aggregate multiple values",
            "parsing": "Parse complex string formats",
            "normalization": "Normalize data format",
            "enrichment": "Add derived/calculated fields"
        }
    
    def analyze_complexity(self, mapping: FieldMapping) -> Dict[str, Any]:
        """Analyze the complexity of a mapping and determine logic type."""
        
        complexity_info = {
            "complexity_level": "high",  # low, medium, high
            "logic_types": [],
            "requires_context": False,
            "requires_external_data": False,
            "multi_field_dependency": False
        }
        
        # Analyze transformation notes for clues
        if mapping.transformation_notes:
            notes_lower = mapping.transformation_notes.lower()
            
            # Check for various complexity indicators
            if any(word in notes_lower for word in ["combine", "concatenate", "merge"]):
                complexity_info["logic_types"].append("concatenation")
                complexity_info["multi_field_dependency"] = True
            
            if any(word in notes_lower for word in ["calculate", "compute", "derive"]):
                complexity_info["logic_types"].append("calculation")
            
            if any(word in notes_lower for word in ["if", "when", "condition", "based on"]):
                complexity_info["logic_types"].append("conditional")
            
            if any(word in notes_lower for word in ["lookup", "map", "translate"]):
                complexity_info["logic_types"].append("lookup")
                complexity_info["requires_external_data"] = True
            
            if any(word in notes_lower for word in ["validate", "check", "verify"]):
                complexity_info["logic_types"].append("validation")
            
            if any(word in notes_lower for word in ["parse", "extract", "split"]):
                complexity_info["logic_types"].append("parsing")
        
        # Default to transformation if no specific type identified
        if not complexity_info["logic_types"]:
            complexity_info["logic_types"].append("transformation")
        
        return complexity_info
    
    def generate_complex_function(
        self, 
        mapping: FieldMapping,
        complexity_info: Dict[str, Any]
    ) -> Tuple[str, str]:
        """
        Generate a Kotlin function for complex logic mapping.
        
        Returns:
            Tuple of (function_code, function_name)
        """
        
        # Create function name
        func_name = f"map{self._to_camel_case(mapping.source_field)}To{self._to_camel_case(mapping.target_field)}"
        
        # Build prompt based on complexity analysis
        logic_desc = ", ".join(complexity_info["logic_types"])
        
        prompt = f"""You are a senior Kotlin developer. Generate a function for complex field mapping.

Mapping Details:
- Source Field: {mapping.source_field} ({mapping.source_type})
- Target Field: {mapping.target_field} ({mapping.target_type})
- Logic Types: {logic_desc}
- Transformation Notes: {mapping.transformation_notes or "Apply complex business logic"}
- Multi-field Dependency: {complexity_info['multi_field_dependency']}
- Requires External Data: {complexity_info['requires_external_data']}

Requirements:
1. Create a well-named function that clearly expresses its purpose
2. Handle all edge cases and null values
3. Add comprehensive KDoc documentation
4. Use Kotlin best practices (when expressions, scope functions, etc.)
5. Make the function pure if possible (no side effects)
6. Include parameter validation if needed
7. Return appropriate default values for error cases

Generate ONLY the Kotlin function code:

Example format:
```kotlin
/**
 * Maps source field to target using complex logic
 * @param source The source data object
 * @param context Optional context for mapping
 * @return Mapped target value
 */
fun {func_name}(source: SourceType, context: MappingContext? = null): TargetType {{
    // Implementation
}}
```

Output the complete function:"""

        try:
            response = get_llm_response(prompt, model=self.model, max_tokens=1000)
            # Clean up response
            code = response.strip()
            if code.startswith("```kotlin"):
                code = code[9:]
            if code.endswith("```"):
                code = code[:-3]
            return code.strip(), func_name
        except Exception as e:
            logger.error(f"Error generating complex function: {e}")
            # Return a TODO function
            return self._generate_todo_function(mapping, func_name), func_name
    
    def _generate_todo_function(self, mapping: FieldMapping, func_name: str) -> str:
        """Generate a TODO placeholder function."""
        return f"""
/**
 * TODO: Implement complex mapping logic
 * Maps {mapping.source_field} ({mapping.source_type}) to {mapping.target_field} ({mapping.target_type})
 * Notes: {mapping.transformation_notes or "Complex business logic required"}
 */
fun {func_name}(source: Any): Any {{
    TODO("Implement complex mapping from {mapping.source_field} to {mapping.target_field}")
}}"""
    
    def _to_camel_case(self, field_path: str) -> str:
        """Convert field path to CamelCase."""
        parts = field_path.replace(".", "_").replace("-", "_").split("_")
        return "".join(part.capitalize() for part in parts)
    
    def generate_all_complex_functions(
        self,
        complex_mappings: List[FieldMapping]
    ) -> Tuple[str, Dict[str, str]]:
        """
        Generate all complex mapping functions.
        
        Returns:
            Tuple of (all_functions_code, integration_points_map)
        """
        
        if not complex_mappings:
            return "// No complex mappings needed", {}
        
        functions = []
        integration_points = {}
        
        # Group by complexity type for better organization
        grouped = {}
        for mapping in complex_mappings:
            complexity = self.analyze_complexity(mapping)
            main_type = complexity["logic_types"][0] if complexity["logic_types"] else "transformation"
            
            if main_type not in grouped:
                grouped[main_type] = []
            grouped[main_type].append((mapping, complexity))
        
        # Generate functions for each group
        for logic_type, mappings_and_complexity in grouped.items():
            functions.append(f"\n// ========== {logic_type.title()} Functions ==========")
            
            for mapping, complexity in mappings_and_complexity:
                func_code, func_name = self.generate_complex_function(mapping, complexity)
                functions.append(func_code)
                
                # Store integration point
                integration_points[mapping.target_field] = func_name
        
        return "\n\n".join(functions), integration_points
    
    def create_integrated_mapper(
        self,
        complex_functions: str,
        integration_points: Dict[str, str],
        all_mappings: List[FieldMapping]
    ) -> str:
        """Create a complete mapper integrating all complex functions."""
        
        prompt = f"""You are a senior Kotlin developer. Create a complete mapper class that integrates complex mapping functions.

Complex Functions Available:
{complex_functions}

Integration Points (target_field -> function_name):
{json.dumps(integration_points, indent=2)}

All Field Mappings:
{json.dumps([{
    "source": m.source_field,
    "target": m.target_field,
    "category": m.category.category
} for m in all_mappings], indent=2)}

Requirements:
1. Create a complete mapper class with all complex functions as private methods
2. Main mapping function should call complex functions where needed
3. Handle direct mappings inline for non-complex fields
4. Follow Kotlin best practices and conventions
5. Include proper error handling and logging
6. Make the class testable with dependency injection if needed

Generate ONLY the complete Kotlin mapper class:"""

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
            logger.error(f"Error creating integrated mapper: {e}")
            return self._get_default_complex_mapper(complex_functions, integration_points)
    
    def _get_default_complex_mapper(
        self,
        complex_functions: str,
        integration_points: Dict[str, str]
    ) -> str:
        """Get default mapper template with complex functions."""
        
        # Build integration calls
        integration_calls = []
        for target_field, func_name in integration_points.items():
            integration_calls.append(
                f"    {target_field} = {func_name}(source),"
            )
        
        return f"""
/**
 * Complex Logic Mapper
 * Handles field mappings requiring custom business logic and transformations
 */
class ComplexLogicMapper {{
    
    fun mapWithComplexLogic(source: SourceDTO): TargetDTO {{
        return TargetDTO(
            // Complex field mappings
{chr(10).join(integration_calls)}
            // TODO: Add remaining field mappings
        )
    }}
    
    // ========== Complex Mapping Functions ==========
    {complex_functions}
}}"""


def generate_complex_mappings(
    mapping_report_path: str,
    ground_truth_path: Optional[str] = None,
    output_directory: str = "outputs/phase3",
    **kwargs
) -> ComplexMappingCode:
    """
    MCP Tool Entry Point: Generate Kotlin code for complex logic mappings.
    
    Args:
        mapping_report_path: Path to the mapping report from Phase 2
        ground_truth_path: Optional path to ground truth verification data
        output_directory: Directory to save generated code
        **kwargs: Additional configuration
    
    Returns:
        ComplexMappingCode with generated functions and integration points
    """
    logger.info(f"Starting complex mapping generation from: {mapping_report_path}")
    
    # Load the mapping report
    try:
        with open(mapping_report_path, 'r') as f:
            report_content = f.read()
        
        # Parse the report to extract mappings
        report = _parse_mapping_report(report_content)
        
    except Exception as e:
        logger.error(f"Failed to load mapping report: {e}")
        return ComplexMappingCode(
            kotlin_code=f"// Error: Failed to load mapping report: {str(e)}",
            function_names=[],
            integration_points={}
        )
    
    # Initialize generator
    generator = ComplexLogicGenerator()
    
    # Extract complex logic mappings
    complex_mappings = [
        m for m in report.mappings 
        if m.category.category == "complex_logic"
    ]
    
    if not complex_mappings:
        logger.info("No complex logic mappings found")
        return ComplexMappingCode(
            kotlin_code="// No complex mappings needed",
            function_names=[],
            integration_points={}
        )
    
    # Generate all complex functions
    complex_functions, integration_points = generator.generate_all_complex_functions(
        complex_mappings
    )
    
    # Create integrated mapper
    integrated_mapper = generator.create_integrated_mapper(
        complex_functions,
        integration_points,
        report.mappings  # Pass all mappings for context
    )
    
    # Save to files
    output_path = Path(output_directory)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save complex functions separately
    func_file = output_path / f"ComplexFunctions_{timestamp}.kt"
    with open(func_file, 'w') as f:
        f.write(complex_functions)
    
    # Save integrated mapper
    mapper_file = output_path / f"ComplexLogicMapper_{timestamp}.kt"
    with open(mapper_file, 'w') as f:
        f.write(integrated_mapper)
    
    logger.info(f"Generated complex functions saved to: {func_file}")
    logger.info(f"Integrated mapper saved to: {mapper_file}")
    
    # Extract function names
    function_names = list(integration_points.values())
    
    return ComplexMappingCode(
        kotlin_code=integrated_mapper,
        function_names=function_names,
        integration_points=integration_points
    )


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
            # Some direct mappings
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
            # Complex logic mappings
            FieldMapping(
                source_field="employee.firstName",
                target_field="fullName",
                source_type="string",
                target_type="string",
                category=MappingCategory(
                    category="complex_logic",
                    reason="Requires concatenation with lastName",
                    confidence=0.85
                ),
                transformation_notes="Concatenate firstName and lastName with space"
            ),
            FieldMapping(
                source_field="employee.birthDate",
                target_field="age",
                source_type="string",
                target_type="int",
                category=MappingCategory(
                    category="complex_logic",
                    reason="Calculate age from birth date",
                    confidence=0.9
                ),
                transformation_notes="Calculate age in years from birthDate"
            ),
            FieldMapping(
                source_field="employee.department",
                target_field="organizationUnit",
                source_type="string",
                target_type="OrgUnit",
                category=MappingCategory(
                    category="complex_logic",
                    reason="Requires department code lookup and transformation",
                    confidence=0.75
                ),
                transformation_notes="Map department name to organization unit using lookup table"
            )
        ]
    )


# MCP Tool Registration
def register_tool():
    """Register this tool with the MCP server."""
    return {
        "name": "phase3_generate_complex_mappings",
        "description": "Generate Kotlin code for complex logic field mappings",
        "input_schema": {
            "type": "object",
            "properties": {
                "mapping_report_path": {
                    "type": "string",
                    "description": "Path to the mapping report file"
                },
                "ground_truth_path": {
                    "type": "string",
                    "description": "Optional path to ground truth verification file"
                },
                "output_directory": {
                    "type": "string",
                    "description": "Directory to save generated code",
                    "default": "outputs/phase3"
                }
            },
            "required": ["mapping_report_path"]
        },
        "handler": generate_complex_mappings
    }
