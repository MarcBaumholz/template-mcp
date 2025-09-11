"""
Flexible Prompt Templates for MCP Tools
Provides domain-agnostic, configurable prompts without hardcoded values
"""

from typing import Dict, Any, Optional, List
from enum import Enum
from .config_manager import get_config, BusinessDomain


class PromptType(Enum):
    """Types of prompts available"""
    FIELD_EXTRACTION = "field_extraction"
    FIELD_DESCRIPTION = "field_description"
    API_MAPPING = "api_mapping"
    CODE_GENERATION = "code_generation"
    VERIFICATION = "verification"


class PromptTemplate:
    """Base class for prompt templates"""
    
    def __init__(self, prompt_type: PromptType, template: str, variables: List[str]):
        self.prompt_type = prompt_type
        self.template = template
        self.variables = variables
    
    def render(self, **kwargs) -> str:
        """Render template with provided variables"""
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing required variable: {e}")


class PromptTemplateManager:
    """Manages prompt templates for different use cases"""
    
    def __init__(self):
        self.templates = self._initialize_templates()
    
    def _initialize_templates(self) -> Dict[PromptType, PromptTemplate]:
        """Initialize all prompt templates"""
        return {
            PromptType.FIELD_EXTRACTION: PromptTemplate(
                PromptType.FIELD_EXTRACTION,
                """You are given JSON payload data. Extract the relevant data fields for API mapping.

Use your judgment to determine what fields are relevant based on the data structure and content.
Consider the business context and what would be useful for API integration.

EXCLUDE only obvious system/metadata fields like:
- Pagination (page, pageSize, total)
- System metadata (metadata, links, etc.)

INCLUDE any field that contains business data or would be useful for mapping.

Business Context: {business_context}

JSON:
{json_data}

Return ONLY valid JSON with relevant data fields:
{{
  "fields": ["field1", "field2", "nested.field", ...]
}}""",
                ["business_context", "json_data"]
            ),
            
            PromptType.FIELD_DESCRIPTION: PromptTemplate(
                PromptType.FIELD_DESCRIPTION,
                """For each field, provide a concise semantic_description (<=20 words) and a short use_case (<=20 words).
Return ONLY valid JSON mapping field -> {{semantic_description, use_case}}.

Business Context: {business_context}

Fields: {fields}
Context JSON:
{json_data}

Example: {{
  "fieldName": {{"semantic_description": "Brief description", "use_case": "How it's used"}}
}}""",
                ["business_context", "fields", "json_data"]
            ),
            
            PromptType.API_MAPPING: PromptTemplate(
                PromptType.API_MAPPING,
                """Analyze the following source fields and map them to the target API specification.

Business Context: {business_context}
Source Fields: {source_fields}
API Specification: {api_spec}

Instructions:
1. Identify direct field matches
2. Find semantic equivalents
3. Suggest transformations where needed
4. Note any unmapped fields
5. Provide confidence scores for each mapping

Return a structured analysis with:
- Direct matches
- Semantic matches  
- Transformation suggestions
- Unmapped fields
- Confidence scores""",
                ["business_context", "source_fields", "api_spec"]
            ),
            
            PromptType.CODE_GENERATION: PromptTemplate(
                PromptType.CODE_GENERATION,
                """You are an expert {language} backend engineer. Generate a complete {architecture_pattern} implementation.

Business Context: {business_context}
Package: {package_name}
Company: {company_name}
Project: {project_name}

CODING_RULES:
1) Architecture: {architecture_pattern} with proper separation of concerns
2) Security & Logging: Implement proper security and logging
3) Error handling: Comprehensive error handling with meaningful messages
4) Null-safety: Handle null values appropriately
5) Ground-truth discipline: Only use verified fields from the mapping analysis
6) Output-only: Return only {language} code (no markdown)

FIELD_MAPPING_ANALYSIS:
{mapping_info}

TEMPLATE_SCAFFOLD:
{template_text}

Instructions:
1) Replace placeholders and fill mapping blocks
2) Ensure imports and classes are consistent
3) Return only the complete {language} code file""",
                ["language", "architecture_pattern", "business_context", "package_name", 
                 "company_name", "project_name", "mapping_info", "template_text"]
            ),
            
            PromptType.VERIFICATION: PromptTemplate(
                PromptType.VERIFICATION,
                """Verify the following API mappings against the OpenAPI specification.

Business Context: {business_context}
Mappings to Verify: {mappings}
API Specification: {api_spec}

Instructions:
1. Check if each claimed endpoint exists in the spec
2. Verify field mappings are correct
3. Identify any hallucinations or incorrect mappings
4. Provide specific feedback for each mapping
5. Suggest corrections where needed

Return verification results with:
- Verified mappings
- Incorrect mappings
- Suggestions for corrections
- Confidence levels""",
                ["business_context", "mappings", "api_spec"]
            )
        }
    
    def get_template(self, prompt_type: PromptType) -> PromptTemplate:
        """Get template for specific prompt type"""
        return self.templates[prompt_type]
    
    def render_prompt(self, prompt_type: PromptType, **kwargs) -> str:
        """Render prompt with current configuration"""
        template = self.get_template(prompt_type)
        
        # Add default values from configuration
        try:
            config = get_config()
            defaults = {
                "business_context": config.business_domain.value.replace("_", " ").title(),
                "language": config.code_generation.default_language,
                "architecture_pattern": config.code_generation.default_framework,
                "package_name": config.code_generation.default_package,
                "company_name": config.code_generation.default_company,
                "project_name": config.code_generation.default_project
            }
        except Exception:
            # Fallback defaults if config is not available
            defaults = {
                "business_context": "Generic",
                "language": "kotlin",
                "architecture_pattern": "micronaut",
                "package_name": "com.company.integrations",
                "company_name": "company",
                "project_name": "integrations"
            }
        
        # Merge defaults with provided kwargs
        merged_kwargs = {**defaults, **kwargs}
        
        return template.render(**merged_kwargs)
    
    def add_custom_template(self, prompt_type: PromptType, template: str, variables: List[str]):
        """Add custom template for specific use case"""
        self.templates[prompt_type] = PromptTemplate(prompt_type, template, variables)
    
    def get_business_context_prompts(self, domain: BusinessDomain) -> Dict[str, str]:
        """Get domain-specific context prompts"""
        context_prompts = {
            BusinessDomain.HR: {
                "description": "Human Resources management including employees, absences, payroll, and benefits",
                "key_concepts": "employee data, time tracking, leave management, performance reviews"
            },
            BusinessDomain.RETAIL: {
                "description": "Retail and e-commerce including products, inventory, orders, and customers",
                "key_concepts": "product catalog, stock management, order processing, customer data"
            },
            BusinessDomain.FINANCE: {
                "description": "Financial services including transactions, accounts, payments, and reporting",
                "key_concepts": "transaction processing, account management, payment systems, financial reporting"
            },
            BusinessDomain.HEALTHCARE: {
                "description": "Healthcare management including patients, appointments, medical records, and billing",
                "key_concepts": "patient data, appointment scheduling, medical records, insurance billing"
            },
            BusinessDomain.MANUFACTURING: {
                "description": "Manufacturing and production including orders, inventory, quality control, and logistics",
                "key_concepts": "production orders, inventory management, quality assurance, supply chain"
            },
            BusinessDomain.EDUCATION: {
                "description": "Educational management including students, courses, grades, and administration",
                "key_concepts": "student records, course management, grade tracking, academic administration"
            },
            BusinessDomain.REAL_ESTATE: {
                "description": "Real estate management including properties, listings, transactions, and clients",
                "key_concepts": "property listings, client management, transaction processing, market data"
            },
            BusinessDomain.GENERIC: {
                "description": "Generic business data processing and API integration",
                "key_concepts": "data mapping, API integration, business logic, system connectivity"
            }
        }
        
        return context_prompts.get(domain, context_prompts[BusinessDomain.GENERIC])


# Global prompt template manager
prompt_manager = PromptTemplateManager()


def get_prompt_template(prompt_type: PromptType) -> PromptTemplate:
    """Get prompt template for specific type"""
    return prompt_manager.get_template(prompt_type)


def render_prompt(prompt_type: PromptType, **kwargs) -> str:
    """Render prompt with current configuration"""
    return prompt_manager.render_prompt(prompt_type, **kwargs)


def get_business_context(domain: BusinessDomain) -> Dict[str, str]:
    """Get business context for specific domain"""
    return prompt_manager.get_business_context_prompts(domain)
