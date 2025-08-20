import os
import sys
import json
import tempfile
from pathlib import Path

import pytest

# Ensure project root is on sys.path
sys.path.append(str(Path(__file__).parent.parent))


def write_spec(tmpdir: str, content: dict, yaml: bool = False) -> str:
    path = os.path.join(tmpdir, f"spec.{ 'yml' if yaml else 'json'}")
    with open(path, "w", encoding="utf-8") as f:
        if yaml:
            import yaml as _yaml
            _yaml.safe_dump(content, f)
        else:
            json.dump(content, f)
    return path


def test_perform_endpoint_verification_basic():
    from tools.reasoning_agent import perform_endpoint_verification

    # Create a minimal spec with two endpoints
    spec = {
        "openapi": "3.0.0",
        "paths": {
            "/absences": {"post": {"description": "Create absence"}},
            "/employees": {"get": {"description": "List employees"}},
        },
    }

    mapping_text = """
    Mapped endpoint candidates:
    - POST /absences
    - POST /timeOffEntries
    """
    verification_text = """
    Further verification mentions:
    - GET /employees
    - PATCH /unknown
    """

    with tempfile.TemporaryDirectory() as tmp:
        spec_path = write_spec(tmp, spec, yaml=False)
        output_dir = tmp
        result = perform_endpoint_verification(
            api_spec_path=spec_path,
            mapping_text=mapping_text,
            verification_text=verification_text,
            output_directory=output_dir,
            collection_name="test_collection",
        )

        # Verified should contain POST /absences and GET /employees
        verified = {(e["method"], e["path"]) for e in result["verified"]}
        assert ("POST", "/absences") in verified
        assert ("GET", "/employees") in verified

        # Unverified should contain POST /timeOffEntries and PATCH /unknown
        unverified = {(e["method"], e["path"]) for e in result["unverified"]}
        assert ("POST", "/timeOffEntries") in unverified
        assert ("PATCH", "/unknown") in unverified

        # File should exist and contain list header or success message
        assert os.path.exists(result["file_path"])  # endpoints_to_research markdown
        with open(result["file_path"], "r", encoding="utf-8") as f:
            content = f.read()
        assert "Endpoints to (Re)Search" in content or "All claimed endpoints are found" in content

        # Research commands should be generated for unverified
        assert result["research_cmds"]
        assert any("query_api_specification" in c for c in result["research_cmds"])


