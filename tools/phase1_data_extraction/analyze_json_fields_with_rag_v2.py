"""
Enhanced JSON Field Analysis Agent (Phase 1, Configuration-Driven)
- Extract relevant fields via AI with flexible configuration
- Add concise semantic description and use-case text
- Enhance each field with RAG-backed ground truth snippets
- Support any business domain without hardcoded assumptions
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
from tools.shared_utilities.config_manager import get_config, get_llm_model, get_collection_name
from tools.shared_utilities.prompt_templates import render_prompt, PromptType
from tools.shared_utilities.field_extractor import extract_fields_from_json, FieldExtractionResult
from tools.phase1_data_extraction.upload_api_specification import retrieve_from_rag

load_dotenv()


class EnhancedFieldAnalysisAgent:
    """Enhanced Phase 1 analyzer with configuration-driven approach."""

    def __init__(self):
        self.config = get_config()
        self.llm = ChatOpenAI(
            model=get_llm_model(),
            temperature=self.config.llm.temperature,
            openai_api_key=os.getenv(self.config.llm.api_key_env),
            openai_api_base=os.getenv(self.config.llm.base_url_env, self.config.llm.base_url_default),
            max_tokens=self.config.llm.max_tokens,
        )

    def _save_results(self, analysis_result: Dict[str, Any], json_file_path: str, current_directory: str) -> Tuple[str, str]:
        """Save analysis results with flexible naming"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_dir = current_directory if current_directory and os.path.exists(current_directory) else "results"
            os.makedirs(save_dir, exist_ok=True)
            
            # Flexible naming based on business domain
            domain_suffix = f"_{self.config.business_domain.value}" if self.config.business_domain.value != "generic" else ""
            base_name = os.path.splitext(os.path.basename(json_file_path))[0] if json_file_path else "analysis"
            
            json_path = os.path.join(save_dir, f"{base_name}_analysis{domain_suffix}_{timestamp}.json")
            md_path = os.path.join(save_dir, f"{base_name}_analysis{domain_suffix}_{timestamp}.md")
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(analysis_result, f, indent=2, ensure_ascii=False)
            
            with open(md_path, 'w', encoding='utf-8') as f:
                self._write_markdown_report(f, analysis_result, json_file_path)
            
            print(f"✅ Results saved: {json_path}")
            return json_path, md_path
        except Exception as e:
            print(f"⚠️ Save error: {e}")
            return None, None

    def _write_markdown_report(self, file, analysis_result: Dict[str, Any], json_file_path: str):
        """Write markdown report with flexible formatting"""
        file.write(f"# Comprehensive Field Analysis Report\n\n")
        file.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        file.write(f"**Source:** {json_file_path}\n")
        file.write(f"**Business Domain:** {self.config.business_domain.value.replace('_', ' ').title()}\n")
        
        fields = analysis_result.get('fields', [])
        file.write(f"**Fields:** {len(fields)}\n")
        
        validation_note = analysis_result.get('field_extraction_validation', '')
        if validation_note:
            file.write(f"**Validation:** {validation_note}\n")
        
        confidence = analysis_result.get('enhancement_confidence', 0.0)
        file.write(f"**Confidence Score:** {confidence:.2f}\n")
        file.write("\n")
        
        descriptions = analysis_result.get('descriptions', {})
        evidence = analysis_result.get('evidence', {})
        rag_note = analysis_result.get('rag_status_note')
        
        for field in fields:
            file.write(f"## {field}\n")
            d = descriptions.get(field, {})
            if d.get('semantic_description'):
                file.write(f"- **Semantic Description:** {d['semantic_description']}\n")
            if d.get('use_case'):
                file.write(f"- **Use Case:** {d['use_case']}\n")
            if evidence.get(field):
                file.write("- **Ground Truth Evidence:**\n")
                for i, ev in enumerate(evidence[field][:3], 1):
                    score = ev.get('semantic_score', ev.get('score', 0.0))
                    file.write(f"  {i}. [{ev.get('chunk_type','unknown')}] (score: {score:.2f})\n")
                    file.write("```\n" + (ev.get('text') or '').strip() + "\n```\n")
            file.write("\n")
        
        if rag_note:
            file.write(f"\n> RAG Note: {rag_note}\n")

    def _clean_json_block(self, text: str) -> str:
        """Clean JSON block from LLM response"""
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
        """Use LLM to extract relevant data fields with flexible prompts"""
        prompt = render_prompt(
            PromptType.FIELD_EXTRACTION,
            business_context=self.config.business_domain.value.replace("_", " ").title(),
            json_data=json.dumps(json_data, indent=2, ensure_ascii=False)
        )

        response = self.llm.invoke([HumanMessage(content=prompt)])
        track_request("json_analysis_agent", get_llm_model(), 0)

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
            # Fallback to programmatic extraction
            print(f"⚠️ AI extraction failed: {e}, using programmatic fallback")
            return self._extract_fields_programmatically(json_data)

    def _extract_fields_programmatically(self, json_data: Dict[str, Any]) -> List[str]:
        """Extract fields using flexible field extractor"""
        result = extract_fields_from_json(json_data, self.config.field_extraction)
        return result.fields

    def _describe_fields_via_ai(self, fields: List[str], json_data: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
        """Describe fields using flexible prompts"""
        if not fields:
            return {}
        
        prompt = render_prompt(
            PromptType.FIELD_DESCRIPTION,
            business_context=self.config.business_domain.value.replace("_", " ").title(),
            fields=fields,
            json_data=json.dumps(json_data, indent=2, ensure_ascii=False)
        )
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        track_request("json_analysis_agent", get_llm_model(), 0)
        
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
        """Query RAG system with flexible collection naming"""
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
        """Enhance fields with RAG using flexible queries"""
        evidence: Dict[str, List[Dict[str, Any]]] = {}
        rag_note = ""
        
        for field in fields:
            # Create flexible queries based on business domain
            queries = [
                f"{field} property schema definition",
                f"{field} parameter definition in request or response",
                f"{field} field type validation rules",
                f"{field} API endpoint usage examples",
                f"{field} data format and constraints",
                f"{field} business logic and validation",
                f"{self.config.business_domain.value.replace('_', ' ')} {field} field mapping",
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
            
            # Sort by semantic score and take top results
            deduped.sort(key=lambda x: x.get('semantic_score', 0.0), reverse=True)
            evidence[field] = deduped[:5]
        
        return evidence, rag_note

    async def process_json_with_combined_analysis(
        self,
        json_data: Dict[str, Any],
        json_file_path: str = "",
        current_directory: str = "",
        collection_name: str = None
    ) -> AgentResponse:
        """Process JSON with enhanced analysis using configuration"""
        try:
            print("🚀 Starting enhanced field analysis (phase1)...")
            
            # Use flexible collection naming
            if collection_name is None:
                collection_name = get_collection_name()
            
            # Extract fields using AI or programmatic fallback
            try:
                ai_fields = self._extract_fields_via_ai(json_data)
                print(f"🤖 AI extraction found {len(ai_fields)} relevant fields: {ai_fields}")
            except Exception as e:
                print(f"⚠️ AI extraction failed: {e}, using programmatic fallback")
                ai_fields = self._extract_fields_programmatically(json_data)
                print(f"📊 Programmatic extraction found {len(ai_fields)} relevant fields: {ai_fields}")
            
            if not ai_fields:
                return AgentResponse(status="error", agent_name="EnhancedFieldAnalysisAgent", error="No fields extracted", result=None)
            
            # Get field descriptions and RAG enhancement
            descriptions = self._describe_fields_via_ai(ai_fields, json_data)
            evidence, rag_note = self._enhance_with_rag(ai_fields, collection_name)
            
            # Calculate confidence scores
            scores: List[float] = []
            for f in ai_fields:
                for ev in evidence.get(f, []):
                    scores.append(float(ev.get('semantic_score', 0.0)))
            avg_score = sum(scores) / len(scores) if scores else 0.0
            
            # Build analysis result
            analysis_result: Dict[str, Any] = {
                "fields": ai_fields,
                "descriptions": descriptions,
                "evidence": evidence,
                "processing_context": f"{self.config.business_domain.value.replace('_', ' ')} data field analysis",
                "enhancement_confidence": round(avg_score, 3),
                "total_fields_identified": len(ai_fields),
                "field_extraction_validation": f"Extracted {len(ai_fields)} fields using {self.config.business_domain.value} context",
                "business_domain": self.config.business_domain.value,
                "extraction_method": "ai_with_programmatic_fallback"
            }
            
            if rag_note:
                analysis_result["rag_status_note"] = rag_note
            
            # Save results
            json_path, md_path = self._save_results(analysis_result, json_file_path, current_directory)
            
            # Build result
            extracted_fields_map = {
                f: {
                    "description": descriptions.get(f, {}).get("semantic_description", ""),
                    "use_case": descriptions.get(f, {}).get("use_case", ""),
                    "evidence_count": len(evidence.get(f, [])),
                }
                for f in ai_fields
            }
            
            lines = [
                "# Enhanced Field Analysis Results",
                "",
                "## 📊 Summary",
                f"- Fields Found: {len(ai_fields)}",
                f"- Business Domain: {self.config.business_domain.value.replace('_', ' ').title()}",
                f"- RAG Evidence Coverage (avg top-score): {avg_score:.2f}",
                f"- Extraction Method: AI with programmatic fallback",
            ]
            if rag_note:
                lines.append(f"- RAG Note: {rag_note}")
            
            lines.extend(["", "## Fields"]) 
            for f in ai_fields:
                d = descriptions.get(f, {})
                lines.append(f"- {f}: {d.get('semantic_description','n/a')} (use: {d.get('use_case','n/a')}) [evidence: {len(evidence.get(f, []))}]")
            
            lines.extend(["", "## 📁 Files", f"- JSON: {json_path or 'N/A'}", f"- Markdown: {md_path or 'N/A'}"]) 
            context = "\n".join(lines)
            
            result = ProcessedResult(
                extracted_fields=extracted_fields_map,
                validation_status="completed" if scores else "partial",
                confidence_score=avg_score,
                processing_notes=f"Enhanced extraction with {self.config.business_domain.value} context; {len(ai_fields)} fields identified with RAG evidence",
                context=context
            )
            
            return AgentResponse(status="completed", agent_name="EnhancedFieldAnalysisAgent", result=result, error="")
        except Exception as e:
            return AgentResponse(status="error", agent_name="EnhancedFieldAnalysisAgent", error=str(e), result=None)
