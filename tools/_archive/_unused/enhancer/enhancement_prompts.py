"""
Prompt templates for field enhancement agent.
"""

FIELD_ENHANCEMENT_PROMPT = """
You are an expert in semantic data analysis and HRIS systems.

Analyze the following extracted fields and create a COMPACT semantic description.

CONTEXT:
Processing Notes: {processing_notes}
Business Context: {context}

FIELDS TO ANALYZE:
{extracted_fields}

TASK:
For each field in extracted_fields, create a comprehensive semantic analysis:

1. **Semantic Description**: Detailed description of what the field means and represents, 1 sentence
2. **Synonyms**: Alternative names in other systems (e.g., emp_id, worker_id for employee_id)
3. **Possible Datatypes**: Which data types are possible (string, integer, date, boolean, etc.)
4. **Business Context**: Classification in business context, where is the field used?

IMPORTANT RULES:
- SHORT, concise descriptions (max 50 words per field)
- MAXIMUM 3 synonyms per field
- MAXIMUM 3 data types per field  
- Answer ONLY with valid JSON, NO markdown blocks

FORMAT (compact JSON):
{{
    "enhanced_fields": [
        {{
            "field_name": "method",
            "semantic_description": "HTTP method for API requests",
            "synonyms": ["http_method", "verb", "action"],
            "possible_datatypes": ["string", "enum"],
            "business_context": "API Integration"
        }},
        {{
            "field_name": "employee_id", 
            "semantic_description": "Unique employee identification",
            "synonyms": ["emp_id", "worker_id", "staff_id"],
            "possible_datatypes": ["string", "integer"],
            "business_context": "HR Management"
        }}
    ],
    "processing_context": "HRIS field enhancement",
    "enhancement_confidence": 0.95
}}

Answer ONLY with the JSON object, no additional text!
"""