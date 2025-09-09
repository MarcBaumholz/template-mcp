"""
Combined JSON Field Analysis Agent (Refactored)
- Extracts relevant fields via AI (Qwen)
- Enhances each field with RAG-backed ground truth snippets from the uploaded OpenAPI spec
- Avoids unverified synonyms and datatypes to reduce hallucinations
"""

import json
import os
from typing import Dict, Any, List, Tuple
from datetime import datetime
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage

from .json_schemas import ProcessedResult, AgentResponse
from ..request_counter import track_request

load_dotenv()


class CombinedFieldAnalysisAgent:
    """Refactored field analysis agent with RAG-backed enhancement."""

    def __init__(self):
        """Initialize analysis agent using Qwen model via OpenRouter."""
        self.llm = ChatOpenAI(
            model=os.getenv("LLM_MODEL", "qwen/qwen3-coder:free"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.1")),
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            openai_api_base=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            max_tokens=2000,
        )

    def _save_results(self, analysis_result: Dict[str, Any], json_file_path: str, current_directory: str) -> Tuple[str, str]:
        """Save analysis results as JSON and Markdown."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Use provided directory or default
            save_dir = current_directory if current_directory and os.path.exists(current_directory) else "results"
            os.makedirs(save_dir, exist_ok=True)

            # Create filename base
            base_name = os.path.splitext(os.path.basename(json_file_path))[0] if json_file_path else "analysis"
            json_filename = f"{base_name}_analysis_{timestamp}.json"
            md_filename = f"{base_name}_analysis_{timestamp}.md"
            json_path = os.path.join(save_dir, json_filename)
            md_path = os.path.join(save_dir, md_filename)

            # Save JSON
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(analysis_result, f, indent=2, ensure_ascii=False)

            # Save Markdown
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(f"# Field Analysis Report\n\n")
                f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Source:** {json_file_path}\n")
                fields = analysis_result.get('fields', [])
                f.write(f"**Fields:** {len(fields)}\n\n")
                descriptions = analysis_result.get('descriptions', {})
                evidence = analysis_result.get('evidence', {})
                rag_note = analysis_result.get('rag_status_note')

                for field in fields:
                    f.write(f"## {field}\n")
                    desc_obj = descriptions.get(field, {})
                    if desc_obj.get('semantic_description'):
                        f.write(f"- **Semantic Description:** {desc_obj['semantic_description']}\n")
                    if desc_obj.get('use_case'):
                        f.write(f"- **Use Case:** {desc_obj['use_case']}\n")
                    if evidence.get(field):
                        f.write(f"- **Ground Truth Evidence:**\n")
                        for i, ev in enumerate(evidence[field][:3], 1):
                            score_str = f" (score: {ev.get('semantic_score', 0):.2f})" if 'semantic_score' in ev else ""
                            chunk = ev.get('chunk_type', 'unknown')
                            f.write(f"  {i}. [{chunk}]{score_str}:\n")
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
        """Extract JSON content from possible fenced code blocks."""
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end > start:
                return text[start:end].strip()
        if "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end > start:
                return text[start:end].strip()
        return text

    def _extract_fields_via_ai(self, json_data: Dict[str, Any]) -> List[str]:
        """Use LLM to extract relevant field names from JSON data (no synonyms/types)."""
        prompt = (
            "You are given JSON payload data. Identify the most relevant field names for HR/API mapping. "
            "Focus on fields typically inside 'body' or top-level properties related to employees, absences, approvals.\n\n"
            f"JSON:\n{json.dumps(json_data, indent=2, ensure_ascii=False)}\n\n"
            "Return ONLY valid JSON with this format (no markdown):\n"
            "{\n  \"fields\": [\"employeeId\", \"type\", \"status\"]\n}"
        )

        response = self.llm.invoke([HumanMessage(content=prompt)])
        track_request("json_analysis_agent", os.getenv("LLM_MODEL", "qwen/qwen3-coder:free"), 0)

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
            raise RuntimeError(f"Failed to parse fields JSON from LLM: {e}")

    def _describe_fields_via_ai(self, fields: List[str], json_data: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
        """Generate short semantic descriptions and use-case notes for each field."""
        if not fields:
            return {}
        prompt = (
            "Provide a concise semantic description (<=20 words) and a short use-case note (<=20 words) for each field.\n"
            "Return ONLY valid JSON as an object mapping field -> {semantic_description, use_case}. No markdown.\n\n"
            f"Fields: {fields}\n"
            f"Context JSON (for hints):\n{json.dumps(json_data, indent=2, ensure_ascii=False)}\n\n"
            "Example format:\n{\n  \"employeeId\": {\"semantic_description\": \"Unique employee identifier\", \"use_case\": \"Join employees across systems\"}\n}"
        )
        response = self.llm.invoke([HumanMessage(content=prompt)])
        track_request("json_analysis_agent", os.getenv("LLM_MODEL", "qwen/qwen3-coder:free"), 0)
        cleaned = self._clean_json_block(response.content)
        try:
            parsed = json.loads(cleaned)
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
        except Exception:
            # If description step fails, continue without descriptions
            return {f: {"semantic_description": "", "use_case": ""} for f in fields}

    def _rag_query(self, query: str, collection_name: str) -> List[Dict[str, Any]]:
        """Query RAG and return structured list of result dicts. Gracefully handle missing config."""
        try:
            from tools.rag_tools import retrieve_from_rag
            raw = retrieve_from_rag(query, collection_name, limit=3)
            try:
                return json.loads(raw)
            except Exception:
                # If the tool returned markdown or error text, wrap it
                if isinstance(raw, str) and raw.startswith("❌"):
                    return [{"error": raw}]
                return [{"text": raw}]
        except Exception as e:
            return [{"error": f"RAG unavailable: {e}"}]

    def _enhance_with_rag(self, fields: List[str], collection_name: str) -> Tuple[Dict[str, List[Dict[str, Any]]], str]:
        """For each field, gather ground-truth snippets from the uploaded OpenAPI spec via RAG.

        Returns tuple: (evidence_by_field, rag_status_note)
        """
        evidence: Dict[str, List[Dict[str, Any]]] = {}
        rag_note = ""
        for field in fields:
            queries = [
                f"{field} property schema definition",
                f"{field} parameter definition in request or response",
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
            # Deduplicate by text
            seen_text = set()
            deduped: List[Dict[str, Any]] = []
            for item in field_results:
                t = item.get('text', '')
                if t and t not in seen_text:
                    seen_text.add(t)
                    deduped.append(item)
            # Sort by semantic_score desc
            deduped.sort(key=lambda x: x.get('semantic_score', 0.0), reverse=True)
            evidence[field] = deduped[:3]

        return evidence, rag_note

    async def process_json_with_combined_analysis(
        self, 
        json_data: Dict[str, Any], 
        json_file_path: str = "",
        current_directory: str = "",
        collection_name: str = "flip_api_v2"
    ) -> AgentResponse:
        """Main analysis method: AI extraction + RAG-backed enrichment + JSON/Markdown outputs."""
        try:
            print("🚀 Starting simplified field analysis...")

            # 1) Extract fields via AI
            fields = self._extract_fields_via_ai(json_data)
            if not fields:
                return AgentResponse(
                    status="error",
                    agent_name="CombinedFieldAnalysisAgent",
                    error="No fields extracted by AI",
                    result=None
                )

            # 2) Describe fields via AI (short semantic + use-case)
            descriptions = self._describe_fields_via_ai(fields, json_data)

            # 3) Enhance using RAG against the uploaded API spec (ground-truth snippets)
            evidence, rag_note = self._enhance_with_rag(fields, collection_name)

            # Compute a simple confidence from RAG coverage
            scores: List[float] = []
            for f in fields:
                for ev in evidence.get(f, []):
                    scores.append(float(ev.get('semantic_score', 0.0)))
            avg_score = sum(scores) / len(scores) if scores else 0.0

            # Build analysis_result for persistence
            analysis_result: Dict[str, Any] = {
                "fields": fields,
                "descriptions": descriptions,
                "evidence": evidence,
                "processing_context": "HR field analysis",
                "enhancement_confidence": round(avg_score, 3),
                "total_fields_identified": len(fields)
            }
            if rag_note:
                analysis_result["rag_status_note"] = rag_note

            # Save results
            print("💾 Saving results...")
            json_path, md_path = self._save_results(
                analysis_result, json_file_path, current_directory
            )

            # Build standardized ProcessedResult
            extracted_fields_map = {
                f: {
                    "description": descriptions.get(f, {}).get("semantic_description", ""),
                    "use_case": descriptions.get(f, {}).get("use_case", ""),
                    "evidence_count": len(evidence.get(f, [])),
                }
                for f in fields
            }

            context_lines = [
                "# Field Analysis Results",
                "",
                "## 📊 Summary",
                f"- Fields Found: {len(fields)}",
                f"- RAG Evidence Coverage (avg top-score): {avg_score:.2f}",
            ]
            if rag_note:
                context_lines.append(f"- RAG Note: {rag_note}")
            context_lines.extend([
                "",
                "## Fields",
            ])
            for f in fields:
                desc = descriptions.get(f, {}).get("semantic_description", "")
                uc = descriptions.get(f, {}).get("use_case", "")
                evn = len(evidence.get(f, []))
                context_lines.append(f"- {f}: {desc or 'n/a'} (use: {uc or 'n/a'}) [evidence: {evn}]")
            context_lines.extend([
                "",
                "## 📁 Files",
                f"- JSON: {json_path or 'N/A'}",
                f"- Markdown: {md_path or 'N/A'}",
            ])
            context = "\n".join(context_lines)

            result = ProcessedResult(
                extracted_fields=extracted_fields_map,
                validation_status="completed" if scores else "partial",
                confidence_score=avg_score,
                processing_notes=f"AI extracted {len(fields)} fields; RAG evidence added where available",
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