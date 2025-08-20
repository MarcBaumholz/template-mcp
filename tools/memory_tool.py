"""
Long-term Memory Tool (RAG-backed) for Phase Learnings

Purpose:
- After Phase 2 and Phase 3 succeed, generate a concise learnings report
- Persist as markdown and embed into Vector DB (Qdrant) for long-term memory

Safety:
- Gated: refuses to persist if verification indicates unresolved issues
"""

from __future__ import annotations

import os
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .llm_client import get_llm_response
from .rag_tools import get_rag_system


@dataclass
class PhaseLearnings:
    """Container for phase-specific learnings."""
    dos: List[str]
    donts: List[str]
    how_tos: List[str]


def _read_text_file(path: str) -> str:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return p.read_text(encoding="utf-8")


def _simple_extract_learnings(markdown: str) -> PhaseLearnings:
    """Heuristic extractor for learnings from markdown without LLM.

    Rules:
    - Lines starting with '- Do:' or containing '✅' => do
    - Lines starting with "- Don't:" or containing '❌' => don't
    - Lines containing 'How to:' or starting with '- How to' => how-to
    """
    dos: List[str] = []
    donts: List[str] = []
    how_tos: List[str] = []

    for raw_line in (markdown or "").splitlines():
        line = raw_line.strip()
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


def _extract_learnings_with_llm(markdown: str) -> PhaseLearnings:
    """Use LLM to extract structured learnings. Falls back to heuristic on error."""
    prompt = f"""
You are an expert technical editor. Extract only concrete, actionable learnings as three lists:
- dos: concise best practices (max 5)
- donts: pitfalls to avoid (max 5)
- how_tos: short implementation tips (max 5)

Source markdown (trim noise, no hallucinations):
"""
    try:
        resp = get_llm_response(prompt + "\n\n" + markdown, max_tokens=800)
        # Very tolerant JSON-ish parsing
        if isinstance(resp, str) and resp.strip().startswith("{"):
            data = json.loads(resp)
            return PhaseLearnings(
                dos=list(data.get("dos", []))[:5],
                donts=list(data.get("donts", []))[:5],
                how_tos=list(data.get("how_tos", []))[:5],
            )
    except Exception:
        pass
    return _simple_extract_learnings(markdown)


def _build_learnings_markdown(
    phase2: Optional[PhaseLearnings], phase3: Optional[PhaseLearnings], meta: Dict[str, str], chat: Optional[PhaseLearnings] = None
) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines: List[str] = [
        f"# 📚 Project Learnings",
        f"Generated: {timestamp}",
        f"Context: {meta.get('context', 'N/A')}",
        "",
    ]

    def section(title: str, learn: PhaseLearnings):
        lines.append(f"## {title}")
        if learn.dos:
            lines.append("### ✅ Do's")
            for item in learn.dos:
                lines.append(f"- {item}")
        if learn.donts:
            lines.append("### ❌ Don'ts")
            for item in learn.donts:
                lines.append(f"- {item}")
        if learn.how_tos:
            lines.append("### 🧭 How-Tos")
            for item in learn.how_tos:
                lines.append(f"- {item}")
        lines.append("")

    if phase2:
        section("Phase 2 Learnings", phase2)
    if phase3:
        section("Phase 3 Learnings", phase3)
    if chat:
        section("Chat/Memory Log Learnings", chat)

    return "\n".join(lines)


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
    try:
        content = _read_text_file(verification_file_path)
    except Exception as e:
        return False, f"Verification file error: {e}"

    if "All claimed endpoints are found" in content:
        return True, "Phase 2 verification passed"
    # If there is a header with items following, treat as failed
    if "Endpoints to (Re)Search" in content and any(
        l.strip().startswith(("1.", "- ")) for l in content.splitlines()
    ):
        return False, "Unverified endpoints present"
    # Default to strict mode: reject if unclear
    return False, "Unable to confirm verification success"


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
    """
    # Gates
    ok2, reason2 = _verification_passed(verification_file_path)
    if not ok2:
        return f"❌ Not saving to memory: Phase 2 verification failed – {reason2}"
    if not phase3_verified:
        return "❌ Not saving to memory: Phase 3 not verified as correct"

    # Read inputs
    phase2_md = _read_text_file(phase2_report_path)
    phase3_md = _read_text_file(phase3_report_path)
    chat_md: Optional[str] = None
    if memory_log_path:
        try:
            chat_md = _read_text_file(memory_log_path)
        except Exception:
            chat_md = None

    # Extract learnings
    p2 = _extract_learnings_with_llm(phase2_md)
    p3 = _extract_learnings_with_llm(phase3_md)
    pc: Optional[PhaseLearnings] = _extract_learnings_with_llm(chat_md) if chat_md else None

    if not (p2.dos or p2.donts or p2.how_tos or p3.dos or p3.donts or p3.how_tos or (pc and (pc.dos or pc.donts or pc.how_tos))):
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
    try:
        status = _embed_markdown_to_rag(str(out_path), collection_name)
        return f"{status}\n📄 File: {out_path}"
    except Exception as e:
        return f"❌ Failed to embed learnings: {e}\n📄 File still created: {out_path}"


