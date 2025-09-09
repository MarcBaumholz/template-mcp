import os
from pathlib import Path


def write_dummy_mapping(tmpdir: Path) -> Path:
    p = tmpdir / "mapping_report.md"
    p.write_text("""
# Mapping Report (Dummy)

Direct Mappings:
- employee.id -> employeeId (string -> string)

""".strip(), encoding="utf-8")
    return p


def test_phase3_generate_mapper(tmp_path: Path):
    from tools.phase3_code_generation.phase3_orchestrator import generate_mapper
    mapping = write_dummy_mapping(tmp_path)
    res = generate_mapper(mapping_report_path=str(mapping), output_directory=str(tmp_path))
    # Should either have code or errors list
    assert res.final_mapper_code is not None or res.errors == []


def test_phase3_quality_suite_audit_only(tmp_path: Path):
    from tools.phase3_code_generation.phase3_quality_suite import run_quality_suite
    # prepare a minimal kotlin file
    kotlin = tmp_path / "K.kt"
    kotlin.write_text("""
package p
import io.micronaut.http.*
import io.micronaut.http.annotation.*
import io.micronaut.security.annotation.*
import io.micronaut.security.rules.SecurityRule
@Controller("/api")
@Secured(SecurityRule.IS_AUTHENTICATED)
class C { }
""".strip(), encoding="utf-8")
    mapping = write_dummy_mapping(tmp_path)
    report = run_quality_suite(str(kotlin), str(mapping), output_directory=str(tmp_path))
    assert "audit" in report


def test_phase3_selector(tmp_path: Path):
    from tools.phase3_code_generation.phase3_selector import select_best_candidate
    k1 = tmp_path / "A.kt"
    k2 = tmp_path / "B.kt"
    k1.write_text("class A {}", encoding="utf-8")
    k2.write_text("""
import io.micronaut.http.*
import io.micronaut.http.annotation.*
import io.micronaut.security.annotation.*
import io.micronaut.security.rules.SecurityRule
@Controller("/api")
@Secured(SecurityRule.IS_AUTHENTICATED)
class B {}
""".strip(), encoding="utf-8")
    mapping = write_dummy_mapping(tmp_path)
    result = select_best_candidate([str(k1), str(k2)], str(mapping))
    assert "best" in result


