# Simple Kotlin Code Generation Prompt
import os



def generate_enhanced_prompt(mapping_info: str, kotlin_template: str, output_directory: str = "") -> str:
    """
    Generate a production-grade Kotlin code generation prompt for Phase 3.

    Args:
        mapping_info: Field mapping analysis results (from reasoning + verification)
        kotlin_template: Kotlin template file content
        output_directory: Optional directory to save the prompt as MD file. If empty, uses current directory.

    Returns:
        Prompt that instructs the LLM to generate layered Kotlin code (Controller → Service → Mapper)
        with security, logging, null-safety, and ground-truth verification discipline.
        Saves the prompt as an MD file and returns instructions for usage.
    """
    # Load template and example files from the same directory
    def _load_file(filename: str) -> str:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, filename)
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    # Load template and example (example is optional)
    KOTLIN_TEMPLATE = _load_file('template.kt')
    try:
        KOTLIN_EXAMPLE = _load_file('example.kt')
    except Exception:
        KOTLIN_EXAMPLE = "// No example available"
    
    prompt = f"""
Generate Kotlin mapping code based on field mapping analysis.
You are an experienced Kotlin developer who creates clean, secure, testable services with TDD mindset.
Fill the provided Kotlin template according to Phase 3 coding rules.

<PHASE_3_CODING_RULES>
1. Layered architecture (single file):
   - Controller (Micronaut): `@Controller`, `@Secured(SecurityRule.IS_AUTHENTICATED)`
   - Service (`@Singleton`): orchestrates client calls and uses the mapper
   - Mapper (object/class): pure field mappings and helpers (enum conversions, null-safety)
2. Security & Logging:
   - Annotate controller with `@Secured(SecurityRule.IS_AUTHENTICATED)`
   - Use SLF4J logger; log entry, success, and errors
3. Error handling:
   - Controller: try/catch → `HttpResponse.serverError()` with logged exception
   - Service: try/catch → log and rethrow `RuntimeException` with concise message
4. Null-safety & defaults:
   - Use Kotlin safe calls (`?.`), Elvis (`?:`), and `.orElse(null)` patterns
   - No NPEs; provide sensible defaults for optional fields
5. Enum mapping:
   - Implement `when` mapping with fallback branch
6. Ground-truth verification (no hallucinations):
   - In a header comment, list the verified endpoint method+path and request fields
   - Map only fields confirmed by the analysis (do not invent fields)
   - For missing targets, insert `TODO("Why missing and how to derive")`
7. Output-only:
   - Return ONLY the complete Kotlin code; no markdown, no explanations.
8. Authentication & Employee resolution (Absence Balances pattern):
   - Provide an authenticated `GET /api/__PLURAL_RESOURCE_PATH__/me` endpoint
   - Extract user email from `Authentication` (prefer `auth.attributes["email"]`, fallback `auth.name`)
   - Use `__EMPLOYEE_FACADE__` to resolve employeeId by email
   - Call service `get__PLURAL_RESOURCE__ByEmail(email)` which resolves employee and fetches balances from `FacadeClient`
</PHASE_3_CODING_RULES>

<WORKFLOW>
1. Read `<field_mapping_analysis>` and `<kotlin_template>`
2. Plan tests you would write (brief list) and keep mapping deterministic and testable
3. Replace all placeholders in template and fill `// --- START MAPPING ---` blocks
4. Ensure the code compiles conceptually (imports, classes, functions present)
5. Return the final Kotlin code only
</WORKFLOW>

**FIELD MAPPING ANALYSIS:**```
{mapping_info}
```

**TEMPLATE:**
```kotlin
{KOTLIN_TEMPLATE}
```
**CODING CHECKLIST:**
1. Replace template placeholders with concrete names/paths (company, project, controller path, service, mapper)
2. Controller: `@Controller("/api/...")`, `@Secured`, method returns `HttpResponse`
3. Service: logging, try/catch, call external client (keep placeholder `FacadeClient`) and delegate to mapper
4. Mapper: implement field mapping blocks, null-safety, enum conversions (use example as guide)
5. Add short header comment listing verified endpoint (METHOD + PATH) and mapped fields
6. Implement `/me` endpoint using `Authentication` → resolves email → service `.get__PLURAL_RESOURCE__ByEmail(email)`
7. For any unmapped field: `TODO("Why missing and recommendation")`
8. Return only Kotlin code

**EXAMPLE (optional):**
```kotlin
{KOTLIN_EXAMPLE}
```

**OUTPUT:**
Return only the complete Kotlin file. No markdown.
Comment unmapped or uncertain mappings with `TODO("reason + recommendation")`.
Note: `FacadeClient` and `__EMPLOYEE_FACADE__` are placeholders; import your generated StackOne client (e.g., `com.stackone.stackone_client_java.*`) and your employee facade implementation (e.g., `stackoneEmployeeFacade`).
"""
    
    # Save prompt to MD file
    from datetime import datetime
    from pathlib import Path
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Determine output directory
    if not output_directory:
        output_directory = "."
    
    output_dir = Path(output_directory)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create filename with timestamp
    filename = f"kotlin_code_generation_prompt_{timestamp}.md"
    output_path = output_dir / filename
    
    # Add instructions header to the prompt
    instructions_header = f"""# 🎯 Kotlin Code Generation Prompt - Generated {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 📋 INSTRUCTIONS FOR LLM USAGE

**IMPORTANT:** This file contains a comprehensive prompt for generating production-grade Kotlin mapping code.

### 🔄 NEXT STEPS:
1. **Copy the prompt below** (everything after this header)
2. **Apply it to your LLM system** (ChatGPT, Claude, etc.)
3. **Follow the Phase 3 coding rules** outlined in the prompt
4. **Generate the complete Kotlin code** as specified

### 📊 EXPECTED OUTPUT:
The LLM should return:
- Complete Kotlin file with Controller, Service, and Mapper layers
- Security annotations and logging
- Null-safety and error handling
- Ground-truth verification comments
- Only Kotlin code (no markdown, no explanations)

---

## 🧠 PROMPT TO APPLY:

"""
    
    # Combine instructions with the prompt
    full_content = instructions_header + prompt
    
    # Save to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(full_content)
    
    # Return success message with instructions
    return f"""✅ **Kotlin Code Generation Prompt Generated Successfully!**

📁 **File saved to:** `{output_path}`

## 🎯 **NEXT STEPS:**
1. **Open the generated file:** `{filename}`
2. **Copy the prompt** (everything after the instructions header)
3. **Apply it to your LLM system** (ChatGPT, Claude, etc.)
4. **Follow the Phase 3 coding rules** outlined in the prompt
5. **Generate the complete Kotlin code** as specified

## 📊 **Expected Output:**
The LLM should return:
- Complete Kotlin file with Controller, Service, and Mapper layers
- Security annotations and logging
- Null-safety and error handling
- Ground-truth verification comments
- Only Kotlin code (no markdown, no explanations)

**File contains:** {len(prompt)} characters of optimized prompt content"""
