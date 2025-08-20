# Rules for the API Integration Agent (with MCP tool Tempalte MCP)

IMPORTANT: Always start by generating a Planning.mD file and a Tasks.md file based on this rules file before using the tools. Always use the information here as context and retain it in memory. Use all the detailed information here in the rules file to create the planning and task files.

## 1. 🎯 Overall Goal

The main goal is to automate the creation of API integrations between different HR software systems. This includes understanding the source and target APIs, mapping data fields, and generating functional connector code in languages such as Python or Kotlin.

## 2. 📝 Core Problem & Context

- **The Challenge:** Manually integrating thousands of HR systems is slow, expensive, and error-prone due to different API specifications (OpenAPI, REST, etc.), data models, and authentication methods.
- **The Approach:** We use a cognitive agent system inspired by the BDI (Belief-Desire-Intention) model. The agent breaks down the complex integration task into a series of smaller, manageable steps, using specialized MCP tools. This approach addresses the limitations of LLMs, such as hallucinations and context window size, by providing focused, relevant information at each stage.

## 3. 🏛️ Agent Architecture & Workflow

The agent follows a structured, multi-stage pipeline. Each step uses specific MCP tools and generates an artifact that serves as input for the next step. The agent uses cursor commands and additional information to create and manage a `PLANNING.md` file.

**Important:** All file paths must be specified as full, absolute paths (e.g., `/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/neo4jrag/clean.json`).

#### PHASE 1: Gathering Information about the Data

### Step 1: Building the Knowledge Base
- **High-Level Action:** Upload API specifications with the full absolute path and store them in a searchable RAG knowledge base
- **Output:** A RAG-enabled knowledge base with structured API information
- **MCP Tools Used:**
- `upload_api_specification`: Primary tool for uploading OpenAPI specification files (.json or .yml) with the full absolute file path. The tool processes the file, splits it into logical blocks, generates vector embeddings, and stores everything in the PostgreSQL database.
- `list_available_api_specs`: Checks existing knowledge bases to avoid duplicates
- `delete_api_specification`: Removes outdated API specifications before uploading new versions

### Step 2: Identify relevant JSON fields and perform detailed field analysis

  Use the tool: analyze_json_fields_with_rag

  High-level action:
  Simplified, combined analysis of all relevant JSON fields with semantic extension

  Output:
  Structured analysis with:
  Identified relevant JSON fields, often contained in the body, that need to be mapped
  Semantic descriptions for each field
  Synonyms and alternative names
  Possible data types
  Business context and usage
  MCP tools used:
  analyze_json_fields_with_rag: ONLY TOOL for this step

  Tool usage:
  analyze_json_fields_with_rag(
  webhook_json_path="/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/neo4jrag/clean.json",
  current_directory="/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/neo4jrag",
  Collection name = "flip_api_v2"
  )

  What the tool does:
  JSON field extraction: Systematic identification of all relevant fields
  Semantic analysis: LLM-based description of each field
  Synonym generation: Alternative names for better mapping
  Data type detection: Possible data types for each field
  Business context: Classification within the business context
  Structured output: JSON + Markdown reports

  Output files:
  clean_enhanced_analysis_YYYYMMDD_HHMMSS.json - Structured data
  clean_enhanced_analysis_YYYYMMDD_HHMMSS.md - Readable report

Status: We now have an analysis of the existing endpoints and relevant fields.

#### PHASE 2: Find the correct endpoints in the 3rd-party API spec. Use query_api_spec to search all relevant fields for their matches, and also use enhanced_rag_anaylsis to find even more details and validate the fields.

### Step 3: Semantic Field Search and Mapping (Advanced)
- **High-Level Action:** Intensive search for the best matches for each source field using multiple query strategies and advanced context analysis.
- Mapping the 3rd-party openAPI spec to find all relevant fields, step by step.

Do not query the flip API, query the other API spec.
- **Output:** Detailed mapping suggestions with confidence values and comprehensive justifications. The results of both tools are displayed at the end. Finally, write the results into a mappings.md file with the top 3 matches found per field, along with the confidence score.


For step 4 always use all 3 methods of query the api query it,get_direct_api_mapping_prompt and enhanced rag analysis

 **MCP tools used:**

**4.1 Intensive Query Strategy:**
- `query_api_specification`:
First, the 3rd-party API specification is queried using the high-level concept, so that all parameters of the most suitable endpoint are indexed, which initially leads to the mapping.

Afterward, queries are systematically executed using various query combinations:
- Exact field name search
- Semantic similarity search
- Context-based search using information from step 3
- Synonym and variant search
- Data type-specific search
- Search based on the description

- 'enhanced_rag_analysis':
Also use this RAG tool to generate better retrieval. 

   ### 4.0 Endpoint Scoping BEFORE Field Queries
1. **First** perform an endpoint inventory:
• Search the API spec (RAG + Grep) for path parts
"timeOff", "absence", "leave", "request", "submit".
• Filter: only endpoints with HTTP method == POST / PUT / PATCH
(creation or submit).
• Return a short list (path, method, summary)
and select the most suitable create/submit endpoint
as PRIMARY_ENDPOINT.
2. Then use PRIMARY_ENDPOINT for all detail queries
(parameters, body schema, field search).
→ This prevents GET list endpoints from being incorrectly mapped.

### 4.x Query Strategies
– Include at least one **method filter** in every RAG query,
e.g., "POST time off", "POST /timeOffEntries".
– Additionally, use regex grep (exact text) against the spec file,
e.g., `\"/timeOff.*\": \\{\\s+\"post\"`.
- **Execution:** For each source field, at least 5-10 different query variants are executed to ensure all possible matches are found. Once you have found an endpoint, run query_api_specification and a grep sarch in parallel, grep_search on the JSON/YAML file (exact text) 

  EXAMPLE:
⚙️ Endpoint Discovery (MANDATORY)
1. Run in parallel:
• query_api_specification(query="POST time off OR submit absence", limit=10)
• grep_search("\"\s*/[^\"}]*timeOff[^\"]*\"\\s*:\\s*\\{\\s*\"post\"", common_v1_*.json)
2. Select the best POST endpoint; abort if none found.
3. Only after PRIMARY_ENDPOINT is fixed, proceed with field mapping.

**4.2 Advanced Context Analysis:**
- `get_direct_api_mapping_prompt`: Improve accuracy by re-searching.

Afterward, improve the mapping results with this MCP tool, focus on the API endpoints of the task to be solved, and generate a better mapping. Use the MCP tool to get the prompt and then use cursor to execute the prompt.

1. **LLM makes MCP tool call:** The LLM executes the `get_direct_api_mapping_prompt` call.
2. **Prompt return:** The tool returns a specialized, context-rich LLM prompt, with API spec and searchable parameters in the context window.
3. **LLM execution:** The cursor LLM takes the returned prompt and executes it to generate advanced mapping analyses, finding the top 3 best-fitting endpoints per field.
4. **More Context:** The returned prompt contains additional context information from the RAG database and previous analysis steps.
5. Really let the cursor use this prompt and work with the context of the prompt for the enhanced analysis.

### Step 5: Cognitive Review and Refinement (Enhanced)
- **High-Level Action:** Intelligent evaluation and validation by reasoning agent with LLM post-processing.
- **Output:** Validated and refined mapping table with quality assessment. I also search for missing fields again and come up with ideas for how to represent Flip's field.

- **MCP Tools Used:**
  **5.1 Reasoning Agent Analysis:**
- Reasoning agent: Performs the cognitive review:
- Checks the completeness and correctness of the mappings
- Identifies missing required fields and potential mapping errors
- Evaluates the quality of the confidence values and justifications
- Suggests improvements or alternative mappings
- Finds possibilities for fields not yet mapped

**5.2 LLM Post-Processing:**
- Reasoning Result Processing:** The reasoning agent tool returns a structured result
- LLM Analysis:** The LLM takes the reasoning result and performs a detailed analysis:
- Interprets the reasoning agent's recommendations
- Apply business logic and domain knowledge
- Creates a final, validated mapping table
- Adds additional context and explanations


IMPORTANT: before you continue with step 6 you show the human all fields and their top 3 matches with full paths in the chat, => integrate that in the plan, only write code if you get the approval from the human 

### Step 6: Kotlin Mapper Code Generation
- **High-Level Action:** Generate functional Kotlin code based on the validated mappings
Generate the Kotlin code based on the template, returning only the template.kt Kotlin file as output, and use the MCP tool again to generate the prompt, which is then executed by cursor. Fill the template with the endpoint/schema path from the 3rd-party API spec; the mapping always happens from Flip to the 3rd-party API.

- **Output:** Executable Kotlin code with unit tests
- **MCP Tools Used:**
- `generate_kotlin_mapping_code`: Returns a specialized LLM prompt to be executed by the LLM. This prompt contains all the necessary information (final mapping table, API details, authentication methods) to generate functional Kotlin code, including unit tests and error handling.
- @generate-resources really search the correct endpoints for each field in that api, implement this in the plan 

## Step 7: Run the unit test with the Clean.json input
- Run and debug the unit test to see the results => how they are then displayed in the 3rd-party API.

## 4. 🔑 Key Principles

- **Explainability:** Every important decision, especially in mapping, must be supported by a comprehensible justification.
- **Modularity:** Each step is a standalone tool/agent module with clear input/output definitions.
- **Iteration & Reflection:** The agent can review and correct its own work through the reasoning agent and LLM post-processing.
- **Context Management:** The RAG knowledge base provides focused, relevant context for each step.
- **Planning Integration:** Use of cursor commands and `PLANNING.md` to document and track workflow progress.
- **Full Paths:** All file paths must be specified as full, absolute paths.

## 5. 🛠️ Supporting Tools

- **System Health:** `test_rag_system` for pre-flight checks of the RAG infrastructure
- **Workflow Management:** Automatic updates of `PLANNING.md` and `TASK.md` after each step
- **Advanced Query Strategies:** Multiple `query_api_specification` calls with different search strategies
- **Context Extension:** LLM-based processing of tool outputs for advanced analysis

## 6. 🔄 Workflow Features

- **Multi-Query Approach:** In step 4, various query combinations are systematically executed
- **Prompt Chain Processing:** Tools such as `get_direct_api_mapping_prompt` and `reasoning_agent` return prompts/results that are further processed by the LLM
- **Contextual Inheritance:** Each step uses and extends the context of the previous steps
- **Absolute Path Requirement:** All file paths must be specified completely and absolutely.

This is how the mcp servers can be called:
I'll analyze the `server_fast.py` file to extract the JSON call format for all MCP tools. Let me examine the tool definitions and their parameters.

Read file: mcp-personal-server-py/template-mcp/server_fast.py
Based on my analysis of `server_fast.py`, here are the JSON call formats for all **11 active MCP tools**:


## 🔧 MCP Tools JSON Call Formats

### 1. **test_rag_system**
```json
{
  "tool": "test_rag_system",
  "arguments": {}
}
```

### 2. **list_available_api_specs**
```json
{
  "tool": "list_available_api_specs",
  "arguments": {}
}
```

### 3. **upload_api_specification**
```json
{
  "tool": "upload_api_specification",
  "arguments": {
    "openapi_file_path": "/path/to/your/api-spec.json",
    "collection_name": "my_api_collection",
    "metadata": {
      "version": "1.0.0",
      "description": "Optional metadata object"
    }
  }
}
```

### 4. **query_api_specification**
```json
{
  "tool": "query_api_specification",
  "arguments": {
    "query": "user authentication endpoints",
    "collection_name": "my_api_collection",
    "limit": 5,
    "score_threshold": 0.5,
    "current_path": "/path/to/save/results"
  }
}
```

### 5. **delete_api_specification**
```json
{
  "tool": "delete_api_specification",
  "arguments": {
    "collection_name": "my_api_collection"
  }
}
```

### 6. **enhanced_rag_analysis**
```json
{
  "tool": "enhanced_rag_analysis",
  "arguments": {
    "webhook_json_path": "/path/to/webhook.json",
    "current_directory": "/path/to/save/results",
    "collection_name": "api_collection_name"
  }
}
```

### 7. **reasoning_agent** (async)
```json
{
  "tool": "reasoning_agent",
  "arguments": {
    "source_analysis_path": "/path/to/source_analysis.md",
    "api_spec_path": "/path/to/api_spec.json",
    "output_directory": "/path/to/output/directory",
    "target_collection_name": "target_api_spec_name"
  }
}
```

### 8. **analyze_json_fields_with_rag**
```json
{
  "tool": "analyze_json_fields_with_rag",
  "arguments": {
    "webhook_json_path": "/path/to/webhook.json",
    "current_directory": "/path/to/save/results",
    "collection_name": "api_collection_name"
  }
}
```

### 9. **get_direct_api_mapping_prompt**
```json
{
  "tool": "get_direct_api_mapping_prompt",
  "arguments": {
    "api_spec_path": "/path/to/api_spec.json",
    "analysis_md_path": "/path/to/analysis.md"
  }
}
```

### 10. **generate_kotlin_mapping_code**
```json
{
  "tool": "generate_kotlin_mapping_code",
  "arguments": {
    "mapping_report_path": "/path/to/mapping_report.md"
  }
}
```

### 11. **iterative_mapping_with_feedback**
```json
{
  "tool": "iterative_mapping_with_feedback",
  "arguments": {
    "source_fields": "field1,field2,field3",
    "target_collection": "api_collection_name",
    "api_spec_path": "/path/to/api_spec.json",
    "output_path": "/path/to/save/results"
  }
}
```

## 📋 Tool Categories

### **RAG System Tools** (5 tools)
- `test_rag_system` - Test connectivity
- `list_available_api_specs` - List collections
- `upload_api_specification` - Upload API specs
- `query_api_specification` - Query API docs
- `delete_api_specification` - Delete collections

### **Analysis & Processing Tools** (4 tools)
- `enhanced_rag_analysis` - Enhanced JSON field analysis with RAG
- `reasoning_agent` - End-to-end mapping orchestration
- `analyze_json_fields_with_rag` - JSON field extraction and analysis
- `get_direct_api_mapping_prompt` - Direct API analysis

### **Code Generation Tools** (2 tools)
- `generate_kotlin_mapping_code` - Kotlin code generation
- `iterative_mapping_with_feedback` - Iterative mapping with feedback loop


All tools return string responses with detailed markdown-formatted reports and analysis results.
