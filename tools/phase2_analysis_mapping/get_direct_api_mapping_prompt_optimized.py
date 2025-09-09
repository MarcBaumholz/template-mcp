"""
Optimized RAG Tools for Direct API Mapping Prompt Generation
Enhanced with research-based prompt engineering strategies from 2024 papers
"""

import os
from pathlib import Path
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Set a reasonable character limit to avoid overflowing the context window
# 500,000 chars is roughly 100k-125k tokens, which fits in most modern models with large context windows.
CONTEXT_WINDOW_CHAR_LIMIT = 800000

def get_api_spec_with_direct_llm_query_optimized(
    api_spec_path: str, 
    analysis_md_path: str,
    output_directory: str = ""
) -> str:
    """
    Crafts a high-quality, research-optimized prompt for an LLM to directly map fields by reading
    an API spec and an analysis file, if they fit within the context window.

    This tool incorporates the latest prompt engineering strategies from 2024 research:
    - Chain-of-Thought reasoning patterns
    - Few-shot examples with structured reasoning
    - Step-by-step decomposition
    - Reasoning pattern selection
    - Cumulative reasoning approach

    Args:
        api_spec_path: The full path to the OpenAPI specification file.
        analysis_md_path: The full path to the markdown analysis file containing
                          source fields, synonyms, descriptions, etc.
        output_directory: Optional directory to save the prompt as MD file. If empty, uses current directory.

    Returns:
        A detailed, structured prompt for the LLM saved as MD file, or an error message
        if the files are too large or not found.
    """
    try:
        # --- 1. Read the input files ---
        spec_path = Path(api_spec_path)
        analysis_path = Path(analysis_md_path)

        logger.info(f"Reading API spec from: {api_spec_path}")
        logger.info(f"Reading analysis from: {analysis_md_path}")

        if not spec_path.exists():
            logger.error(f"API Specification file not found at '{api_spec_path}'")
            return f"❌ Error: API Specification file not found at '{api_spec_path}'."
        if not analysis_path.exists():
            logger.error(f"Analysis markdown file not found at '{analysis_md_path}'")
            return f"❌ Error: Analysis markdown file not found at '{analysis_md_path}'."

        logger.info(f"Reading files...")
        api_spec_content = spec_path.read_text(encoding='utf-8')
        analysis_content = analysis_path.read_text(encoding='utf-8')
        logger.info(f"Successfully read {len(api_spec_content)} chars from API spec and {len(analysis_content)} chars from analysis")

        # --- 2. Check if the content fits in the context window ---
        total_chars = len(api_spec_content) + len(analysis_content)
        logger.info(f"Total content size: {total_chars} chars (limit: {CONTEXT_WINDOW_CHAR_LIMIT} chars)")
        
        if total_chars > CONTEXT_WINDOW_CHAR_LIMIT:
            logger.warning(f"Content size {total_chars} exceeds limit {CONTEXT_WINDOW_CHAR_LIMIT}")
            return (f"❌ Error: The combined size of the API spec and analysis ({total_chars} chars) "
                    f"exceeds the context window limit of {CONTEXT_WINDOW_CHAR_LIMIT} chars. "
                    f"Please use the RAG-based 'query_api_specification' tool instead.")
        
        logger.info(f"Content size within limits, proceeding with optimized prompt generation")

        # --- 3. Craft the research-optimized prompt ---
        prompt = f"""
# 🧠 Advanced API Schema Mapping with Structured Reasoning

You are an expert AI system integrator specializing in API field mapping. Your task is to analyze the provided OpenAPI specification and map source fields to the most appropriate destination fields using advanced reasoning patterns.

## 🎯 Task Overview

This is a **direct-analysis task** that requires you to:
1. **Decompose** the complex mapping problem into manageable subproblems
2. **Reason** through each mapping decision step-by-step
3. **Verify** your reasoning at each step
4. **Synthesize** a comprehensive mapping solution

---

## 📊 Source Field Analysis

Here is the analysis of the source data containing fields that need to be mapped, along with their descriptions, data types, and possible synonyms:

```markdown
{analysis_content}
```

---

## 📄 Complete OpenAPI Specification

Here is the complete OpenAPI specification for the destination system. Analyze it systematically to find the correct endpoints and schema properties:

```json
{api_spec_content}
```

---

## 🔍 Structured Reasoning Process

Follow this **cumulative reasoning approach** with three distinct roles:

### **Role 1: Proposer** - Decompose and Suggest
Break down the mapping task into logical subproblems:

1. **Endpoint Identification**: Scan the API spec to identify the most relevant endpoint(s) for the source data context
2. **Schema Analysis**: Locate the request body schema for the identified endpoint(s)
3. **Field Mapping**: Map each source field to the most appropriate destination field
4. **Validation**: Verify that all mappings are logically sound and complete

### **Role 2: Verifier** - Evaluate and Refine
For each proposed mapping, verify:

- **Semantic Alignment**: Does the destination field represent the same concept as the source field?
- **Data Type Compatibility**: Are the data types compatible or can they be converted?
- **Business Logic**: Does the mapping make sense in the business context?
- **Completeness**: Are all source fields accounted for?

### **Role 3: Reporter** - Synthesize and Document
Compile the verified mappings into a comprehensive report.

---

## 🧩 Step-by-Step Mapping Process

### **Step 1: Endpoint Discovery**
**Let's think step by step:**

1. **Analyze the source context** - What type of data are we working with? (e.g., employee data, absence records, time tracking)
2. **Scan the API specification** - Look for endpoints that handle this type of data
3. **Identify the primary endpoint** - Which endpoint is most relevant for creating/updating this data?
4. **Document your reasoning** - Explain why you selected this endpoint

**Example reasoning pattern:**
```
Source context: "Absence Management/time offs"
Analysis: This appears to be employee absence/time-off data
API scan: Found endpoints like POST /absences, PUT /timeOffRequests, POST /leaveRequests
Selection: POST /absences (most direct match for absence data)
Reasoning: The endpoint name directly corresponds to the source context
```

### **Step 2: Schema Analysis**
**Let's think step by step:**

1. **Locate the request body schema** - Find the schema under `requestBody.content['application/json'].schema`
2. **Identify available fields** - List all properties in the destination schema
3. **Understand field types** - Note the data types and constraints for each field
4. **Document schema structure** - Create a clear overview of available destination fields

### **Step 3: Field Mapping with Reasoning Patterns**

For each source field, apply this **structured reasoning pattern**:

#### **Pattern A: Direct Match Analysis**
```
Source Field: [field_name]
Analysis: Looking for exact or near-exact matches
Reasoning: [step-by-step analysis]
Decision: [Direct Match/Semantic Match/No Match]
Justification: [detailed explanation]
```

#### **Pattern B: Semantic Match Analysis**
```
Source Field: [field_name]
Analysis: No direct match found, searching for semantic equivalents
Reasoning: [conceptual analysis]
Decision: [best semantic match or no match]
Justification: [why this mapping makes sense]
```

#### **Pattern C: No Match Analysis**
```
Source Field: [field_name]
Analysis: No suitable match found in the API specification
Reasoning: [why no match exists]
Decision: No Match
Recommendation: [suggested approach or TODO]
```

### **Step 4: Verification and Quality Assurance**

**Let's think step by step:**

1. **Review all mappings** - Ensure each source field has been properly analyzed
2. **Check for completeness** - Verify no source fields were missed
3. **Validate data types** - Confirm type compatibility or conversion requirements
4. **Test logical consistency** - Ensure the overall mapping makes business sense

---

## 📋 Final Output Format

Produce a comprehensive mapping report using this structure:

### **🔍 Endpoint Analysis**
**Selected Endpoint:** `[Your Identified Endpoint]`
**Reasoning:** [Why this endpoint was selected]

### **📊 Schema Overview**
**Available Destination Fields:** [List of all available fields in the schema]
**Key Field Types:** [Summary of data types and constraints]

### **🔄 Field Mapping Results**

| Source Field | Destination Field | Match Type | Confidence | Reasoning | Data Type Notes |
|--------------|-------------------|------------|------------|-----------|-----------------|
| `[field_1]` | `[dest_field_1]` | `Direct Match` | `High` | `Exact name match with same semantic meaning` | `string → string` |
| `[field_2]` | `[dest_field_2]` | `Semantic Match` | `Medium` | `Maps to 'X' because it represents the same business concept` | `number → string (conversion needed)` |
| `[field_3]` | `(No Match)` | `No Match` | `N/A` | `TODO: No equivalent found - consider custom field or business logic` | `N/A` |

### **⚠️ Mapping Notes and Recommendations**

**Data Type Conversions Required:**
- [List any necessary type conversions]

**Business Logic Considerations:**
- [Any special business rules or transformations needed]

**Missing Fields:**
- [Fields that couldn't be mapped and recommendations]

**Validation Rules:**
- [Any validation requirements for the mapped fields]

---

## 🎯 Success Criteria

Your mapping will be considered successful if:
1. **All source fields are analyzed** - No field is left unexamined
2. **Reasoning is explicit** - Each decision is clearly justified
3. **Mappings are accurate** - Only fields that exist in the API spec are mapped
4. **Business logic is sound** - The overall mapping makes business sense
5. **Documentation is complete** - All decisions and recommendations are clearly documented

**Remember:** Only map to fields that actually exist in the API specification. If a field doesn't exist, mark it as "No Match" and provide a TODO recommendation for how to handle it.

Let's begin the structured reasoning process...
"""
        logger.info(f"Successfully crafted an optimized direct API spec query prompt of {len(prompt)} characters.")
        
        # --- 4. Save prompt to MD file ---
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Determine output directory
        if not output_directory:
            output_directory = "."
        
        output_dir = Path(output_directory)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create filename with timestamp
        filename = f"direct_api_mapping_prompt_{timestamp}.md"
        output_path = output_dir / filename
        
        # Add instructions header to the prompt
        instructions_header = f"""# 🎯 Direct API Mapping Prompt - Generated {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 📋 INSTRUCTIONS FOR LLM USAGE

**IMPORTANT:** This file contains a comprehensive prompt for direct API field mapping analysis. 

### 🔄 NEXT STEPS:
1. **Copy the prompt below** (everything after this header)
2. **Apply it to your LLM system** (ChatGPT, Claude, etc.)
3. **Follow the structured reasoning process** outlined in the prompt
4. **Generate the mapping analysis** as specified in the output format

### 📊 EXPECTED OUTPUT:
The LLM should return a comprehensive mapping report with:
- Endpoint analysis and selection
- Schema overview
- Field mapping results table
- Mapping notes and recommendations

---

## 🧠 PROMPT TO APPLY:

"""
        
        # Combine instructions with the prompt
        full_content = instructions_header + prompt
        
        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_content)
        
        logger.info(f"Prompt saved to: {output_path}")
        
        # Return success message with instructions
        return f"""✅ **Direct API Mapping Prompt Generated Successfully!**

📁 **File saved to:** `{output_path}`

## 🎯 **NEXT STEPS:**
1. **Open the generated file:** `{filename}`
2. **Copy the prompt** (everything after the instructions header)
3. **Apply it to your LLM system** (ChatGPT, Claude, etc.)
4. **Follow the structured reasoning process** outlined in the prompt
5. **Generate the mapping analysis** as specified

## 📊 **Expected Output:**
The LLM should return a comprehensive mapping report with:
- Endpoint analysis and selection
- Schema overview  
- Field mapping results table
- Mapping notes and recommendations

**File contains:** {len(prompt)} characters of optimized prompt content"""

    except FileNotFoundError as e:
        logger.error(f"File not found error: {e}")
        return f"❌ File not found: {str(e)}"
    except PermissionError as e:
        logger.error(f"Permission error reading file: {e}")
        return f"❌ Permission denied reading file: {str(e)}"
    except UnicodeDecodeError as e:
        logger.error(f"Unicode decode error: {e}")
        return f"❌ Unicode decode error: {str(e)}"
    except Exception as e:
        logger.error(f"Failed to generate optimized direct API query prompt: {e}")
        return f"❌ Failed to generate prompt: {str(e)}"


def get_direct_api_mapping_prompt_optimized(api_spec_path: str, analysis_md_path: str, output_directory: str = "") -> str:
    """Backward compatibility wrapper. Calls get_api_spec_with_direct_llm_query_optimized."""
    return get_api_spec_with_direct_llm_query_optimized(api_spec_path, analysis_md_path, output_directory)
