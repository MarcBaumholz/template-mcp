"""
Simple Reasoning Agent for HR API Mapping
Simplified version with integrated proof tool functionality

Adds Phase-2 endpoint hallucination proofing:
- Extracts claimed endpoints from mapping texts
- Verifies against OpenAPI spec paths/methods
- Writes a file listing endpoints to re-search
- Returns actionable research commands
"""

import json
import os
import re
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

import yaml

from .llm_client import get_llm_response
from .api_spec_getter import get_api_spec_with_direct_llm_query, CONTEXT_WINDOW_CHAR_LIMIT
from .rag_tools import (
    upload_openapi_spec_to_rag,
    analyze_fields_with_rag_and_llm,
    retrieve_from_rag,
)

HIGH_LEVEL_GOAL = "Map HR data fields to API specification with verification and creative solutions"


def save_report(directory: str, content: str, prefix: str) -> str:
    """Save report with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"{prefix}_{timestamp}.md"
    report_path = Path(directory) / report_filename
    
    os.makedirs(directory, exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return str(report_path)


def _load_spec_paths(api_spec_path: str) -> Dict[str, Any]:
    """Load OpenAPI spec and return normalized path-method map.

    Args:
        api_spec_path: Path to OpenAPI spec (json/yaml)

    Returns:
        Dict with structure {"paths": {"/path": ["POST", "GET", ...]}}
    """
    with open(api_spec_path, "r", encoding="utf-8") as f:
        if api_spec_path.endswith((".yaml", ".yml")):
            spec = yaml.safe_load(f)
        else:
            spec = json.load(f)

    paths = spec.get("paths", {}) or {}
    normalized: Dict[str, Any] = {"paths": {}}
    for path, methods in paths.items():
        if isinstance(methods, dict):
            method_list = [m.upper() for m in methods.keys() if isinstance(m, str)]
            normalized["paths"][path] = method_list
    return normalized


def _extract_claimed_endpoints(text: str) -> List[Dict[str, str]]:
    """Extract claimed endpoints like 'POST /absences' from free text.

    Args:
        text: Input text containing potential endpoint mentions

    Returns:
        List of {"method": METHOD, "path": PATH}
    """
    pattern = re.compile(r"\b(POST|PUT|PATCH|GET|DELETE)\s+(/[A-Za-z0-9_\-\./{}]+)")
    found = pattern.findall(text or "")
    unique = {(m.upper(), p) for (m, p) in found}
    return [{"method": m, "path": p} for (m, p) in sorted(unique)]


def _verify_claimed_endpoints(
    claimed: List[Dict[str, str]], spec_paths: Dict[str, Any]
) -> Dict[str, List[Dict[str, str]]]:
    """Verify claimed endpoints against spec.

    Args:
        claimed: List of endpoint claims with method and path
        spec_paths: Output of _load_spec_paths

    Returns:
        Dict with keys 'verified' and 'unverified'
    """
    verified: List[Dict[str, str]] = []
    unverified: List[Dict[str, str]] = []

    spec_map: Dict[str, List[str]] = spec_paths.get("paths", {})

    for claim in claimed:
        path = claim.get("path", "")
        method = (claim.get("method", "") or "").upper()
        methods = spec_map.get(path)
        if methods and method in methods:
            verified.append({"method": method, "path": path})
        else:
            reason = "not_in_spec_or_method_mismatch"
            unverified.append({"method": method, "path": path, "reason": reason})

    return {"verified": verified, "unverified": unverified}


def _format_unverified_endpoints_md(unverified: List[Dict[str, str]]) -> str:
    """Format unverified endpoints list as markdown."""
    if not unverified:
        return "✅ All claimed endpoints are found in the spec."
    lines: List[str] = ["# ❗ Endpoints to (Re)Search", ""]
    for idx, e in enumerate(unverified, start=1):
        reason = e.get("reason", "unverified")
        lines.append(f"{idx}. `{e['method']} {e['path']}` — {reason}")
    return "\n".join(lines) + "\n"


def _format_endpoint_list(endpoints: List[Dict[str, str]], max_items: int = 3) -> str:
    """Format a list of endpoints as short code strings like `POST /path`.

    Args:
        endpoints: List of {method, path}
        max_items: cap for display

    Returns:
        Comma-separated short list
    """
    unique: List[str] = []
    for e in endpoints[:max_items]:
        method = (e.get("method") or "").upper()
        path = e.get("path") or ""
        pair = f"{method} {path}".strip()
        if pair and pair not in unique:
            unique.append(pair)
    return ", ".join(unique) if unique else "-"


def triangulate_candidates(
    fields: List[str],
    collection_name: str,
    api_spec_path: str,
    analysis_md_path: str,
    output_directory: str,
    context_topic: str = "HR Management API Mapping",
) -> Dict[str, Any]:
    """Run all three search strategies and build a per-field consensus table.

    Strategies:
    - query_api_specification (retrieve_from_rag): per-field targeted queries
    - enhanced_rag_analysis (analyze_fields_with_rag_and_llm): LLM-synthesized mapping text
    - get_direct_api_mapping_prompt + LLM: direct semantic mapping (if spec fits)

    Returns:
        Dict with keys: summary_path (str), rows (List[Dict])
    """
    rows: List[Dict[str, Any]] = []

    # 1) Enhanced RAG over all fields (one call) – text result
    try:
        enhanced_text = analyze_fields_with_rag_and_llm(
            fields=fields,
            collection_name=collection_name,
            context_topic=context_topic,
            current_path=output_directory,
        )
    except Exception as _e_enh:
        enhanced_text = f"❌ enhanced_rag_analysis failed: {_e_enh}"

    # 2) Direct prompt mapping (one call) – text result
    try:
        direct_prompt = get_api_spec_with_direct_llm_query(api_spec_path, analysis_md_path)
        if direct_prompt.startswith("❌"):
            direct_text = direct_prompt
        else:
            direct_text = get_llm_response(direct_prompt, max_tokens=4096)
    except Exception as _e_dir:
        direct_text = f"❌ direct mapping failed: {_e_dir}"

    # Build per-field rows
    for field in fields:
        # 2a) query_api_specification variant via retrieve_from_rag
        query_texts: List[str] = []
        try:
            # Prefer method filters per rules
            q1 = f"POST {field} parameter"
            q2 = f"create {field} request body"
            query_texts.append(
                retrieve_from_rag(q1, collection_name, limit=5, score_threshold=0.5, current_path=output_directory)
            )
            query_texts.append(
                retrieve_from_rag(q2, collection_name, limit=5, score_threshold=0.5, current_path=output_directory)
            )
        except Exception as _e_q:
            query_texts.append(f"❌ query failed: {_e_q}")

        # Extract endpoints from each source
        endpoints_query: List[Dict[str, str]] = []
        for t in query_texts:
            endpoints_query.extend(_extract_claimed_endpoints(t))
        # Deduplicate
        endpoints_query = [dict(t) for t in { (e.get("method",""), e.get("path","")) for e in endpoints_query }]
        endpoints_enhanced = _extract_claimed_endpoints(enhanced_text)
        endpoints_direct = _extract_claimed_endpoints(direct_text)

        # Compute consensus: any endpoint appearing in at least two sources
        def to_key_list(lst: List[Dict[str, str]]) -> List[str]:
            return [f"{(e.get('method') or '').upper()} {(e.get('path') or '')}".strip() for e in lst if e.get('path')]

        s_query = set(to_key_list(endpoints_query))
        s_enh = set(to_key_list(endpoints_enhanced))
        s_direct = set(to_key_list(endpoints_direct))

        candidates_all = list(s_query | s_enh | s_direct)
        support_counts = {c: (1 if c in s_query else 0) + (1 if c in s_enh else 0) + (1 if c in s_direct else 0) for c in candidates_all}
        consensus = [c for c, n in support_counts.items() if n >= 2]

        rows.append({
            "field": field,
            "query_hits": endpoints_query,
            "enhanced_hits": endpoints_enhanced,
            "direct_hits": endpoints_direct,
            "consensus": consensus[:3],
        })

    # Write summary markdown
    lines: List[str] = ["# 🔀 Triangulation Summary (ToT)", "", "Per-field comparison of three strategies: query_api_specification, enhanced_rag_analysis, direct semantic mapping.", ""]
    lines.append("| Field | query_api_spec | enhanced_rag | direct_prompt | consensus |")
    lines.append("|---|---|---|---|---|")
    for r in rows:
        lines.append(
            f"| `{r['field']}` | {_format_endpoint_list(r['query_hits'])} | {_format_endpoint_list(r['enhanced_hits'])} | {_format_endpoint_list(r['direct_hits'])} | {', '.join(r['consensus']) if r['consensus'] else '-'} |"
        )

    summary_path = save_report(output_directory, "\n".join(lines), "triangulation_summary")
    return {"summary_path": summary_path, "rows": rows}

def perform_endpoint_verification(
    api_spec_path: str,
    mapping_text: str,
    verification_text: str,
    output_directory: str,
    collection_name: str,
) -> Dict[str, Any]:
    """Verify claimed endpoints and write an endpoints-to-research file.

    Args:
        api_spec_path: Path to the OpenAPI spec
        mapping_text: Main mapping text (e.g., mapping_response)
        verification_text: Additional verification text (e.g., LLM verification)
        output_directory: Directory to write the artifact
        collection_name: RAG collection for suggested commands

    Returns:
        Dict with keys: verified (list), unverified (list), file_path (str), research_cmds (list)
    """
    spec_paths = _load_spec_paths(api_spec_path)
    claims = _extract_claimed_endpoints((mapping_text or "") + "\n" + (verification_text or ""))
    result = _verify_claimed_endpoints(claims, spec_paths)

    # Save unverified endpoints list
    endpoints_md = _format_unverified_endpoints_md(result["unverified"]) 
    endpoints_file = save_report(output_directory, endpoints_md, "endpoints_to_research")

    # Build research commands for MCP tool
    research_cmds: List[str] = []
    for e in result["unverified"]:
        cmd = (
            f'query_api_specification(\n'
            f'  query="{e["method"]} {e["path"]}",\n'
            f'  collection_name="{collection_name}",\n'
            f'  limit=10,\n'
            f'  current_path="{output_directory}"\n'
            f')'
        )
        research_cmds.append(cmd)

    return {
        "verified": result["verified"],
        "unverified": result["unverified"],
        "file_path": endpoints_file,
        "research_cmds": research_cmds,
    }


def extract_unmapped_fields(mapping_content: str) -> List[str]:
    """Extract unmapped fields from mapping report."""
    unmapped_fields = []
    lines = mapping_content.lower().split('\n')
    
    for line in lines:
        if any(keyword in line for keyword in ['unmapped', 'no match', 'missing', 'not found', 'todo']):
            # Try to extract field name
            if '|' in line:
                parts = line.split('|')
                if len(parts) > 1:
                    field = parts[1].strip().replace('`', '').replace('*', '')
                    if field and field not in ['field', 'source field']:
                        unmapped_fields.append(field)
    
    return list(set(unmapped_fields))  # Remove duplicates


def generate_creative_solutions(unmapped_fields: List[str], api_spec_content: str) -> Dict[str, str]:
    """Generate creative solutions for unmapped fields."""
    if not unmapped_fields:
        return {}
    
    solutions = {}
    
    for field in unmapped_fields:
        solution_prompt = f"""
Field "{field}" could not be mapped to the API specification.

API Specification (first 1000 chars):
{api_spec_content[:1000]}

Generate creative solutions for how this field could be:
1. Mapped to existing API fields (with transformation)
2. Derived from multiple API fields
3. Implemented as calculated field
4. Handled with default values
5. Transformed using business logic

Keep response concise and practical.
"""
        
        try:
            solution = get_llm_response(solution_prompt, max_tokens=800)
            solutions[field] = solution
        except Exception as e:
            solutions[field] = f"Error generating solution: {str(e)}"
    
    return solutions


async def reasoning_agent(
    source_analysis_path: str,
    api_spec_path: str,
    output_directory: str,
    target_collection_name: Optional[str] = None
) -> str:
    """
    Simple reasoning agent for HR API mapping with integrated proof tool.
    
    Args:
        source_analysis_path: Path to source field analysis markdown
        api_spec_path: Path to OpenAPI specification
        output_directory: Output directory for reports
        target_collection_name: Optional RAG collection name
    """
    try:
        # Validate inputs
        source_path = Path(source_analysis_path)
        spec_path = Path(api_spec_path)
        
        if not source_path.exists():
            return f"❌ Source analysis not found: {source_analysis_path}"
        if not spec_path.exists():
            return f"❌ API spec not found: {api_spec_path}"
        if not Path(output_directory).exists():
            return f"❌ Output directory not found: {output_directory}"

        # Read files
        analysis_content = source_path.read_text(encoding='utf-8')
        api_spec_content = spec_path.read_text(encoding='utf-8')
        
        # Choose strategy: Direct vs RAG
        total_chars = len(analysis_content) + len(api_spec_content)
        collection_name = target_collection_name or spec_path.stem.replace('.', '_').replace('-', '_')
        
        # Extract source fields from analysis markdown (used in both branches)
        source_fields: List[str] = []
        for line in analysis_content.splitlines():
            if '|' in line and 'Source Field' not in line and '---' not in line:
                parts = line.split('|')
                if len(parts) > 1:
                    field = parts[1].strip().replace('`', '')
                    if field:
                        source_fields.append(field)
        
        if total_chars <= CONTEXT_WINDOW_CHAR_LIMIT:
            # Direct analysis - fits in context window
            print("📝 Using direct LLM analysis (small spec)")
            
            prompt = get_api_spec_with_direct_llm_query(api_spec_path, source_analysis_path)
            if prompt.startswith("❌"):
                return prompt
                
            mapping_response = get_llm_response(prompt, max_tokens=4096)
            strategy_log = "Direct LLM analysis (small spec)"
            
        else:
            # RAG-based analysis - spec too large
            print(f"📚 Using RAG-based analysis (large spec: {total_chars} chars)")
            
            # Upload to RAG
            upload_result = upload_openapi_spec_to_rag(api_spec_path, collection_name)
            print(f"RAG Upload: {upload_result}")
            
            if not source_fields:
                return "❌ No source fields found in analysis markdown"
            
            mapping_response = analyze_fields_with_rag_and_llm(
                fields=source_fields,
                collection_name=collection_name,
                context_topic="HR Management API Mapping",
                current_path=output_directory
            )
            strategy_log = f"RAG-based analysis (spec: {total_chars} chars)"
        
        # Step: Query API spec via RAG tool for each source field (saves enhanced MD files)
        rag_query_summaries: List[str] = []
        if source_fields:
            # Ensure collection exists for queries (safe if already present)
            try:
                upload_openapi_spec_to_rag(api_spec_path, collection_name)
            except Exception:
                pass
            for field in source_fields:
                try:
                    q = f"{field} parameter property field"
                    summary = retrieve_from_rag(q, collection_name, limit=2, score_threshold=0.5, current_path=output_directory)
                    rag_query_summaries.append(summary)
                except Exception as _e:
                    rag_query_summaries.append(f"❌ Query failed for '{field}': {_e}")
        
        # Step: Direct prompt verification (get_direct_api_mapping_prompt)
        direct_prompt_result = get_api_spec_with_direct_llm_query(api_spec_path, source_analysis_path)
        verification_response = ""
        if not direct_prompt_result.startswith("❌"):
            try:
                verification_response = get_llm_response(direct_prompt_result, max_tokens=4096)
            except Exception as _e:
                verification_response = f"❌ Direct verification failed: {_e}"
        else:
            verification_response = direct_prompt_result  # propagate size/validation error
        
        # Proof tool integration: Find unmapped fields
        print("🔍 Analyzing unmapped fields...")
        unmapped_fields = extract_unmapped_fields(mapping_response)
        print(f"Found {len(unmapped_fields)} unmapped fields: {unmapped_fields}")
        
        # Triangulation step (ToT): compare the three strategies per field
        triangulation_md_path = ""
        try:
            if source_fields:
                tri = triangulate_candidates(
                    fields=source_fields,
                    collection_name=collection_name,
                    api_spec_path=api_spec_path,
                    analysis_md_path=source_analysis_path,
                    output_directory=output_directory,
                )
                triangulation_md_path = tri.get("summary_path", "")
        except Exception as _e_tri:
            triangulation_md_path = f"❌ Triangulation failed: {_e_tri}"

        # Generate creative solutions
        creative_solutions = generate_creative_solutions(unmapped_fields, api_spec_content)
        
        # Generate comprehensive report
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Precompute RAG references to avoid backslashes in f-string expressions
        if rag_query_summaries:
            rag_refs_lines = os.linesep.join(['- ' + s.split('\n', 1)[0] for s in rag_query_summaries])
        else:
            rag_refs_lines = 'No RAG queries executed.'

        report_content = f"""# 🚀 Simple Reasoning Agent Report

## 🎯 Goal
{HIGH_LEVEL_GOAL}

## 📊 Analysis Summary
- **Timestamp**: {timestamp}
- **Strategy**: {strategy_log}
- **Source Analysis**: `{source_analysis_path}`
- **API Specification**: `{api_spec_path}`
- **RAG Collection**: `{collection_name}`

---

## 🗺️ Mapping Analysis

{mapping_response}

---

## 🔎 RAG Query References (per field)

{rag_refs_lines}

---

## ✅ Direct Mapping Verification (get_direct_api_mapping_prompt)

{verification_response}

---

## 🔀 Tree‑of‑Thought Triangulation

Summary file: `{triangulation_md_path or 'N/A'}`

---

## 🔍 Proof Tool Analysis

### 📊 Unmapped Fields ({len(unmapped_fields)} found)

{format_unmapped_fields(unmapped_fields)}

### 💡 Creative Solutions

{format_creative_solutions(creative_solutions)}

---

## ✅ Implementation Checklist

1. **Review Mappings**: Verify all direct field mappings are correct
2. **Apply Solutions**: Implement creative solutions for unmapped fields
3. **Add Transformations**: Create data transformation functions where needed
4. **Test Mappings**: Test with sample data
5. **Handle Errors**: Add error handling for missing/invalid data

## 🎯 Next Steps

1. Implement direct field mappings from the analysis above
2. Apply creative solutions for unmapped fields
3. Create transformation functions for complex mappings
4. Test thoroughly with real data samples
5. Document any assumptions or limitations

---

*Generated by Simple Reasoning Agent with integrated Proof Tool*
        """

        # Phase 2: Endpoint hallucination proofing
        try:
            proof = perform_endpoint_verification(
                api_spec_path=api_spec_path,
                mapping_text=mapping_response,
                verification_text=verification_response,
                output_directory=output_directory,
                collection_name=collection_name,
            )

            research_cmds_md = (
                "\n".join(f"- {c}" for c in proof["research_cmds"]) if proof["research_cmds"] else "- None"
            )

            report_content += f"""

---
## 🧷 Endpoint Verification (Ground Truth)
- Verified: {len(proof['verified'])}
- Unverified: {len(proof['unverified'])}
- Details file: `{proof['file_path']}`

### ▶️ Research Commands (run via MCP)
{research_cmds_md}
"""

            # Auto re-run direct mapping verification focused on unverified endpoints
            if proof["unverified"]:
                try:
                    original_analysis = Path(source_analysis_path).read_text(encoding='utf-8')
                    focus_lines = ["## 🔁 Focus Re-Verification: Unverified Endpoints", "", "Please validate the following endpoints strictly against the spec. If invalid, suggest the correct endpoint(s) and provide request body schema pointers:"]
                    for e in proof["unverified"]:
                        focus_lines.append(f"- `{e['method']} {e['path']}` — reason: {e.get('reason','unverified')}")
                    focus_lines.append("")
                    focus_content = original_analysis + "\n\n" + "\n".join(focus_lines)
                    focus_md_path = save_report(output_directory, focus_content, "analysis_focus_unverified")

                    retry_prompt = get_api_spec_with_direct_llm_query(api_spec_path, focus_md_path)
                    if not retry_prompt.startswith("❌"):
                        try:
                            retry_response = get_llm_response(retry_prompt, max_tokens=4096)
                        except Exception as _re:
                            retry_response = f"❌ Direct re-verification failed: {_re}"
                    else:
                        retry_response = retry_prompt

                    report_content += f"""

---
## 🔁 Direct Mapping Re-Verification (Unverified Endpoints)
{retry_response}
"""
                except Exception as _e2:
                    report_content += f"\n\n---\n## 🔁 Direct Mapping Re-Verification\n❌ Re-run failed: {_e2}\n"
        except Exception as _e:
            # Keep the agent robust even if verification fails
            report_content += f"\n\n---\n## 🧷 Endpoint Verification\n❌ Verification step failed: {_e}\n"
        
        # Save report
        report_path = save_report(output_directory, report_content, "simple_reasoning_agent_report")
        
        print(f"✅ Report saved to: {report_path}")
        return report_path
        
    except Exception as e:
        return f"❌ Reasoning agent failed: {str(e)}"


def format_unmapped_fields(unmapped_fields: List[str]) -> str:
    """Format unmapped fields for display."""
    if not unmapped_fields:
        return "✅ **All fields mapped successfully!**"
    
    formatted = "🔴 **Fields needing attention:**\n\n"
    for i, field in enumerate(unmapped_fields, 1):
        formatted += f"{i}. `{field}`\n"
    
    return formatted


def format_creative_solutions(solutions: Dict[str, str]) -> str:
    """Format creative solutions for display."""
    if not solutions:
        return "✅ **No creative solutions needed - all fields mapped!**"
    
    formatted = ""
    for field, solution in solutions.items():
        formatted += f"### 💡 Solutions for `{field}`\n\n"
        formatted += f"{solution}\n\n"
        formatted += "---\n\n"
    
    return formatted