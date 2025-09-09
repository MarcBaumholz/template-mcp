"""
Long-term Memory Tool (RAG-backed) for Phase Learnings

Purpose:
- After Phase 2 and Phase 3 succeed, generate a concise learnings report
- Persist as markdown and embed into Vector DB (Qdrant) for long-term memory

Safety:
- Gated: refuses to persist if verification indicates unresolved issues
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .llm_client import get_llm_response
from tools.phase1_data_extraction.rag_core import get_rag_system


@dataclass
class PhaseLearnings:
    """Container for phase-specific learnings."""
    dos: List[str]
    donts: List[str]
    how_tos: List[str]


def _read_text_file(path: str) -> str:
    """Generic file reader with comprehensive error handling."""
    if not path or not path.strip():
        raise ValueError("File path cannot be empty")
    
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    try:
        return p.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        raise ValueError(f"File encoding error: {e}")
    except PermissionError as e:
        raise PermissionError(f"Permission denied: {e}")


def _extract_learnings(markdown: str) -> PhaseLearnings:
    """Extract structured learnings using LLM with heuristic fallback."""
    if not markdown or not markdown.strip():
        return PhaseLearnings(dos=[], donts=[], how_tos=[])
    
    # Try LLM extraction first
    prompt = """Extract actionable learnings as JSON:
{
  "dos": ["best practice 1", "best practice 2"],
  "donts": ["pitfall 1", "pitfall 2"], 
  "how_tos": ["tip 1", "tip 2"]
}
Max 5 items per category. Source:"""
    
    try:
        resp = get_llm_response(prompt + "\n\n" + markdown, max_tokens=800)
        if isinstance(resp, str) and resp.strip().startswith("{"):
            data = json.loads(resp)
            return PhaseLearnings(
                dos=list(data.get("dos", []))[:5],
                donts=list(data.get("donts", []))[:5],
                how_tos=list(data.get("how_tos", []))[:5],
            )
    except Exception:
        pass
    
    # Fallback to heuristic extraction
    return _heuristic_extract_learnings(markdown)


def _heuristic_extract_learnings(markdown: str) -> PhaseLearnings:
    """Heuristic extractor for learnings from markdown."""
    dos, donts, how_tos = [], [], []
    
    for line in (markdown or "").splitlines():
        line = line.strip()
        if not line:
            continue
            
        lower = line.lower()
        if lower.startswith("- do:") or "✅" in line:
            dos.append(line.lstrip("- "))
        elif lower.startswith("- don't:") or "❌" in line or "dont:" in lower:
            donts.append(line.lstrip("- "))
        elif "how to:" in lower or lower.startswith("- how to"):
            how_tos.append(line.lstrip("- "))
    
    return PhaseLearnings(dos=dos, donts=donts, how_tos=how_tos)


def _build_learnings_markdown(
    phase2: Optional[PhaseLearnings], phase3: Optional[PhaseLearnings], meta: Dict[str, str], chat: Optional[PhaseLearnings] = None
) -> str:
    """Build consolidated learnings markdown using template approach."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Template sections
    sections = [
        ("# 📚 Project Learnings", ""),
        (f"Generated: {timestamp}", ""),
        (f"Context: {meta.get('context', 'N/A')}", ""),
        ("", "")
    ]
    
    # Add learning sections
    for title, learnings in [
        ("Phase 2 Learnings", phase2),
        ("Phase 3 Learnings", phase3), 
        ("Chat/Memory Log Learnings", chat)
    ]:
        if learnings and (learnings.dos or learnings.donts or learnings.how_tos):
            sections.append((f"## {title}", ""))
            sections.extend(_format_learning_section(learnings))
            sections.append(("", ""))
    
    return "\n".join(line for line, _ in sections)


def _format_learning_section(learnings: PhaseLearnings) -> List[Tuple[str, str]]:
    """Format a learning section into markdown lines."""
    lines = []
    
    if learnings.dos:
        lines.append(("### ✅ Do's", ""))
        lines.extend((f"- {item}", "") for item in learnings.dos)
    
    if learnings.donts:
        lines.append(("### ❌ Don'ts", ""))
        lines.extend((f"- {item}", "") for item in learnings.donts)
    
    if learnings.how_tos:
        lines.append(("### 🧭 How-Tos", ""))
        lines.extend((f"- {item}", "") for item in learnings.how_tos)
    
    return lines


def _chunk_text(text: str, max_tokens: int = 800) -> List[str]:
    """Simple whitespace-based chunker, approximate tokens by chars/4."""
    approx_token = lambda s: max(1, len(s) // 4)
    words = text.split()
    chunks: List[str] = []
    current: List[str] = []
    current_tokens = 0
    for w in words:
        t = approx_token(w) + 1
        if current_tokens + t > max_tokens and current:
            chunks.append(" ".join(current))
            current, current_tokens = [], 0
        current.append(w)
        current_tokens += t
    if current:
        chunks.append(" ".join(current))
    return chunks


def _embed_markdown_to_rag(md_path: str, collection_name: str) -> str:
    """Embed markdown content to RAG collection."""
    rag = get_rag_system()
    text = _read_text_file(md_path)
    chunks = _chunk_text(text)

    # Make sure collection exists
    rag.create_collection(collection_name)

    # Prepare and upsert points
    vectors = [rag.encoder.encode(c).tolist() for c in chunks]

    from qdrant_client.models import PointStruct
    points: List[PointStruct] = []
    for idx, (c, vec) in enumerate(zip(chunks, vectors)):
        points.append(
            PointStruct(
                id=int(datetime.now().timestamp() * 1_000_000) + idx,
                vector=vec,
                payload={
                    "text": c,
                    "chunk_type": "learning",
                    "metadata": {
                        "source": str(md_path),
                        "created_at": datetime.now().isoformat(),
                    },
                },
            )
        )

    rag.client.upsert(collection_name=collection_name, points=points)
    return f"✅ Persisted {len(points)} learning chunks to collection '{collection_name}'"


def _verification_passed(verification_file_path: str) -> Tuple[bool, str]:
    """Check if Phase 2 verification passed using regex patterns."""
    try:
        content = _read_text_file(verification_file_path)
    except Exception as e:
        return False, f"Verification file error: {e}"

    # Check for verification rate patterns (handles edge case of 0% with 0 endpoints)
    verification_rate_match = re.search(r"Verification Rate:\s*(\d+)%", content, re.IGNORECASE)
    total_endpoints_match = re.search(r"Total Endpoints Claimed:\s*(\d+)", content, re.IGNORECASE)
    
    if verification_rate_match and total_endpoints_match:
        verification_rate = int(verification_rate_match.group(1))
        total_endpoints = int(total_endpoints_match.group(1))
        
        # Edge case: 0% verification rate with 0 total endpoints = success (nothing to verify)
        if total_endpoints == 0 and verification_rate == 0:
            return True, "Phase 2 verification passed (no endpoints to verify)"
        
        # Normal case: 100% verification rate = success
        if verification_rate == 100:
            return True, "Phase 2 verification passed (100% rate)"
        
        # Any other case with endpoints claimed but not 100% verified = failure
        if total_endpoints > 0 and verification_rate < 100:
            return False, f"Unverified endpoints present ({verification_rate}% rate with {total_endpoints} endpoints)"

    # Success patterns (fallback)
    success_patterns = [
        r"All claimed endpoints are found",
        r"✅.*verification.*passed",
        r"verification.*successful"
    ]
    
    # Failure patterns
    failure_patterns = [
        r"Endpoints to \(Re\)Search.*\n.*[1-9]\.",  # Header followed by numbered list
        r"❌.*endpoint.*not found",
        r"unverified.*endpoint"
    ]
    
    # Check for success
    for pattern in success_patterns:
        if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
            return True, "Phase 2 verification passed"
    
    # Check for failure
    for pattern in failure_patterns:
        if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
            return False, "Unverified endpoints present"
    
    # Default to strict mode: reject if unclear
    return False, "Unable to confirm verification success"


def _validate_inputs(
    phase2_report_path: str,
    verification_file_path: str, 
    phase3_report_path: str,
    collection_name: str,
    output_directory: str,
    memory_log_path: str
) -> Optional[str]:
    """Validate input parameters and return error message if invalid."""
    # Required file paths
    for path, name in [
        (phase2_report_path, "phase2_report_path"),
        (verification_file_path, "verification_file_path"),
        (phase3_report_path, "phase3_report_path")
    ]:
        if not path or not path.strip():
            return f"❌ {name} cannot be empty"
    
    # Collection name validation
    if not collection_name or not collection_name.strip():
        return "❌ collection_name cannot be empty"
    
    # Optional memory log path validation
    if memory_log_path and not memory_log_path.strip():
        return "❌ memory_log_path cannot be empty string"
    
    return None


def persist_learnings(
    phase2_report_path: str,
    verification_file_path: str,
    phase3_report_path: str,
    phase3_verified: bool,
    collection_name: str = "long_term_memory",
    output_directory: str = "",
    embed: bool = True,
    memory_log_path: str = "",
) -> str:
    """Persist concise learnings to vector DB after success gates.

    Args:
        phase2_report_path: Path to Phase 2 mapping report (markdown)
        verification_file_path: Path to endpoints verification file created in Phase 2
        phase3_report_path: Path to Phase 3 report/code summary (markdown)
        phase3_verified: Whether Phase 3 result is verified as correct
        collection_name: Target RAG collection
        output_directory: Where to write the consolidated learnings report
        embed: If False, skip embeddings (useful for tests)
        memory_log_path: Optional path to chat/memory log file
    """
    # Input validation
    validation_error = _validate_inputs(
        phase2_report_path, verification_file_path, phase3_report_path,
        collection_name, output_directory, memory_log_path
    )
    if validation_error:
        return validation_error

    # Verification gates
    ok2, reason2 = _verification_passed(verification_file_path)
    if not ok2:
        return f"❌ Not saving to memory: Phase 2 verification failed – {reason2}"
    if not phase3_verified:
        return "❌ Not saving to memory: Phase 3 not verified as correct"

    # Read and process inputs
    try:
        phase2_md = _read_text_file(phase2_report_path)
        phase3_md = _read_text_file(phase3_report_path)
        chat_md: Optional[str] = None
        
        if memory_log_path:
            try:
                chat_md = _read_text_file(memory_log_path)
            except Exception:
                chat_md = None  # Optional file, continue without it

        # Extract learnings
        p2 = _extract_learnings(phase2_md)
        p3 = _extract_learnings(phase3_md)
        pc = _extract_learnings(chat_md) if chat_md else None

        # Check if any learnings found
        if not (p2.dos or p2.donts or p2.how_tos or p3.dos or p3.donts or p3.how_tos or 
                (pc and (pc.dos or pc.donts or pc.how_tos))):
            return "ℹ️ No actionable learnings found – nothing persisted"

        # Build and save consolidated file
        meta = {"context": "Phase 2 & 3 Post-Run Learnings"}
        consolidated = _build_learnings_markdown(p2, p3, meta, chat=pc)
        
        outdir = Path(output_directory or ".")
        outdir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = outdir / f"learnings_report_{ts}.md"
        out_path.write_text(consolidated, encoding="utf-8")

        if not embed:
            return f"✅ Learnings report created (embedding skipped): {out_path}"

        # Embed to vector DB
        status = _embed_markdown_to_rag(str(out_path), collection_name)
        return f"{status}\n📄 File: {out_path}"
        
    except Exception as e:
        return f"❌ Failed to process learnings: {e}"


