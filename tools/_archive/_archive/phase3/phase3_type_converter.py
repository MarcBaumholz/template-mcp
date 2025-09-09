"""
Phase 3 MCP Tool: Type Converter

This tool handles second-level mappings that require data type conversions,
such as string to int, date formatting, enum conversions, etc.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime

from pydantic import BaseModel, Field
from .phase3_models import (
    MappingReport, FieldMapping, TypeConversionCode,
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


class TypeConversionGenerator:
    """Generates Kotlin code for data type conversions."""
    
    def __init__(self):
        self.model = "qwen/qwen3-coder:free"  # Free model from OpenRouter
        self.conversion_patterns = self._load_conversion_patterns()
    
    def _load_conversion_patterns(self) -> Dict[str, str]:
        """Load common conversion patterns."""
        return {
            "string_to_int": "toIntOrNull() ?: 0",
            "string_to_double": "toDoubleOrNull() ?: 0.0",
            "string_to_boolean": "toBoolean()",
            "int_to_string": "toString()",
            "date_to_string": "format(DateTimeFormatter.ISO_DATE)",
            "string_to_date": "LocalDate.parse(this)",
            "string_to_datetime": "OffsetDateTime.parse(this)",
            "enum_conversion": "when (this) { /* enum mapping */ }"
        }
    
    def identify_conversion_type(self, source_type: str, target_type: str) -> str:
        """Identify the type of conversion needed."""
        conversion_key = f"{source_type.lower()}_to_{target_type.lower()}"
        
        # Check for direct pattern match
        if conversion_key in self.conversion_patterns:
            return conversion_key
        
        # Check for enum conversions
        if "enum" in source_type.lower() or "enum" in target_type.lower():
            return "enum_conversion"
        
        # Check for date/time conversions
        if any(dt in source_type.lower() for dt in ["date", "time", "timestamp"]) or \
           any(dt in target_type.lower() for dt in ["date", "time", "timestamp"]):
            return "datetime_conversion"
        
        # Default to custom conversion
        return "custom_conversion"
    
    def generate_conversion_function(self, mapping: FieldMapping) -> str:
        """Generate a Kotlin conversion function for a specific field mapping."""
        
        conversion_type = self.identify_conversion_type(
            mapping.source_type, 
            mapping.target_type
        )
        
        prompt = f"""You are a senior Kotlin developer. Generate a type conversion function.

Source Field: {mapping.source_field}
Source Type: {mapping.source_type}
Target Field: {mapping.target_field}
Target Type: {mapping.target_type}
Conversion Type: {conversion_type}

Requirements:
1. Create an extension function for clean syntax
2. Handle null values safely
3. Provide sensible defaults for conversion failures
4. Use Kotlin idioms (when expressions, elvis operator, safe calls)
5. Add brief KDoc comment explaining the conversion

Generate ONLY the Kotlin function code, no explanations:

Example format:
```kotlin
/**
 * Converts source field to target type
 */
fun SourceType.toTargetType(): TargetType {{
    // conversion logic
}}
```

Output the function code only:"""

        try:
            response = get_llm_response(prompt, model=self.model, max_tokens=500)
            # Clean up response
            code = response.strip()
            if code.startswith("```kotlin"):
                code = code[9:]  # Remove ```kotlin
            if code.endswith("```"):
                code = code[:-3]  # Remove ```
            return code.strip()
        except Exception as e:
            logger.error(f"Error generating conversion function: {e}")
            return f"""
/**
 * Auto-generated conversion for {mapping.source_field} -> {mapping.target_field}
 * TODO: Implement proper conversion from {mapping.source_type} to {mapping.target_type}
 */
fun convert_{mapping.source_field.replace('.', '_')}(): {mapping.target_type} {{
    TODO("Implement conversion from {mapping.source_type} to {mapping.target_type}")
}}"""
    
    def generate_conversion_functions(self, conversions: List[FieldMapping]) -> Tuple[str, List[str]]:
        """Generate all conversion functions needed."""
        
        if not conversions:
            return "// No type conversions needed", []
        
        functions = []
        function_names = []
        
        # Group conversions by type for better organization
        conversion_groups = {}
        for mapping in conversions:
            conv_type = self.identify_conversion_type(
                mapping.source_type, 
                mapping.target_type
            )
            if conv_type not in conversion_groups:
                conversion_groups[conv_type] = []
            conversion_groups[conv_type].append(mapping)
        
        # Generate functions for each group
        for conv_type, mappings in conversion_groups.items():
            functions.append(f"\n// {conv_type.replace('_', ' ').title()} Conversions")
            
            for mapping in mappings:
                func_code = self.generate_conversion_function(mapping)
                functions.append(func_code)
                
                # Extract function name from generated code
                func_name = f"convert_{mapping.source_field.replace('.', '_')}"
                function_names.append(func_name)
        
        return "\n\n".join(functions), function_names
    
    def integrate_conversions_into_mapper(
        self, 
        conversions: List[FieldMapping],
        conversion_functions: str,
        template_path: Optional[str] = None
    ) -> str:
        """Integrate conversion functions and their usage into the mapper."""
        
        prompt = f"""You are a senior Kotlin developer. Integrate type conversion functions into a mapper.

Conversion Functions Generated:
{conversion_functions}

Field Mappings Requiring Conversions:
{json.dumps([{
    "source": m.source_field,
    "target": m.target_field,
    "source_type": m.source_type,
    "target_type": m.target_type
} for m in conversions], indent=2)}

Generate a complete Kotlin mapper that:
1. Includes all conversion functions as private methods or extensions
2. Uses these conversions in the main mapping function
3. Follows Kotlin best practices
4. Handles null safety

Output ONLY the complete Kotlin code for the mapper class:"""

        try:
            response = get_llm_response(prompt, model=self.model, max_tokens=3000)
            # Clean up response
            code = response.strip()
            if code.startswith("```kotlin"):
                code = code[9:]
            if code.endswith("```"):
                code = code[:-3]
            return code.strip()
        except Exception as e:
            logger.error(f"Error integrating conversions: {e}")
            return self._get_default_conversion_mapper(conversion_functions)
    
    def _get_default_conversion_mapper(self, conversion_functions: str) -> str:
        """Get default mapper template with conversions."""
        return f"""
/**
 * Type Conversion Mapper
 * Handles data type conversions between source and target systems
 */
class TypeConversionMapper {{
    
    fun mapWithConversions(source: SourceDTO): TargetDTO {{
        return TargetDTO(
            // TODO: Apply conversions here
            // Example: field = source.field.toTargetType()
        )
    }}
    
    // Conversion Functions
    {conversion_functions}
}}"""


def generate_type_conversions(
    mapping_report_path: str,
    ground_truth_path: Optional[str] = None,
    output_directory: str = "outputs/phase3",
    **kwargs
) -> TypeConversionCode:
    """
    MCP Tool Entry Point: Generate Kotlin code for type conversion mappings.
    
    Args:
        mapping_report_path: Path to the mapping report from Phase 2
        ground_truth_path: Optional path to ground truth verification data
        output_directory: Directory to save generated code
        **kwargs: Additional configuration
    
    Returns:
        TypeConversionCode with generated conversion functions and integrated code
    """
    logger.info(f"Starting type conversion generation from: {mapping_report_path}")
    
    # Load the mapping report
    try:
        with open(mapping_report_path, 'r') as f:
            report_content = f.read()
        
        # Parse the report to extract mappings
        report = _parse_mapping_report(report_content)
        
    except Exception as e:
        logger.error(f"Failed to load mapping report: {e}")
        return TypeConversionCode(
            kotlin_code=f"// Error: Failed to load mapping report: {str(e)}",
            conversion_functions=[],
            integrated_code=""
        )
    
    # Initialize generator
    generator = TypeConversionGenerator()
    
    # Extract type conversion mappings
    type_conversions = [
        m for m in report.mappings 
        if m.category.category == "type_conversion"
    ]
    
    if not type_conversions:
        logger.info("No type conversion mappings found")
        return TypeConversionCode(
            kotlin_code="// No type conversions needed",
            conversion_functions=[],
            integrated_code="// No type conversions needed"
        )
    
    # Generate conversion functions
    conversion_code, function_names = generator.generate_conversion_functions(type_conversions)
    
    # Integrate into mapper
    integrated_code = generator.integrate_conversions_into_mapper(
        type_conversions,
        conversion_code
    )
    
    # Save to files
    output_path = Path(output_directory)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save conversion functions separately
    conv_file = output_path / f"TypeConversions_{timestamp}.kt"
    with open(conv_file, 'w') as f:
        f.write(conversion_code)
    
    # Save integrated mapper
    mapper_file = output_path / f"TypeConversionMapper_{timestamp}.kt"
    with open(mapper_file, 'w') as f:
        f.write(integrated_code)
    
    logger.info(f"Generated type conversions saved to: {conv_file}")
    logger.info(f"Integrated mapper saved to: {mapper_file}")
    
    return TypeConversionCode(
        kotlin_code=conversion_code,
        conversion_functions=function_names,
        integrated_code=integrated_code
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
            FieldMapping(
                source_field="employee.startDate",
                target_field="hireDate",
                source_type="string",
                target_type="LocalDate",
                category=MappingCategory(
                    category="type_conversion",
                    reason="String to date conversion required",
                    confidence=0.9
                )
            ),
            FieldMapping(
                source_field="employee.salary",
                target_field="compensation",
                source_type="string",
                target_type="Double",
                category=MappingCategory(
                    category="type_conversion",
                    reason="String to double conversion required",
                    confidence=0.95
                )
            ),
            FieldMapping(
                source_field="employee.status",
                target_field="employmentStatus",
                source_type="string",
                target_type="StatusEnum",
                category=MappingCategory(
                    category="type_conversion",
                    reason="String to enum conversion required",
                    confidence=0.85
                )
            )
        ]
    )


# MCP Tool Registration
def register_tool():
    """Register this tool with the MCP server."""
    return {
        "name": "phase3_generate_type_conversions",
        "description": "Generate Kotlin code for data type conversion mappings",
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
        "handler": generate_type_conversions
    }
