"""
Phase 3 MCP Tool: Direct Field Mapper

This tool handles direct 1:1 field mappings where source fields
directly map to target fields without transformation.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from pydantic import BaseModel, Field
from .phase3_models import (
    MappingReport, FieldMapping, DirectMappingCode, 
    KotlinCodeRequest, MappingCategory
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


class DirectMappingGenerator:
    """Generates Kotlin code for direct field mappings."""
    
    def __init__(self):
        self.model = "qwen/qwen3-coder:free"  # Free model from OpenRouter
        
    def categorize_mappings(self, report: MappingReport) -> Tuple[List[FieldMapping], List[FieldMapping], List[FieldMapping]]:
        """
        Categorize mappings into direct, type_conversion, and complex_logic.
        
        Returns:
            Tuple of (direct_mappings, type_conversions, complex_mappings)
        """
        direct_mappings = []
        type_conversions = []
        complex_mappings = []
        
        for mapping in report.mappings:
            if mapping.category.category == "direct":
                direct_mappings.append(mapping)
            elif mapping.category.category == "type_conversion":
                type_conversions.append(mapping)
            elif mapping.category.category == "complex_logic":
                complex_mappings.append(mapping)
                
        return direct_mappings, type_conversions, complex_mappings
    
    def generate_direct_mapping_code(self, mappings: List[FieldMapping], request: KotlinCodeRequest) -> str:
        """Generate Kotlin code for direct mappings using LLM."""
        
        if not mappings:
            return "// No direct mappings found"
        
        # Prepare mapping data for the prompt
        mapping_data = []
        for m in mappings:
            mapping_data.append({
                "source": m.source_field,
                "target": m.target_field,
                "source_type": m.source_type,
                "target_type": m.target_type,
                "null_safe": m.null_safe,
                "default_value": m.default_value
            })
        
        prompt = f"""You are a senior Kotlin developer generating direct field mappings for a data mapper.
Generate ONLY the Kotlin code for these direct 1:1 field mappings. No explanations, just code.

Company: {request.company_name}
Project: {request.project_name}
Backend: {request.backend_name}

Direct Mappings to Generate:
{json.dumps(mapping_data, indent=2)}

Requirements:
1. Use Kotlin's null-safe operators (?., ?:) where null_safe is true
2. Apply default values where specified
3. Generate clean, idiomatic Kotlin code
4. Follow this exact format for each mapping:
   - For simple fields: targetField = source.sourceField
   - For nested fields: targetField = source?.nested?.field
   - With defaults: targetField = source?.field ?: defaultValue

Generate the mapping code block that would go inside a mapper function like:
fun mapToTarget(source: SourceType): TargetType = TargetType(
    // YOUR GENERATED MAPPINGS HERE
)

Output ONLY the field mapping lines, nothing else."""

        try:
            response = get_llm_response(prompt, model=self.model, max_tokens=2000)
            return response.strip()
        except Exception as e:
            logger.error(f"Error generating direct mapping code: {e}")
            return f"// Error generating mappings: {str(e)}"
    
    def integrate_into_mapper(self, mapping_code: str, template_path: Optional[str] = None) -> str:
        """Integrate direct mappings into the mapper template."""
        
        if not template_path:
            # Use default template
            template = self._get_default_mapper_template()
        else:
            with open(template_path, 'r') as f:
                template = f.read()
        
        # Replace the mapping placeholder with generated code
        integrated = template.replace(
            "// --- START MAPPING ---",
            "// --- START MAPPING ---\n" + mapping_code
        )
        
        return integrated
    
    def _get_default_mapper_template(self) -> str:
        """Get the default mapper template."""
        return """
/**
 * Direct Field Mapper
 * Generated for 1:1 field mappings without transformation
 */
class DirectFieldMapper {
    
    fun mapToTarget(source: SourceDTO): TargetDTO = TargetDTO(
        // --- START MAPPING ---
        // --- END MAPPING ---
    )
}
"""


def generate_direct_mappings(
    mapping_report_path: str,
    ground_truth_path: Optional[str] = None,
    output_directory: str = "outputs/phase3",
    **kwargs
) -> DirectMappingCode:
    """
    MCP Tool Entry Point: Generate Kotlin code for direct field mappings.
    
    Args:
        mapping_report_path: Path to the mapping report from Phase 2
        ground_truth_path: Optional path to ground truth verification data
        output_directory: Directory to save generated code
        **kwargs: Additional configuration (company_name, project_name, etc.)
    
    Returns:
        DirectMappingCode with generated Kotlin code
    """
    logger.info(f"Starting direct mapping generation from: {mapping_report_path}")
    
    # Load the mapping report
    try:
        with open(mapping_report_path, 'r') as f:
            report_content = f.read()
        
        # Parse the report to extract mappings
        # This is simplified - you'd parse the actual markdown/JSON format
        report = _parse_mapping_report(report_content)
        
    except Exception as e:
        logger.error(f"Failed to load mapping report: {e}")
        return DirectMappingCode(
            kotlin_code=f"// Error: Failed to load mapping report: {str(e)}",
            mapped_fields=[],
            mapping_count=0
        )
    
    # Create request object
    request = KotlinCodeRequest(
        mapping_report_path=mapping_report_path,
        ground_truth_path=ground_truth_path,
        output_directory=output_directory,
        **kwargs
    )
    
    # Initialize generator
    generator = DirectMappingGenerator()
    
    # Categorize mappings
    direct_mappings, _, _ = generator.categorize_mappings(report)
    
    if not direct_mappings:
        logger.info("No direct mappings found in report")
        return DirectMappingCode(
            kotlin_code="// No direct mappings found",
            mapped_fields=[],
            mapping_count=0
        )
    
    # Generate code for direct mappings
    mapping_code = generator.generate_direct_mapping_code(direct_mappings, request)
    
    # Integrate into full mapper
    full_code = generator.integrate_into_mapper(mapping_code)
    
    # Save to file
    output_path = Path(output_directory)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_path / f"DirectMapper_{timestamp}.kt"
    
    with open(output_file, 'w') as f:
        f.write(full_code)
    
    logger.info(f"Generated direct mapper code saved to: {output_file}")
    
    # Extract mapped field names
    mapped_fields = [m.source_field for m in direct_mappings]
    
    return DirectMappingCode(
        kotlin_code=full_code,
        mapped_fields=mapped_fields,
        mapping_count=len(direct_mappings)
    )


def _parse_mapping_report(content: str) -> MappingReport:
    """
    Parse the mapping report from markdown/text format.
    This is a simplified parser - implement based on actual report format.
    """
    # For now, create a mock report with example data
    # In production, parse the actual markdown content
    
    mappings = []
    
    # Example parsing logic (replace with actual parsing)
    if "Direct Mappings:" in content:
        # Extract direct mappings section
        # Parse each mapping line
        pass
    
    # Return mock data for testing
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
                    reason="Direct 1:1 mapping",
                    confidence=1.0
                )
            ),
            FieldMapping(
                source_field="employee.email",
                target_field="contactEmail",
                source_type="string",
                target_type="string",
                category=MappingCategory(
                    category="direct",
                    reason="Direct field mapping",
                    confidence=0.95
                ),
                null_safe=True,
                default_value='""'
            )
        ]
    )


# MCP Tool Registration
def register_tool():
    """Register this tool with the MCP server."""
    return {
        "name": "phase3_generate_direct_mappings",
        "description": "Generate Kotlin code for direct 1:1 field mappings from Phase 2 report",
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
                },
                "company_name": {
                    "type": "string",
                    "description": "Company name for package",
                    "default": "flip"
                },
                "project_name": {
                    "type": "string",
                    "description": "Project name for package",
                    "default": "integrations"
                }
            },
            "required": ["mapping_report_path"]
        },
        "handler": generate_direct_mappings
    }