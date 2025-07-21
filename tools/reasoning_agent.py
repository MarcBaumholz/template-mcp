from typing import Dict, Any, Optional
from datetime import datetime
import logging
from pathlib import Path

# Assuming other tools are in the same directory or accessible via path
from .llm_client import get_llm_response
from .api_spec_getter import get_api_spec_with_direct_llm_query, CONTEXT_WINDOW_CHAR_LIMIT
from .rag_tools import upload_openapi_spec_to_rag, analyze_fields_with_rag_and_llm

logger = logging.getLogger(__name__)

# Define the consistent high-level goal for the agent
HIGH_LEVEL_GOAL = "Map source HR data fields to the target API specification to generate a complete and accurate schema mapping."

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
            f.write(f"### ✅ Completed by Reasoning Agent\n")
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

async def reasoning_agent(
    source_analysis_path: str,
    api_spec_path: str,
    output_directory: str,
    target_collection_name: Optional[str] = None
) -> str:
    """
    Orchestrates the entire schema mapping process from a high-level goal.

    This agent analyzes the inputs, decides whether to use direct analysis or a
    RAG-based approach, executes the necessary tools, and returns a final report.

    Args:
        source_analysis_path: Path to the markdown file with source field analysis.
        api_spec_path: Path to the target OpenAPI specification (.json or .yml).
        output_directory: The directory where the final report should be saved.
        target_collection_name: Optional. The RAG collection for the target API.
                                If not provided, one will be derived from the spec file name.
    """
    try:
        # --- 1. Establish Project Context ---
        output_dir = Path(output_directory)
        # A more robust way to find the project root might be needed,
        # but for now, we assume the output_directory is inside the project root.
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
        
        final_llm_response = ""
        strategy_log = ""

        if total_chars <= CONTEXT_WINDOW_CHAR_LIMIT:
            # --- Strategy 1: Direct Analysis ---
            strategy_log = "📝 Strategy: API spec is small enough. Using direct LLM analysis for maximum context."
            logger.info(strategy_log)
            
            prompt = get_api_spec_with_direct_llm_query(api_spec_path, source_analysis_path)
            if prompt.startswith("❌"):
                return prompt # Return error from the tool
                
            final_llm_response = get_llm_response(prompt, max_tokens=4096)

        else:
            # --- Strategy 2: RAG-based Analysis ---
            strategy_log = f"📚 Strategy: API spec is too large ({total_chars} chars). Using RAG-based analysis."
            logger.info(strategy_log)
            
            collection_name = target_collection_name or spec_path.stem.replace('.', '_').replace('-', '_')
            
            # Ensure the spec is uploaded to RAG
            upload_status = await upload_openapi_spec_to_rag(api_spec_path, collection_name)
            logger.info(f"RAG Upload Status for '{collection_name}': {upload_status}")
            
            # Extract field names from the analysis file to pass to the RAG tool
            source_fields = [line.split('|')[1].strip().replace('`', '') for line in analysis_content.splitlines() if '|' in line and 'Source Field' not in line and '---' not in line]
            source_fields = [field for field in source_fields if field]

            if not source_fields:
                 return "❌ Error: Could not extract any source fields from the analysis markdown file."

            final_llm_response = analyze_fields_with_rag_and_llm(
                fields_to_analyze=source_fields,
                collection_name=collection_name,
                context_topic=HIGH_LEVEL_GOAL,
                current_path=output_directory
            )

        # --- 4. Synthesize and Save Final Report ---
        report_content = f"""# End-to-End Mapping Agent Report

## 🎯 High-Level Goal
{HIGH_LEVEL_GOAL}

## 🧠 Reasoning Log
- **Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Strategy Chosen**: {strategy_log}
- **Source Analysis**: `{source_analysis_path}`
- **API Specification**: `{api_spec_path}`

---

## 📜 Project Context from PLANNING.md
```markdown
{planning_context}
```

---

## 🗺️ LLM Mapping Analysis

{final_llm_response}
"""
        report_path = save_report(output_directory, report_content, "mapping_agent_report")
        
        # --- 5. Update Progress Log ---
        if not report_path.startswith("❌"):
            update_task_md(project_root, HIGH_LEVEL_GOAL, report_path)
        
        return report_path

    except Exception as e:
        logger.error(f"Reasoning agent failed: {e}", exc_info=True)
        return f"❌ Error: Failed to generate report. {str(e)}"
