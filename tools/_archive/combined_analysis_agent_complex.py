"""
Combined JSON Field Analysis Agent - Simplified Version
Ein LLM-Prompt der relevante Felder identifiziert und semantisch erweitert
"""

import json
import os
from typing import Dict, Any, List
from datetime import datetime
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage

from .json_schemas import ProcessedResult, AgentResponse

# Load environment variables
load_dotenv()

# Prompt template for field identification and enhancement
FIELD_ANALYSIS_PROMPT = """
You are an expert in semantic data analysis and HRIS systems.

Analyze the following JSON data and identify the relevant fields for API mapping.

JSON DATA:
{json_data}

TASK:
1. **Identify relevant fields**: Often the most important fields are in "body", event or directly in the root object
2. **Create semantic descriptions**: Comprehensive analysis for each relevant field

For each relevant field create:

1. **Semantic Description**: Detailed description of what the field means and represents, 1 sentence
2. **Synonyms**: Alternative names in other systems (e.g., emp_id, worker_id for employee_id)
3. **Possible Datatypes**: Which data types are possible (string, integer, date, boolean, etc.)
4. **Business Context**: Classification in business context, where is the field used?

IMPORTANT RULES:
- Focus on FIELDS that are relevant for HR/Absence Management
- SHORT, concise descriptions (max 50 words per field)
- MAXIMUM 3 synonyms per field
- MAXIMUM 3 data types per field  
- Answer ONLY with valid JSON, NO markdown blocks

FORMAT (compact JSON):
{{
    "enhanced_fields": [
        {{
            "field_name": "event",
            "semantic_description": "Specific event or incident in HR system",
            "synonyms": ["incident", "occurrence", "activity"],
            "possible_datatypes": ["string", "enum"],
            "business_context": "Event Tracking, Incident Management"
        }},
        {{
            "field_name": "absence_type", 
            "semantic_description": "Type of absence (vacation, sick leave, etc.)",
            "synonyms": ["leave_type", "absence_category", "time_off_type"],
            "possible_datatypes": ["string", "enum"],
            "business_context": "Absence Management, Workforce Planning"
        }}
    ],
    "processing_context": "HRIS field identification and enhancement",
    "enhancement_confidence": 0.95,
    "total_fields_identified": 2
}}

Answer ONLY with the JSON object, no additional text!
"""


class CombinedFieldAnalysisAgent:
    """Simplified Agent that identifies relevant fields and semantically enhances them."""
    
    def __init__(self):
        """Initialize the simplified analysis agent."""
        # Configure OpenRouter LLM
        self.llm = ChatOpenAI(
            model=os.getenv("LLM_MODEL", "deepseek/deepseek-chat"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.1")),
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            openai_api_base=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            max_tokens=4000,
        )
    
    def _save_analysis_results(self, analysis_result: Dict[str, Any], json_file_path: str, current_directory: str):
        """Save the analysis results structured."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Use the specified directory or fallback
            save_dir = current_directory if current_directory and os.path.exists(current_directory) else "results"
            os.makedirs(save_dir, exist_ok=True)
            
            # Create filename based on JSON file
            base_name = os.path.splitext(os.path.basename(json_file_path))[0] if json_file_path else "analysis"
            filename = f"{base_name}_enhanced_analysis_{timestamp}.json"
            filepath = os.path.join(save_dir, filename)
            
            # Create structured result
            structured_result = {
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "source_json": json_file_path,
                    "analysis_type": "field_identification_and_enhancement",
                    "total_fields_identified": analysis_result.get("total_fields_identified", 0),
                    "enhancement_confidence": analysis_result.get("enhancement_confidence", 0.0)
                },
                "processing_context": analysis_result.get("processing_context", ""),
                "enhanced_fields": analysis_result.get("enhanced_fields", [])
            }
            
            # Save JSON
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(structured_result, f, indent=2, ensure_ascii=False)
            
            # Also create Markdown report
            md_filename = f"{base_name}_enhanced_analysis_{timestamp}.md"
            md_filepath = os.path.join(save_dir, md_filename)
            
            with open(md_filepath, 'w', encoding='utf-8') as f:
                f.write(f"# Enhanced Field Analysis Report\n\n")
                f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Source JSON:** {json_file_path}\n")
                f.write(f"**Total Fields:** {analysis_result.get('total_fields_identified', 0)}\n")
                f.write(f"**Confidence:** {analysis_result.get('enhancement_confidence', 0.0):.2f}\n\n")
                
                f.write(f"## Enhanced Fields\n\n")
                for field in analysis_result.get("enhanced_fields", []):
                    f.write(f"### 📋 {field['field_name']}\n")
                    f.write(f"- **Description:** {field['semantic_description']}\n")
                    f.write(f"- **Synonyms:** {', '.join(field['synonyms'])}\n")
                    f.write(f"- **Data Types:** {', '.join(field['possible_datatypes'])}\n")
                    f.write(f"- **Business Context:** {field['business_context']}\n\n")
                
                f.write(f"## Processing Context\n")
                f.write(f"{analysis_result.get('processing_context', '')}\n")
            
            print(f"✅ Analysis saved:")
            print(f"  �� JSON: {filepath}")
            print(f"  📝 Markdown: {md_filepath}")
            
            return filepath, md_filepath
            
        except Exception as e:
            print(f"⚠️ Error saving: {e}")
            return None, None
    
    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON response from LLM."""
        try:
            # Remove Markdown blocks if present
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
            
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON Parse Error: {e}")
            print(f"Response: {response_text[:200]}...")
            return {"error": "Failed to parse JSON response"}
    
    async def process_json_with_combined_analysis(
        self, 
        json_data: Dict[str, Any], 
        json_file_path: str = "",
        current_directory: str = "",
        collection_name: str = "flip_api_v2"
    ) -> AgentResponse:
        """Main method for combined analysis - a single LLM prompt."""
        try:
            print("🚀 Starting simplified field analysis...")
            
            # Create the prompt with the JSON data
            prompt = FIELD_ANALYSIS_PROMPT.format(
                json_data=json.dumps(json_data, indent=2, ensure_ascii=False)
            )
            
            # LLM Call
            print("📤 Calling LLM for field analysis...")
            response = self.llm.invoke([HumanMessage(content=prompt)])
            
            # Parse Response
            print("🧹 Parsing LLM response...")
            analysis_result = self._parse_json_response(response.content)
            
            if "error" in analysis_result:
                return AgentResponse(
                    status="error",
                    agent_name="CombinedFieldAnalysisAgent",
                    error=f"LLM Response parsing failed: {analysis_result['error']}",
                    result=None
                )
            
            # Save results
            print("💾 Saving analysis results...")
            json_path, md_path = self._save_analysis_results(
                analysis_result, json_file_path, current_directory
            )
            
            # Create the result object
            enhanced_fields = analysis_result.get("enhanced_fields", [])
            field_names = [field["field_name"] for field in enhanced_fields]
            
            combined_context = f"""# Simplified Field Analysis

## 🔍 Identified Relevant Fields
**Number of Fields**: {len(enhanced_fields)}
**Confidence**: {analysis_result.get('enhancement_confidence', 0.0):.2f}

## 📋 Enhanced Fields
"""
            
            for field in enhanced_fields:
                combined_context += f"""
### {field['field_name']}
- **Description**: {field['semantic_description']}
- **Synonyms**: {', '.join(field['synonyms'])}
- **Data Types**: {', '.join(field['possible_datatypes'])}
- **Business Context**: {field['business_context']}
"""
            
            combined_context += f"""
## 📁 Saved Files
- **JSON Report**: {json_path or 'N/A'}
- **Markdown Report**: {md_path or 'N/A'}

## 🎯 Next Steps
1. Review the enhanced field descriptions
2. Use synonyms for API mapping
3. Apply business context for integration decisions
"""
            
            result = ProcessedResult(
                extracted_fields={field: {"type": "enhanced_field", "value": field} for field in field_names},  # Convert to dict
                validation_status="completed",
                confidence_score=analysis_result.get("enhancement_confidence", 0.8),
                processing_notes=f"Simplified analysis completed with {len(enhanced_fields)} enhanced fields",
                context=combined_context
            )
            
            return AgentResponse(
                status="completed",
                agent_name="CombinedFieldAnalysisAgent",
                result=result,
                error=""
            )
            
        except Exception as e:
            return AgentResponse(
                status="error",
                agent_name="CombinedFieldAnalysisAgent",
                error=str(e),
                result=None
            ) 