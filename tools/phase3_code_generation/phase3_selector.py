"""
Phase 3 MCP Tool: Consistency Selector

Selects the best Kotlin candidate among multiple files using:
- Rule audit violations (from Quality Suite)
- Simple heuristics (file size sanity, presence of key annotations)
- Optional future extension: test pass rates / compile results
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import json

from .phase3_quality_suite import audit_kotlin_code


def _heuristics_score(code: str) -> int:
    score = 0
    # Reward presence of key annotations and structures
    tokens = ["@Controller", "@Secured", "@Singleton", "HttpResponse", "object Mapper"]
    for t in tokens:
        if t in code:
            score += 1
    # Penalize extremely short files
    if len(code) < 300:
        score -= 2
    return score


def select_best_candidate(
    kotlin_files: List[str],
    mapping_report_path: str,
    model: str = "qwen/qwen3-coder:free",
) -> Dict[str, Any]:
    if not kotlin_files:
        return {"error": "No candidate files provided"}

    results: List[Dict[str, Any]] = []
    for fp in kotlin_files:
        try:
            code = Path(fp).read_text(encoding="utf-8")
        except Exception as e:
            results.append({"file": fp, "error": str(e)})
            continue
        audit = audit_kotlin_code(fp, model=model)
        violations = audit.get("violations", [])
        v_penalty = len(violations)
        h_score = _heuristics_score(code)
        total = h_score - v_penalty
        results.append({
            "file": fp,
            "violations": violations,
            "suggestions": audit.get("suggestions", []),
            "heuristics": h_score,
            "score": total,
        })

    # Choose best by highest score, tie-breaker by fewer violations
    best = sorted(results, key=lambda r: (r.get("score", -999), -len(r.get("violations", []))), reverse=True)[0]
    return {"candidates": results, "best": best}


def register_tool():
    return {
        "name": "phase3_select_best_candidate",
        "description": "Pick best Kotlin candidate using rule audits and heuristics",
        "input_schema": {
            "type": "object",
            "properties": {
                "kotlin_files": {"type": "array", "items": {"type": "string"}},
                "mapping_report_path": {"type": "string"},
                "model": {"type": "string", "default": "qwen/qwen3-coder:free"}
            },
            "required": ["kotlin_files", "mapping_report_path"]
        },
        "handler": select_best_candidate
    }


