"""
Combined JSON Field Analysis Agent (Phase 1, Refactored)
- Extract relevant fields via AI (Qwen)
- Add concise semantic description and use-case text
- Enhance each field with RAG-backed ground truth snippets from uploaded OpenAPI spec
- Avoid unverified synonyms & datatypes to reduce hallucinations
"""

import json
import os
from typing import Dict, Any, List, Tuple
from datetime import datetime
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage

from tools._archive._archive.json_schemas import ProcessedResult, AgentResponse
from tools.shared_utilities.request_counter import track_request
from tools.phase1_data_extraction.upload_api_specification import retrieve_from_rag

load_dotenv()


class CombinedFieldAnalysisAgent:
    """Phase 1 analyzer with RAG-backed enhancement."""

    def __init__(self):
        self.llm = ChatOpenAI(
            model=os.getenv("LLM_MODEL", "deepseek/deepseek-chat-v3.1:free"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.1")),
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            openai_api_base=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            max_tokens=2000,
        )

    def _save_results(self, analysis_result: Dict[str, Any], json_file_path: str, current_directory: str) -> Tuple[str, str]:
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_dir = current_directory if current_directory and os.path.exists(current_directory) else "results"
            os.makedirs(save_dir, exist_ok=True)
            base_name = os.path.splitext(os.path.basename(json_file_path))[0] if json_file_path else "analysis"
            json_path = os.path.join(save_dir, f"{base_name}_analysis_{timestamp}.json")
            md_path = os.path.join(save_dir, f"{base_name}_analysis_{timestamp}.md")
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(analysis_result, f, indent=2, ensure_ascii=False)
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(f"# Comprehensive Field Analysis Report\n\n")
                f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Source:** {json_file_path}\n")
                fields = analysis_result.get('fields', [])
                f.write(f"**Fields:** {len(fields)}\n")
                validation_note = analysis_result.get('field_extraction_validation', '')
                if validation_note:
                    f.write(f"**Validation:** {validation_note}\n")
                f.write("\n")
                descriptions = analysis_result.get('descriptions', {})
                evidence = analysis_result.get('evidence', {})
                rag_note = analysis_result.get('rag_status_note')
                for field in fields:
                    f.write(f"## {field}\n")
                    d = descriptions.get(field, {})
                    if d.get('semantic_description'):
                        f.write(f"- **Semantic Description:** {d['semantic_description']}\n")
                    if d.get('use_case'):
                        f.write(f"- **Use Case:** {d['use_case']}\n")
                    if evidence.get(field):
                        f.write("- **Ground Truth Evidence:**\n")
                        for i, ev in enumerate(evidence[field][:3], 1):
                            score = ev.get('semantic_score', ev.get('score', 0.0))
                            f.write(f"  {i}. [{ev.get('chunk_type','unknown')}] (score: {score:.2f})\n")
                            f.write("```\n" + (ev.get('text') or '').strip() + "\n```\n")
                    f.write("\n")
                if rag_note:
                    f.write(f"\n> RAG Note: {rag_note}\n")
            print(f"✅ Results saved: {json_path}")
            return json_path, md_path
        except Exception as e:
            print(f"⚠️ Save error: {e}")
            return None, None

    def _clean_json_block(self, text: str) -> str:
        if "```json" in text:
            s = text.find("```json") + 7
            e = text.find("```", s)
            if e > s:
                return text[s:e].strip()
        if "```" in text:
            s = text.find("```") + 3
            e = text.find("```", s)
            if e > s:
                return text[s:e].strip()
        return text

    def _extract_fields_via_ai(self, json_data: Dict[str, Any]) -> List[str]:
        """Use LLM to extract ONLY relevant data fields for HR/API mapping - filtered extraction."""
        prompt = (
            "You are given JSON payload data. Extract ONLY the relevant data fields for HR/API mapping.\n"
            "FOCUS ONLY on fields that contain actual business data, NOT metadata or pagination.\n\n"
            "EXTRACT ONLY:\n"
            "1. Fields within 'data' arrays (id, employeeId, type, status, startDate, endDate, etc.)\n"
            "2. Nested object fields within data (duration.value, duration.unit, etc.)\n"
            "3. Timestamp fields within data (createdAt, updatedAt, etc.)\n\n"
            "EXCLUDE:\n"
            "- Pagination fields (page, pageSize, total)\n"
            "- Top-level metadata fields (data, pagination)\n"
            "- System fields that don't contain business data\n\n"
            "Return ONLY the meaningful data fields that would be used for API mapping.\n\n"
            f"JSON:\n{json.dumps(json_data, indent=2, ensure_ascii=False)}\n\n"
            "Return ONLY valid JSON with relevant data fields:\n"
            "{\n  \"fields\": [\"id\", \"employeeId\", \"type\", \"status\", \"startDate\", \"endDate\", \"duration.value\", \"duration.unit\", \"createdAt\", \"updatedAt\"]\n}"
        )

        response = self.llm.invoke([HumanMessage(content=prompt)])
        track_request("json_analysis_agent", os.getenv("LLM_MODEL", "deepseek/deepseek-chat-v3.1:free"), 0)

        cleaned = self._clean_json_block(response.content)
        try:
            data = json.loads(cleaned)
            fields = data.get("fields") or []
            # Ensure list of strings
            fields = [str(f) for f in fields if isinstance(f, (str, int, float))]
            # De-duplicate while preserving order
            seen = set()
            unique_fields = []
            for f in fields:
                if f not in seen:
                    seen.add(f)
                    unique_fields.append(f)
            return unique_fields
        except Exception as e:
            # Fallback to programmatic extraction with filtering
            print(f"⚠️ AI extraction failed: {e}, using programmatic fallback with filtering")
            return self._extract_relevant_fields_programmatically(json_data)

    def _extract_all_fields_programmatically(self, json_data: Dict[str, Any]) -> List[str]:
        """Programmatically extract all field paths from JSON structure."""
        fields = []
        
        def extract_paths(obj, prefix="", max_depth=4, current_depth=0):
            if current_depth >= max_depth:
                return
                
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{prefix}.{key}" if prefix else key
                    fields.append(current_path)
                    
                    # Recursively extract nested fields
                    if isinstance(value, (dict, list)) and current_depth < max_depth - 1:
                        extract_paths(value, current_path, max_depth, current_depth + 1)
                        
            elif isinstance(obj, list) and obj:
                # For arrays, extract fields from the first item if it's a dict
                if isinstance(obj[0], dict):
                    extract_paths(obj[0], prefix, max_depth, current_depth)
        
        extract_paths(json_data)
        return fields

    def _extract_relevant_fields_programmatically(self, json_data: Dict[str, Any]) -> List[str]:
        """Programmatically extract only relevant data fields, filtering out pagination and metadata."""
        fields = []
        
        def extract_data_fields(obj, prefix="", max_depth=4, current_depth=0):
            if current_depth >= max_depth:
                return
                
            if isinstance(obj, dict):
                for key, value in obj.items():
                    # Skip pagination and metadata fields
                    if key in ['pagination', 'page', 'pageSize', 'total', 'data'] and current_depth == 0:
                        continue
                        
                    current_path = f"{prefix}.{key}" if prefix else key
                    
                    # Only add fields that are within data arrays or are meaningful business fields
                    if (prefix.startswith('data.') or 
                        key in ['id', 'employeeId', 'type', 'status', 'startDate', 'endDate', 
                               'createdAt', 'updatedAt', 'duration', 'value', 'unit']):
                        fields.append(current_path)
                    
                    # Recursively extract nested fields
                    if isinstance(value, (dict, list)) and current_depth < max_depth - 1:
                        extract_data_fields(value, current_path, max_depth, current_depth + 1)
                        
            elif isinstance(obj, list) and obj:
                # For arrays, extract fields from the first item if it's a dict
                if isinstance(obj[0], dict):
                    extract_data_fields(obj[0], prefix, max_depth, current_depth)
        
        extract_data_fields(json_data)
        return fields

    def _validate_field_extraction(self, fields: List[str], json_data: Dict[str, Any]) -> Tuple[List[str], str]:
        """Validate that all relevant data fields were extracted from the JSON structure."""
        validation_notes = []
        
        # Get relevant fields from programmatic extraction for comparison
        relevant_paths = self._extract_relevant_fields_programmatically(json_data)
        
        # Check for missing important data fields
        missing_fields = []
        for path in relevant_paths:
            if path not in fields:
                missing_fields.append(path)
        
        if missing_fields:
            validation_notes.append(f"Missing relevant data fields: {missing_fields[:10]}")
            # Add missing fields to the final list
            fields.extend(missing_fields)
            fields = list(set(fields))  # Remove duplicates
        
        # Check for data array fields specifically
        if "data" in json_data and isinstance(json_data["data"], list) and json_data["data"]:
            data_item = json_data["data"][0]
            if isinstance(data_item, dict):
                data_fields = list(data_item.keys())
                missing_data_fields = []
                for f in data_fields:
                    if f not in fields:
                        missing_data_fields.append(f)
                if missing_data_fields:
                    validation_notes.append(f"Missing data array fields: {missing_data_fields}")
                    fields.extend(missing_data_fields)
        
        # Final deduplication
        fields = list(set(fields))
        
        validation_note = "; ".join(validation_notes) if validation_notes else f"All {len(fields)} relevant data fields extracted successfully"
        
        return fields, validation_note

    def _describe_fields_via_ai(self, fields: List[str], json_data: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
        if not fields:
            return {}
        prompt = (
            "For each field, provide a concise semantic_description (<=20 words) and a short use_case (<=20 words).\n"
            "Return ONLY valid JSON mapping field -> {semantic_description, use_case}.\n\n"
            f"Fields: {fields}\n"
            f"Context JSON:\n{json.dumps(json_data, indent=2, ensure_ascii=False)}\n\n"
            "Example: {\n  \"employeeId\": {\"semantic_description\": \"Unique employee identifier\", \"use_case\": \"Join employees across systems\"}\n}"
        )
        response = self.llm.invoke([HumanMessage(content=prompt)])
        track_request("json_analysis_agent", os.getenv("LLM_MODEL", "qwen/qwen3-coder:free"), 0)
        cleaned = self._clean_json_block(response.content)
        try:
            parsed = json.loads(cleaned)
        except Exception:
            return {f: {"semantic_description": "", "use_case": ""} for f in fields}
        result: Dict[str, Dict[str, str]] = {}
        for f in fields:
            entry = parsed.get(f) if isinstance(parsed, dict) else None
            if isinstance(entry, dict):
                result[f] = {
                    "semantic_description": str(entry.get("semantic_description", ""))[:500],
                    "use_case": str(entry.get("use_case", ""))[:500],
                }
            else:
                result[f] = {"semantic_description": "", "use_case": ""}
        return result

    def _rag_query(self, query: str, collection_name: str) -> List[Dict[str, Any]]:
        try:
            raw = retrieve_from_rag(query, collection_name, limit=3)
            try:
                return json.loads(raw)
            except Exception:
                if isinstance(raw, str) and raw.startswith("❌"):
                    return [{"error": raw}]
                return [{"text": raw}]
        except Exception as e:
            return [{"error": f"RAG unavailable: {e}"}]

    def _enhance_with_rag(self, fields: List[str], collection_name: str) -> Tuple[Dict[str, List[Dict[str, Any]]], str]:
        """For each field, gather comprehensive ground-truth snippets from the uploaded OpenAPI spec via RAG."""
        evidence: Dict[str, List[Dict[str, Any]]] = {}
        rag_note = ""
        
        for field in fields:
            # Create comprehensive queries for each field
            queries = [
                f"{field} property schema definition",
                f"{field} parameter definition in request or response",
                f"{field} field type validation rules",
                f"{field} API endpoint usage examples",
                f"{field} data format and constraints",
                f"absence {field} business logic",
                f"HR {field} field mapping",
            ]
            
            field_results: List[Dict[str, Any]] = []
            for q in queries:
                results = self._rag_query(q, collection_name)
                for r in results:
                    if isinstance(r, dict) and 'error' not in r:
                        field_results.append({
                            'text': r.get('text', ''),
                            'score': r.get('score', 0.0),
                            'semantic_score': r.get('semantic_score', r.get('score', 0.0)),
                            'chunk_type': r.get('chunk_type', 'unknown'),
                            'metadata': r.get('metadata', {})
                        })
                    elif isinstance(r, dict) and 'error' in r and not rag_note:
                        rag_note = r['error']
            
            # Deduplicate by text content and sort by score
            seen_text = set()
            deduped: List[Dict[str, Any]] = []
            for item in field_results:
                t = item.get('text', '')
                if t and t not in seen_text:
                    seen_text.add(t)
                    deduped.append(item)
            
            # Sort by semantic score and take top results for comprehensive analysis
            deduped.sort(key=lambda x: x.get('semantic_score', 0.0), reverse=True)
            evidence[field] = deduped[:5]  # Take top 5 results for comprehensive analysis
        
        return evidence, rag_note

    async def process_json_with_combined_analysis(
        self,
        json_data: Dict[str, Any],
        json_file_path: str = "",
        current_directory: str = "",
        collection_name: str = "flip_api_v2"
    ) -> AgentResponse:
        try:
            print("🚀 Starting comprehensive field analysis (phase1)...")
            
            # Use filtered extraction to focus on relevant data fields only
            try:
                ai_fields = self._extract_fields_via_ai(json_data)
                print(f"🤖 AI filtered extraction found {len(ai_fields)} relevant fields: {ai_fields}")
            except Exception as e:
                print(f"⚠️ AI extraction failed: {e}, using programmatic fallback")
                ai_fields = self._extract_relevant_fields_programmatically(json_data)
                print(f"📊 Programmatic filtered extraction found {len(ai_fields)} relevant fields: {ai_fields}")
            
            # Use the filtered fields directly
            all_fields = ai_fields
            print(f"✅ Final relevant fields: {len(all_fields)} fields")
            
            if not all_fields:
                return AgentResponse(status="error", agent_name="CombinedFieldAnalysisAgent", error="No fields extracted", result=None)
            
            # Validate field extraction completeness
            validated_fields, validation_note = self._validate_field_extraction(all_fields, json_data)
            print(f"📊 Field extraction validation: {validation_note}")
            print(f"✅ Final field count: {len(validated_fields)}")
            
            descriptions = self._describe_fields_via_ai(validated_fields, json_data)
            evidence, rag_note = self._enhance_with_rag(validated_fields, collection_name)
            scores: List[float] = []
            for f in validated_fields:
                for ev in evidence.get(f, []):
                    scores.append(float(ev.get('semantic_score', 0.0)))
            avg_score = sum(scores) / len(scores) if scores else 0.0
            analysis_result: Dict[str, Any] = {
                "fields": validated_fields,
                "descriptions": descriptions,
                "evidence": evidence,
                "processing_context": "HR field analysis",
                "enhancement_confidence": round(avg_score, 3),
                "total_fields_identified": len(validated_fields),
                "field_extraction_validation": validation_note
            }
            if rag_note:
                analysis_result["rag_status_note"] = rag_note
            json_path, md_path = self._save_results(analysis_result, json_file_path, current_directory)
            extracted_fields_map = {
                f: {
                    "description": descriptions.get(f, {}).get("semantic_description", ""),
                    "use_case": descriptions.get(f, {}).get("use_case", ""),
                    "evidence_count": len(evidence.get(f, [])),
                }
                for f in validated_fields
            }
            lines = [
                "# Comprehensive Field Analysis Results",
                "",
                "## 📊 Summary",
                f"- Fields Found: {len(validated_fields)}",
                f"- RAG Evidence Coverage (avg top-score): {avg_score:.2f}",
                f"- Field Extraction Validation: {validation_note}",
            ]
            if rag_note:
                lines.append(f"- RAG Note: {rag_note}")
            lines.extend(["", "## Fields"]) 
            for f in validated_fields:
                d = descriptions.get(f, {})
                lines.append(f"- {f}: {d.get('semantic_description','n/a')} (use: {d.get('use_case','n/a')}) [evidence: {len(evidence.get(f, []))}]")
            lines.extend(["", "## 📁 Files", f"- JSON: {json_path or 'N/A'}", f"- Markdown: {md_path or 'N/A'}"]) 
            context = "\n".join(lines)
            result = ProcessedResult(
                extracted_fields=extracted_fields_map,
                validation_status="completed" if scores else "partial",
                confidence_score=avg_score,
                processing_notes=f"Programmatic + AI extracted {len(validated_fields)} fields with validation; RAG evidence added where available. Validation: {validation_note}",
                context=context
            )
            return AgentResponse(status="completed", agent_name="CombinedFieldAnalysisAgent", result=result, error="")
        except Exception as e:
            return AgentResponse(status="error", agent_name="CombinedFieldAnalysisAgent", error=str(e), result=None)