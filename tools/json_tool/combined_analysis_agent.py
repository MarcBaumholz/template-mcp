"""
Simple JSON Field Analysis Agent
Identifies relevant fields and provides semantic descriptions
"""

import json
import os
from typing import Dict, Any, List
from datetime import datetime
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage

from .json_schemas import ProcessedResult, AgentResponse

load_dotenv()

# Simple prompt for field analysis
FIELD_ANALYSIS_PROMPT = """
Analyze the JSON data and identify relevant fields for HR/API mapping.

JSON Data:
{json_data}

Task:
1. Find relevant fields (usually in "body")
2. For each field, provide:
   - Semantic description (1 sentence)
   - Synonyms (max 3 alternative names)
   - Data types (max 3 possible types)
   - Business context (where it's used)

Rules:
- Focus on HR/Absence Management fields
- Keep descriptions under 50 words
- Return ONLY valid JSON, no markdown

Format:
{{
    "enhanced_fields": [
        {{
            "field_name": "employee_id",
            "semantic_description": "Unique employee identifier",
            "synonyms": ["emp_id", "worker_id", "staff_id"],
            "possible_datatypes": ["string", "integer"],
            "business_context": "HR Management"
        }}
    ],
    "processing_context": "HR field analysis",
    "enhancement_confidence": 0.95,
    "total_fields_identified": 1
}}
"""


class CombinedFieldAnalysisAgent:
    """Simple field analysis agent."""
    
    def __init__(self):
        """Initialize simple analysis agent."""
        self.llm = ChatOpenAI(
            model=os.getenv("LLM_MODEL", "deepseek/deepseek-chat"),
            temperature=0.1,
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            openai_api_base=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            max_tokens=3000,
        )
    
    def _save_results(self, analysis_result: Dict[str, Any], json_file_path: str, current_directory: str):
        """Save analysis results."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Use provided directory or default
            save_dir = current_directory if current_directory and os.path.exists(current_directory) else "results"
            os.makedirs(save_dir, exist_ok=True)
            
            # Create filename
            base_name = os.path.splitext(os.path.basename(json_file_path))[0] if json_file_path else "analysis"
            filename = f"{base_name}_analysis_{timestamp}.json"
            filepath = os.path.join(save_dir, filename)
            
            # Save JSON
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(analysis_result, f, indent=2, ensure_ascii=False)
            
            # Save Markdown
            md_filename = f"{base_name}_analysis_{timestamp}.md"
            md_filepath = os.path.join(save_dir, md_filename)
            
            with open(md_filepath, 'w', encoding='utf-8') as f:
                f.write(f"# Field Analysis Report\n\n")
                f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Source:** {json_file_path}\n")
                f.write(f"**Fields:** {analysis_result.get('total_fields_identified', 0)}\n\n")
                
                for field in analysis_result.get("enhanced_fields", []):
                    f.write(f"## {field['field_name']}\n")
                    f.write(f"- **Description:** {field['semantic_description']}\n")
                    f.write(f"- **Synonyms:** {', '.join(field['synonyms'])}\n")
                    f.write(f"- **Types:** {', '.join(field['possible_datatypes'])}\n")
                    f.write(f"- **Context:** {field['business_context']}\n\n")
            
            print(f"✅ Results saved: {filepath}")
            return filepath, md_filepath
            
        except Exception as e:
            print(f"⚠️ Save error: {e}")
            return None, None
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM JSON response."""
        try:
            # Remove markdown blocks if present
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
            return {"error": "Failed to parse JSON response"}
    
    async def process_json_with_combined_analysis(
        self, 
        json_data: Dict[str, Any], 
        json_file_path: str = "",
        current_directory: str = "",
        collection_name: str = "flip_api_v2"
    ) -> AgentResponse:
        """Main analysis method."""
        try:
            print("🚀 Starting field analysis...")
            
            # Create prompt
            prompt = FIELD_ANALYSIS_PROMPT.format(
                json_data=json.dumps(json_data, indent=2, ensure_ascii=False)
            )
            
            # Call LLM
            print("📤 Calling LLM...")
            response = self.llm.invoke([HumanMessage(content=prompt)])
            
            # Parse response
            print("🧹 Parsing response...")
            analysis_result = self._parse_response(response.content)
            
            if "error" in analysis_result:
                return AgentResponse(
                    status="error",
                    agent_name="CombinedFieldAnalysisAgent",
                    error=f"LLM parsing failed: {analysis_result['error']}",
                    result=None
                )
            
            # Save results
            print("💾 Saving results...")
            json_path, md_path = self._save_results(
                analysis_result, json_file_path, current_directory
            )
            
            # Create result
            enhanced_fields = analysis_result.get("enhanced_fields", [])
            field_names = [field["field_name"] for field in enhanced_fields]
            
            context = f"""# Field Analysis Results

## 📊 Summary
- **Fields Found:** {len(enhanced_fields)}
- **Confidence:** {analysis_result.get('enhancement_confidence', 0.0):.2f}

## 📋 Fields
"""
            
            for field in enhanced_fields:
                context += f"""
### {field['field_name']}
- **Description:** {field['semantic_description']}
- **Synonyms:** {', '.join(field['synonyms'])}
- **Types:** {', '.join(field['possible_datatypes'])}
- **Context:** {field['business_context']}
"""
            
            context += f"""
## 📁 Files
- **JSON:** {json_path or 'N/A'}
- **Markdown:** {md_path or 'N/A'}
"""
            
            result = ProcessedResult(
                extracted_fields={field: {"type": "enhanced_field", "value": field} for field in field_names},
                validation_status="completed",
                confidence_score=analysis_result.get("enhancement_confidence", 0.8),
                processing_notes=f"Analysis completed with {len(enhanced_fields)} fields",
                context=context
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