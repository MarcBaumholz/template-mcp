from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
from pathlib import Path
import json
import os

# Assuming other tools are in the same directory or accessible via path
from .llm_client import get_llm_response
from .api_spec_getter import get_api_spec_with_direct_llm_query, CONTEXT_WINDOW_CHAR_LIMIT
from .rag_tools import upload_openapi_spec_to_rag, analyze_fields_with_rag_and_llm
from .rag_helper import RAGHelper

logger = logging.getLogger(__name__)

# Define the consistent high-level goal for the agent
HIGH_LEVEL_GOAL = "Map source HR data fields to the target API specification to generate a complete and accurate schema mapping with verification and creative solutions for unmapped fields."

def read_project_file(project_root: Path, filename: str) -> str:
    """Reads a project context file (e.g., PLANNING.md) if it exists."""
    file_path = project_root / filename
    if file_path.exists():
        return file_path.read_text(encoding='utf-8')
    return f"{filename} not found."

def update_task_md(project_root: Path, goal: str, report_path: str):
    """Appends a record of the completed task to TASK.MD."""
    task_md_path = project_root / "TASK.MD"
    try:
        with open(task_md_path, 'a', encoding='utf-8') as f:
            f.write("\n\n---\n")
            f.write(f"### ✅ Completed by Enhanced Reasoning Agent\n")
            f.write(f"- **Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"- **Goal**: {goal}\n")
            f.write(f"- **Output**: See report at `{report_path}`\n")
        logger.info(f"Successfully updated {task_md_path}")
    except Exception as e:
        logger.error(f"Failed to update {task_md_path}: {e}")

def save_report(directory: str, content: str, prefix: str) -> str:
    """Saves a report to a file with a timestamp and returns the path."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"{prefix}_{timestamp}.md"
    report_path = Path(directory) / report_filename
    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Report saved to {report_path}")
        return str(report_path)
    except Exception as e:
        logger.error(f"Failed to save report to {report_path}: {e}")
        return f"❌ Error: Failed to save report to {report_path}. {str(e)}"

async def extract_unmapped_fields(mapping_content: str) -> List[str]:
    """Extract unmapped fields from the mapping report using LLM."""
    extraction_prompt = f"""
    Analyze the following mapping report and extract all fields that are marked as "unmapped", 
    "no direct match", "missing", or similar indicators.
    
    Return ONLY a JSON array of field names, nothing else.
    
    Mapping Report:
    {mapping_content}
    """
    
    try:
        response = get_llm_response(extraction_prompt, max_tokens=1000)
        # Try to parse as JSON
        unmapped_fields = json.loads(response.strip())
        return unmapped_fields if isinstance(unmapped_fields, list) else []
    except:
        # Fallback: simple text parsing
        lines = mapping_content.lower().split('\n')
        unmapped_fields = []
        for line in lines:
            if any(keyword in line for keyword in ['unmapped', 'no match', 'missing', 'not found']):
                # Extract field name from line
                if ':' in line:
                    field = line.split(':')[0].strip('- *')
                    unmapped_fields.append(field)
        return unmapped_fields

async def generate_creative_solutions(
    unmapped_fields: List[str],
    api_spec_content: str,
    collection_name: str
) -> Dict[str, str]:
    """Generate creative solutions for unmapped fields using RAG and LLM."""
    if not unmapped_fields:
        return {}
    
    solutions = {}
    rag_helper = RAGHelper()
    
    for field in unmapped_fields:
        # Search for similar fields in API spec using RAG
        try:
            search_query = f"field property attribute {field} similar data type"
            rag_results = await rag_helper.query_collection(
                collection_name=collection_name,
                query=search_query,
                limit=3
            )
            
            rag_context = "\n".join([f"- {result}" for result in rag_results]) if rag_results else "No similar fields found in API specification."
        except Exception as e:
            rag_context = f"Error searching API spec: {str(e)}"
        
        # Generate creative solution
        solution_prompt = f"""
        Field "{field}" could not be directly mapped to the API specification.
        
        RAG Search Results:
        {rag_context}
        
        API Specification Context (first 2000 chars):
        {api_spec_content[:2000]}...
        
        Generate creative solutions for how this field could be:
        1. Mapped to existing API fields (even if transformation is needed)
        2. Derived from multiple API fields
        3. Implemented as a calculated field
        4. Handled through default values or constants
        5. Transformed using business logic
        
        Provide specific, actionable suggestions with code examples where possible.
        Keep response concise but practical.
        """
        
        try:
            solution = get_llm_response(solution_prompt, max_tokens=1500)
            solutions[field] = solution
        except Exception as e:
            solutions[field] = f"Error generating solution: {str(e)}"
    
    return solutions

def format_unmapped_fields(unmapped_fields: List[str]) -> str:
    """Format unmapped fields for display."""
    if not unmapped_fields:
        return "✅ **No unmapped fields detected - Great job!**"
    
    formatted = "🔴 **Fields requiring attention:**\n\n"
    for i, field in enumerate(unmapped_fields, 1):
        formatted += f"{i}. `{field}`\n"
    
    return formatted

def format_creative_solutions(solutions: Dict[str, str]) -> str:
    """Format creative solutions for display."""
    if not solutions:
        return "✅ **No creative solutions needed - all fields are mapped!**"
    
    formatted = ""
    for field, solution in solutions.items():
        formatted += f"### 💡 Solutions for `{field}`\n\n"
        formatted += f"{solution}\n\n"
        formatted += "---\n\n"
    
    return formatted

async def reasoning_agent(
    source_analysis_path: str,
    api_spec_path: str,
    output_directory: str,
    target_collection_name: Optional[str] = None
) -> str:
    """
    Enhanced orchestrator that combines schema mapping with proof tool functionality.
    
    This agent:
    1. Analyzes inputs and chooses optimal strategy (direct vs RAG)
    2. Executes mapping analysis
    3. Identifies unmapped fields
    4. Generates creative solutions for unmapped fields
    5. Provides comprehensive verification and implementation guidance
    
    Args:
        source_analysis_path: Path to the markdown file with source field analysis.
        api_spec_path: Path to the target OpenAPI specification (.json or .yml).
        output_directory: The directory where the final report should be saved.
        target_collection_name: Optional. The RAG collection for the target API.
    """
    try:
        # --- 1. Establish Project Context ---
        output_dir = Path(output_directory)
        project_root = output_dir if output_dir.is_dir() else output_dir.parent
        
        planning_context = read_project_file(project_root, "PLANNING.md")

        # --- 2. Validate Inputs ---
        source_path = Path(source_analysis_path)
        spec_path = Path(api_spec_path)
        
        if not source_path.exists():
            return f"❌ Error: Source analysis file not found at '{source_analysis_path}'."
        if not spec_path.exists():
            return f"❌ Error: API specification file not found at '{api_spec_path}'."
        if not Path(output_directory).is_dir():
            return f"❌ Error: Output directory '{output_directory}' not found."

        analysis_content = source_path.read_text(encoding='utf-8')
        api_spec_content = spec_path.read_text(encoding='utf-8')
        
        # --- 3. Reason about the best strategy (Direct vs. RAG) ---
        total_chars = len(analysis_content) + len(api_spec_content)
        
        mapping_response = ""
        strategy_log = ""
        collection_name = target_collection_name or spec_path.stem.replace('.', '_').replace('-', '_')

        if total_chars <= CONTEXT_WINDOW_CHAR_LIMIT:
            # --- Strategy 1: Direct Analysis ---
            strategy_log = "📝 Strategy: API spec is small enough. Using direct LLM analysis for maximum context."
            logger.info(strategy_log)
            
            prompt = get_api_spec_with_direct_llm_query(api_spec_path, source_analysis_path)
            if prompt.startswith("❌"):
                return prompt # Return error from the tool
                
            mapping_response = get_llm_response(prompt, max_tokens=4096)

        else:
            # --- Strategy 2: RAG-based Analysis ---
            strategy_log = f"📚 Strategy: API spec is too large ({total_chars} chars). Using RAG-based analysis."
            logger.info(strategy_log)
            
            # Ensure the spec is uploaded to RAG
            upload_status = await upload_openapi_spec_to_rag(api_spec_path, collection_name)
            logger.info(f"RAG Upload Status for '{collection_name}': {upload_status}")
            
            # Extract field names from the analysis file to pass to the RAG tool
            source_fields = [line.split('|')[1].strip().replace('`', '') for line in analysis_content.splitlines() if '|' in line and 'Source Field' not in line and '---' not in line]
            source_fields = [field for field in source_fields if field]

            if not source_fields:
                 return "❌ Error: Could not extract any source fields from the analysis markdown file."

            mapping_response = analyze_fields_with_rag_and_llm(
                fields_to_analyze=source_fields,
                collection_name=collection_name,
                context_topic=HIGH_LEVEL_GOAL,
                current_path=output_directory
            )

        # --- 4. PROOF TOOL INTEGRATION: Extract unmapped fields and generate solutions ---
        logger.info("🔍 Analyzing unmapped fields and generating creative solutions...")
        
        unmapped_fields = await extract_unmapped_fields(mapping_response)
        logger.info(f"Found {len(unmapped_fields)} unmapped fields: {unmapped_fields}")
        
        creative_solutions = await generate_creative_solutions(
            unmapped_fields, api_spec_content, collection_name
        )
        
        # --- 5. Generate Comprehensive Report with Proof Tool Integration ---
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        report_content = f"""# 🚀 Enhanced Reasoning Agent Report with Proof Tool Integration

## 🎯 High-Level Goal
{HIGH_LEVEL_GOAL}

## 🧠 Reasoning & Strategy Log
- **Timestamp**: {timestamp}
- **Strategy Chosen**: {strategy_log}
- **Source Analysis**: `{source_analysis_path}`
- **API Specification**: `{api_spec_path}`
- **RAG Collection**: `{collection_name}`

---

## 📜 Project Context from PLANNING.md
```markdown
{planning_context}
```

---

## 🗺️ Initial Mapping Analysis

{mapping_response}

---

## 🔍 PROOF TOOL ANALYSIS - Verification & Creative Solutions

### 📊 Unmapped Fields Detection

{format_unmapped_fields(unmapped_fields)}

### 💡 Creative Solutions for Unmapped Fields

{format_creative_solutions(creative_solutions)}

---

## 🎯 COMPREHENSIVE IMPLEMENTATION GUIDE

### ✅ Verification Checklist
1. **Double-check all mapped fields** for technical correctness
2. **Verify data type compatibility** between source and target
3. **Check for logical inconsistencies** in the mapping logic
4. **Ensure business context alignment** with requirements

### 🔧 Implementation Tasks
1. **Review mapped fields** and implement direct mappings
2. **Apply creative solutions** for unmapped fields
3. **Add data transformation logic** where needed
4. **Implement validation rules** for data integrity
5. **Create default value strategies** for missing fields

### 🧪 Testing Strategy
1. **Unit tests** for each mapping function
2. **Integration tests** with sample data
3. **Edge case handling** for null/missing values
4. **Performance testing** for large datasets

---

## 📁 Next Steps

1. **Review this comprehensive analysis** and validate all suggestions
2. **Implement the direct field mappings** using the provided mapping table
3. **Apply creative solutions** for unmapped fields based on the suggestions above
4. **Create transformation functions** for complex mappings
5. **Test thoroughly** with real data samples
6. **Document any assumptions** or limitations discovered

---

## 🔄 Continuous Improvement

- **Monitor mapping accuracy** in production
- **Collect feedback** on missing or incorrect mappings  
- **Update creative solutions** based on real-world usage
- **Refine transformation logic** as business requirements evolve

---

*Report generated by Enhanced Reasoning Agent with integrated Proof Tool functionality*
"""
        
        report_path = save_report(output_directory, report_content, "enhanced_reasoning_agent_report")
        
        # --- 6. Update Progress Log ---
        if not report_path.startswith("❌"):
            update_task_md(project_root, HIGH_LEVEL_GOAL, report_path)
        
        return report_path

    except Exception as e:
        logger.error(f"Enhanced reasoning agent failed: {e}", exc_info=True)
        return f"❌ Error: Failed to generate enhanced report. {str(e)}"
