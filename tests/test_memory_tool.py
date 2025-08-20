import os
import sys
import tempfile
from pathlib import Path

import pytest

# Ensure project root on path
sys.path.append(str(Path(__file__).parent.parent))


def test_persist_learnings_gated_saves_only_on_success(tmp_path):
    from tools.memory_tool import persist_learnings

    # Create dummy phase reports
    phase2 = tmp_path / "phase2_report.md"
    phase2.write_text(
        """
        ## Notes
        - Do: Use POST endpoint filtering
        - Don't: Map to GET list endpoints
        - How to: Verify endpoints via spec paths
        """.strip(),
        encoding="utf-8",
    )

    # Verification file indicating success
    verification_ok = tmp_path / "endpoints_to_research.md"
    verification_ok.write_text("✅ All claimed endpoints are found in the spec.", encoding="utf-8")

    phase3 = tmp_path / "phase3_report.md"
    phase3.write_text(
        """
        ## Results
        - Do: Keep code generation small and modular
        - Don't: Hardcode environment variables
        - How to: Pin versions in requirements.txt
        """.strip(),
        encoding="utf-8",
    )

    # When gates pass but we skip embeddings
    result_ok = persist_learnings(
        phase2_report_path=str(phase2),
        verification_file_path=str(verification_ok),
        phase3_report_path=str(phase3),
        phase3_verified=True,
        collection_name="test_long_term_memory",
        output_directory=str(tmp_path),
        embed=False,
    )
    assert "Learnings report created" in result_ok

    # If verification fails, memory should not persist
    verification_bad = tmp_path / "endpoints_to_research_bad.md"
    verification_bad.write_text(
        "# ❗ Endpoints to (Re)Search\n\n1. POST /unknown — not_in_spec_or_method_mismatch\n",
        encoding="utf-8",
    )
    result_bad = persist_learnings(
        phase2_report_path=str(phase2),
        verification_file_path=str(verification_bad),
        phase3_report_path=str(phase3),
        phase3_verified=True,
        collection_name="test_long_term_memory",
        output_directory=str(tmp_path),
        embed=False,
    )
    assert "Not saving to memory" in result_bad



