"""
Task Update Templates
Defines templates for generating new tasks based on different MCP tool outputs
"""

from typing import List, Dict, Any
from datetime import datetime

class TaskUpdateTemplates:
    """Templates for generating new tasks based on MCP tool outputs"""
    
    @staticmethod
    def get_tool_specific_requirements(tool_name: str, output_path: str, analysis: str) -> List[str]:
        """Generate new task requirements based on specific tool outputs"""
        
        if 'upload_api_specification' in tool_name.lower():
            return TaskUpdateTemplates._get_upload_requirements(output_path, analysis)
        elif 'analyze_json_fields_with_rag' in tool_name.lower():
            return TaskUpdateTemplates._get_analysis_requirements(output_path, analysis)
        elif 'reasoning_agent' in tool_name.lower():
            return TaskUpdateTemplates._get_reasoning_requirements(output_path, analysis)
        elif 'get_direct_api_mapping_prompt' in tool_name.lower():
            return TaskUpdateTemplates._get_mapping_prompt_requirements(output_path, analysis)
        elif 'phase3_generate_mapper' in tool_name.lower():
            return TaskUpdateTemplates._get_code_generation_requirements(output_path, analysis)
        elif 'phase3_quality_suite' in tool_name.lower():
            return TaskUpdateTemplates._get_quality_requirements(output_path, analysis)
        elif 'phase4_tdd_validation' in tool_name.lower():
            return TaskUpdateTemplates._get_validation_requirements(output_path, analysis)
        else:
            return TaskUpdateTemplates._get_generic_requirements(tool_name, output_path, analysis)
    
    @staticmethod
    def _get_upload_requirements(output_path: str, analysis: str) -> List[str]:
        """Requirements after uploading API specification"""
        return [
            f"Review uploaded API specification: {output_path}",
            "Validate API specification structure and completeness",
            "Identify key endpoints and data models for mapping",
            "Proceed with field analysis and semantic mapping"
        ]
    
    @staticmethod
    def _get_analysis_requirements(output_path: str, analysis: str) -> List[str]:
        """Requirements after JSON field analysis"""
        return [
            f"Review field analysis results: {output_path}",
            "Identify unmapped fields and data gaps",
            "Generate semantic mapping recommendations",
            "Create field mapping strategy document"
        ]
    
    @staticmethod
    def _get_reasoning_requirements(output_path: str, analysis: str) -> List[str]:
        """Requirements after reasoning agent execution"""
        return [
            f"Review reasoning agent report: {output_path}",
            "Validate endpoint mappings and field correlations",
            "Identify high-confidence vs. low-confidence mappings",
            "Generate verification checklist for manual review"
        ]
    
    @staticmethod
    def _get_mapping_prompt_requirements(output_path: str, analysis: str) -> List[str]:
        """Requirements after generating mapping prompt"""
        return [
            f"Execute generated mapping prompt: {output_path}",
            "Review mapping prompt quality and completeness",
            "Test prompt with sample data if available",
            "Refine prompt based on initial results"
        ]
    
    @staticmethod
    def _get_code_generation_requirements(output_path: str, analysis: str) -> List[str]:
        """Requirements after Kotlin code generation"""
        return [
            f"Review generated Kotlin mapper: {output_path}",
            "Run code quality suite and fix any issues",
            "Execute unit tests and validate functionality",
            "Perform security and performance review"
        ]
    
    @staticmethod
    def _get_quality_requirements(output_path: str, analysis: str) -> List[str]:
        """Requirements after quality suite execution"""
        return [
            f"Review quality suite results: {output_path}",
            "Fix identified code quality issues",
            "Address security vulnerabilities if any",
            "Optimize performance bottlenecks"
        ]
    
    @staticmethod
    def _get_validation_requirements(output_path: str, analysis: str) -> List[str]:
        """Requirements after TDD validation"""
        return [
            f"Review TDD validation results: {output_path}",
            "Fix failing tests and improve test coverage",
            "Validate business logic correctness",
            "Prepare for production deployment"
        ]
    
    @staticmethod
    def _get_generic_requirements(tool_name: str, output_path: str, analysis: str) -> List[str]:
        """Generic requirements for unknown tools"""
        return [
            f"Review {tool_name} output: {output_path}",
            f"Analyze results and identify next steps",
            "Update workflow documentation",
            "Proceed with next phase of integration"
        ]
    
    @staticmethod
    def get_priority_tasks(tool_name: str, output_path: str) -> List[str]:
        """Get high-priority tasks based on tool output"""
        if 'error' in output_path.lower() or 'failed' in output_path.lower():
            return [
                "🚨 URGENT: Fix tool execution error",
                "Review error logs and identify root cause",
                "Implement error handling improvements",
                "Re-run failed tool with corrected parameters"
            ]
        elif 'success' in output_path.lower() or 'completed' in output_path.lower():
            return [
                "✅ Continue with next workflow step",
                "Validate tool output quality",
                "Update progress documentation"
            ]
        else:
            return [
                "Review tool output and assess quality",
                "Identify any issues or improvements needed",
                "Proceed with next logical step"
            ]
    
    @staticmethod
    def get_phase_specific_tasks(current_phase: str, tool_name: str, output_path: str) -> List[str]:
        """Get tasks specific to current workflow phase"""
        
        if current_phase == "Phase 0 - Bootstrap":
            return [
                "Verify environment setup completion",
                "Test RAG system connectivity",
                "Validate all required files are accessible",
                "Proceed to Phase 1 - Data Extraction"
            ]
        elif current_phase == "Phase 1 - Data Extraction":
            return [
                "Review uploaded API specifications",
                "Validate data structure and completeness",
                "Identify key endpoints for mapping",
                "Proceed to Phase 2 - Analysis & Mapping"
            ]
        elif current_phase == "Phase 2 - Analysis & Mapping":
            return [
                "Review mapping analysis results",
                "Validate field correlations and mappings",
                "Identify unmapped fields and gaps",
                "Proceed to Phase 3 - Code Generation"
            ]
        elif current_phase == "Phase 3 - Code Generation":
            return [
                "Review generated Kotlin mapper code",
                "Run quality suite and fix issues",
                "Execute unit tests and validation",
                "Proceed to Phase 4 - TDD Validation"
            ]
        elif current_phase == "Phase 4 - TDD Validation":
            return [
                "Review TDD validation results",
                "Fix failing tests and improve coverage",
                "Validate business logic correctness",
                "Prepare for production deployment"
            ]
        else:
            return [
                "Review current phase progress",
                "Identify next steps and requirements",
                "Update phase documentation",
                "Proceed with workflow continuation"
            ]
    
    @staticmethod
    def generate_task_content(template_type: str, **kwargs) -> str:
        """Generate task content using templates"""
        
        templates = {
            'review_output': "Review {tool_name} output: {output_path}",
            'validate_data': "Validate {data_type} structure and completeness",
            'fix_issues': "Fix identified issues in {component}",
            'proceed_next': "Proceed to {next_step}",
            'generate_docs': "Generate documentation for {component}",
            'run_tests': "Run {test_type} tests for {component}",
            'optimize_performance': "Optimize performance of {component}",
            'security_review': "Perform security review of {component}"
        }
        
        template = templates.get(template_type, "Complete {task_description}")
        return template.format(**kwargs)
    
    @staticmethod
    def get_task_dependencies(tool_name: str, output_path: str) -> List[str]:
        """Get task dependencies based on tool output"""
        
        dependencies = []
        
        if 'upload' in tool_name.lower():
            dependencies.append("Verify file accessibility and format")
            dependencies.append("Validate API specification structure")
        
        elif 'analyze' in tool_name.lower():
            dependencies.append("Ensure data source is properly loaded")
            dependencies.append("Verify analysis parameters are correct")
        
        elif 'generate' in tool_name.lower():
            dependencies.append("Ensure mapping analysis is complete")
            dependencies.append("Verify target API specification is available")
        
        elif 'validate' in tool_name.lower():
            dependencies.append("Ensure generated code is available")
            dependencies.append("Verify test data is properly configured")
        
        return dependencies
