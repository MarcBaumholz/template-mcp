"""
Phase 3 MCP Tool: Orchestrator (End-to-End Kotlin Mapper Generator)

This tool combines Phase 3 generation steps into a single flow:
- Reads the Phase 2 mapping report
- Builds an enhanced prompt with coding rules and a minimal template
- Calls the LLM coder to generate a complete Kotlin implementation
- Saves the generated file and returns a concise result payload
"""

from pathlib import Path
from typing import Optional, Dict, Any
import logging
from datetime import datetime

from .phase3_models import Phase3Result

# Import the LLM client with fallback
try:
    from tools.shared_utilities.llm_client import get_llm_response
except Exception:  # pragma: no cover
    def get_llm_response(prompt: str, model: str = None, max_tokens: int = 3000, tool_name: str = "llm_client") -> str:
        return "// LLM unavailable. This is a placeholder."


logger = logging.getLogger(__name__)


DEFAULT_MIN_TEMPLATE = """
package com.flip.integrations

import io.micronaut.http.*
import io.micronaut.http.annotation.*
import io.micronaut.security.annotation.*
import io.micronaut.security.rules.SecurityRule
import jakarta.inject.Singleton
import org.slf4j.LoggerFactory
import io.micronaut.security.authentication.Authentication

/**
 * Verified Endpoint(s):
 * - METHOD PATH
 * Fields: <filled by generator>
 */
@Controller("/api/resource")
@Secured(SecurityRule.IS_AUTHENTICATED)
class ResourceController(private val service: ResourceService) {

    private val log = LoggerFactory.getLogger(ResourceController::class.java)

    @Get("/me")
    fun getForMe(auth: Authentication): HttpResponse<Any> {
        return try {
            val email = (auth.attributes["email"] as? String) ?: auth.name
            val result = service.getResourcesByEmail(email)
            HttpResponse.ok(result)
        } catch (ex: Throwable) {
            log.error("Controller error", ex)
            HttpResponse.serverError()
        }
    }
}

@Singleton
class ResourceService(private val facadeClient: FacadeClient /* TODO replace with real client */) {
    private val log = LoggerFactory.getLogger(ResourceService::class.java)

    fun getResourcesByEmail(email: String): Any {
        return try {
            val dto = facadeClient.fetchByEmail(email)
            Mapper.mapToTarget(dto)
        } catch (ex: Throwable) {
            log.error("Service error", ex)
            throw RuntimeException("Failed to fetch resources")
        }
    }
}

object Mapper {
    fun mapToTarget(source: SourceDTO): TargetDTO = TargetDTO(
        // --- START MAPPING ---
        // --- END MAPPING ---
    )
}

// Placeholder types
data class SourceDTO(val sample: String? = null)
data class TargetDTO(val sample: String? = null)

interface FacadeClient {
    fun fetchByEmail(email: String): SourceDTO
}
""".strip()


CODING_RULES = """
PHASE_3_CODING_RULES:
1) Architecture (single file ok): Controller (@Controller + @Secured), Service (@Singleton), Mapper (object/class)
2) Security & Logging: Controller secured with SecurityRule.IS_AUTHENTICATED; use SLF4J logger; log entry/errors
3) Error handling: try/catch in Controller and Service; return HttpResponse.serverError on failure in Controller
4) Null-safety & defaults: prefer safe calls (?.) and elvis (?:); avoid NPEs; use sensible defaults
5) Enum mapping: use when with else branch as fallback
6) Ground-truth discipline: In a header comment list verified METHOD+PATH and mapped fields. Do NOT invent fields
7) Unmapped: add TODO("reason and recommendation") where target cannot be derived
8) Output-only: return only Kotlin code (no markdown)
9) /me endpoint: resolve email from Authentication (attributes["email"] or name) and call service
""".strip()


def _build_prompt(mapping_info: str, template_text: str) -> str:
    return f"""
You are an expert Kotlin backend engineer. Generate a complete Controller/Service/Mapper implementation.

{CODING_RULES}

FIELD_MAPPING_ANALYSIS:
{mapping_info}

TEMPLATE_SCAFFOLD:
```kotlin
{template_text}
```

Instructions:
1) Replace placeholders and fill mapping blocks
2) Ensure imports and classes are consistent
3) Return only the complete Kotlin code file
""".strip()


def generate_mapper(
    mapping_report_path: str,
    output_directory: str = "outputs/phase3",
    company_name: str = "flip",
    project_name: str = "integrations",
    backend_name: str = "stackone",
    model: str = "qwen/qwen3-coder:free",
    max_tokens: int = 4000,
    template_text: Optional[str] = None,
) -> Phase3Result:
    """
    Generate full Kotlin Controller/Service/Mapper using the mapping analysis and coding rules.
    """
    try:
        mapping_info = Path(mapping_report_path).read_text(encoding="utf-8")
    except Exception as e:
        return Phase3Result(errors=[f"Failed to read mapping report: {e}"])

    scaffold = (template_text or DEFAULT_MIN_TEMPLATE)
    prompt = _build_prompt(mapping_info=mapping_info, template_text=scaffold)

    try:
        kotlin_code = get_llm_response(prompt, model=model, max_tokens=max_tokens)
        kotlin_code = kotlin_code.strip()
    except Exception as e:
        return Phase3Result(errors=[f"LLM generation failed: {e}"])

    out_dir = Path(output_directory)
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = out_dir / f"CompleteMapper_{ts}.kt"
    try:
        out_file.write_text(kotlin_code, encoding="utf-8")
    except Exception as e:
        return Phase3Result(errors=[f"Failed to save Kotlin file: {e}"])

    logger.info(f"Generated Kotlin mapper saved to: {out_file}")

    result = Phase3Result(
        final_mapper_code=kotlin_code,
    )
    return result


def register_tool() -> Dict[str, Any]:
    return {
        "name": "phase3_generate_mapper",
        "description": "End-to-end generator: produces Kotlin Controller/Service/Mapper from mapping analysis",
        "input_schema": {
            "type": "object",
            "properties": {
                "mapping_report_path": {"type": "string", "description": "Path to Phase 2 mapping report"},
                "output_directory": {"type": "string", "default": "outputs/phase3"},
                "company_name": {"type": "string", "default": "flip"},
                "project_name": {"type": "string", "default": "integrations"},
                "backend_name": {"type": "string", "default": "stackone"},
                "model": {"type": "string", "default": "qwen/qwen3-coder:free"},
                "max_tokens": {"type": "number", "default": 4000}
            },
            "required": ["mapping_report_path"]
        },
        "handler": generate_mapper
    }


