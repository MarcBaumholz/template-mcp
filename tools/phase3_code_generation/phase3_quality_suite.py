"""
Phase 3 MCP Tool: Quality Suite (Audit + TDD tests)

Combines: Kotlin rule auditing and TDD test generation.
Outputs a JSON-like report with violations and writes a test file.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import json
import logging

from .phase3_models import TDDTestSuite

try:
    from tools.shared_utilities.llm_client import get_llm_response
except Exception:  # pragma: no cover
    def get_llm_response(prompt: str, model: str = None, max_tokens: int = 2000, tool_name: str = "llm_client") -> str:
        return "{}"

logger = logging.getLogger(__name__)


AUDIT_RULES = [
    "Controller annotated with @Controller and @Secured(SecurityRule.IS_AUTHENTICATED)",
    "Controller returns HttpResponse and handles errors with serverError()",
    "Service annotated with @Singleton and logs errors; rethrows with concise message",
    "Mapper uses null-safe operators and elvis defaults; no unsafe !!",
    "Enum with when has else fallback",
    "Header comment lists verified METHOD+PATH and mapped fields",
]


def _audit_prompt(kotlin_code: str) -> str:
    return f"""
You are a Kotlin reviewer. Audit this code against the following rules and return a JSON object:
Rules:
{json.dumps(AUDIT_RULES, indent=2)}

Code:
```kotlin
{kotlin_code}
```

Return JSON with fields: violations: [{{rule: string, finding: string, lineHint: string}}], suggestions: [string]
""".strip()


def audit_kotlin_code(kotlin_file_path: str, model: str = "qwen/qwen3-coder:free", max_tokens: int = 1500) -> Dict[str, Any]:
    code = Path(kotlin_file_path).read_text(encoding="utf-8")
    prompt = _audit_prompt(code)
    raw = get_llm_response(prompt, model=model, max_tokens=max_tokens)
    try:
        data = json.loads(raw)
    except Exception:
        data = {"violations": [], "suggestions": ["Auditor returned non-JSON output"]}
    data.setdefault("violations", [])
    data.setdefault("suggestions", [])
    data["rule_count"] = len(AUDIT_RULES)
    data["file"] = kotlin_file_path
    return data


def generate_tdd_from_report(
    mapping_report_path: str,
    output_directory: str = "outputs/phase3/tests",
    package_name: str = "com.flip.integrations.test",
    model: str = "qwen/qwen3-coder:free",
) -> TDDTestSuite:
    # Try full generator; fallback to minimal tests if unavailable
    try:
        from .phase3_tdd_generator import generate_tdd_tests
        return generate_tdd_tests(
            mapping_report_path=mapping_report_path,
            mapper_code_path=None,
            output_directory=output_directory,
            test_all_scenarios=True,
            package_name=package_name,
        )
    except Exception:
        # Minimal single test fallback
        setup = """
@TestInstance(TestInstance.Lifecycle.PER_CLASS)
class MapperTestSuiteFallback {
    @BeforeEach
    fun setup() { }
}
""".strip()
        tc = TDDTestSuite(
            test_class_name="MapperTestSuiteFallback",
            test_cases=[],
            setup_code=setup,
            teardown_code=None,
            full_test_file=f"package {package_name}\n\nimport org.junit.jupiter.api.*\n\n{setup}\n",
        )
        # Persist file
        out_dir = Path(output_directory)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "MapperTestSuiteFallback.kt").write_text(tc.full_test_file, encoding="utf-8")
        return tc


def run_quality_suite(
    kotlin_file_path: str,
    mapping_report_path: str,
    output_directory: str = "outputs/phase3/quality",
    model: str = "qwen/qwen3-coder:free",
) -> Dict[str, Any]:
    out_dir = Path(output_directory)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1) Audit
    audit = audit_kotlin_code(kotlin_file_path, model=model)

    # 2) TDD tests
    tests_dir = out_dir / "tests"
    suite = generate_tdd_from_report(mapping_report_path, output_directory=str(tests_dir), model=model)

    # Save audit report
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = out_dir / f"quality_report_{ts}.json"
    payload = {
        "audit": audit,
        "test_file": str(tests_dir),
        "test_count": len(suite.test_cases),
    }
    report_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    logger.info(f"Quality report saved: {report_file}")
    return payload


def register_tool():
    return {
        "name": "phase3_quality_suite",
        "description": "Audit Kotlin code against Phase 3 rules and generate TDD tests",
        "input_schema": {
            "type": "object",
            "properties": {
                "kotlin_file_path": {"type": "string"},
                "mapping_report_path": {"type": "string"},
                "output_directory": {"type": "string", "default": "outputs/phase3/quality"},
                "model": {"type": "string", "default": "qwen/qwen3-coder:free"}
            },
            "required": ["kotlin_file_path", "mapping_report_path"]
        },
        "handler": run_quality_suite
    }


