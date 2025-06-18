# MCP Server Integration Guide
## Schema Mapping & RAG Tools

### 🚀 Overview
Your MCP server now includes advanced schema mapping capabilities that combine:
- **RAG (Retrieval-Augmented Generation)** for API documentation search
- **Multi-Agent AI System** for intelligent field analysis
- **Cognitive Pattern Matching** for semantic similarity
- **Markdown Report Generation** for comprehensive output

---

## 🔧 Server Configuration

### Environment Variables Required
```bash
# Required for AI agents (using free model)
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Optional for enhanced features
QDRANT_STORAGE_PATH=/path/to/qdrant/storage  # Defaults to ./qdrant_storage
```

### Dependencies
All required packages are in `requirements.txt`:
- `sentence-transformers` - For text embeddings
- `qdrant-client` - Vector database
- `fastmcp` - MCP server framework
- `openai` - For OpenRouter API calls
- `pydantic` - Data validation

---

## 🛠️ Available MCP Tools

### 1. **RAG System Tools**

#### `upload_api_specification`
Upload OpenAPI specs to the RAG system for analysis.
```json
{
  "openapi_file_path": "path/to/your/api.json",
  "collection_name": "my_api_collection",
  "metadata": {"version": "v2", "domain": "hr"}
}
```

#### `list_available_api_specs`
List all uploaded API collections.
```json
{}
```

#### `query_api_specification`
Search through uploaded API documentation.
```json
{
  "query": "employee time off fields",
  "collection_name": "stackone_api",
  "limit": 5,
  "score_threshold": 0.5
}
```

#### `delete_api_specification`
Remove an API collection.
```json
{
  "collection_name": "old_api_collection"
}
```

### 2. **Schema Mapping Tools**

#### `intelligent_schema_mapping`
Main tool for AI-powered field mapping between schemas.
```json
{
  "source_json_path": "examples/sample_employee_data.json",
  "source_analysis_md_path": "examples/sample_employee_analysis.md",
  "target_collection_name": "stackone_api",
  "mapping_context": "Employee time off management system",
  "max_matches_per_field": 3,
  "output_path": "mapping_report.md"
}
```

### 3. **Analysis Tools**

#### `analyze_json_structure`
Analyze the structure of JSON data.
```json
{
  "json_data": "{\"employee\": {\"id\": \"123\"}}"
}
```

#### `analyze_api_fields`
Analyze specific fields against API documentation.
```json
{
  "fields_to_analyze": ["employee_id", "start_date", "end_date"],
  "collection_name": "stackone_api",
  "context_topic": "time off requests"
}
```

#### `enhance_csv_with_rag`
Enhance CSV files with API context and business insights.
```json
{
  "csv_file_path": "data/employees.csv",
  "collection_name": "stackone_api",
  "context_query": "employee data management",
  "output_dir": "enhanced_output/"
}
```

---

## 📋 Step-by-Step Integration Workflow

### Step 1: Upload Your API Documentation
```bash
# Use MCP tool to upload your OpenAPI spec
{
  "tool": "upload_api_specification",
  "arguments": {
    "openapi_file_path": "your_api_spec.json",
    "collection_name": "your_api_name"
  }
}
```

### Step 2: Prepare Your Source Data
Create or prepare:
- **JSON file** with your source data structure
- **Markdown analysis** (optional) with field descriptions

Example structure:
```
project/
├── source_data.json          # Your data structure
├── source_analysis.md        # Field descriptions
└── mapping_report.md         # Generated output
```

### Step 3: Run Schema Mapping
```bash
{
  "tool": "intelligent_schema_mapping",
  "arguments": {
    "source_json_path": "source_data.json",
    "source_analysis_md_path": "source_analysis.md",
    "target_collection_name": "your_api_name",
    "mapping_context": "Description of your mapping goal",
    "max_matches_per_field": 3
  }
}
```

### Step 4: Review Generated Report
The tool generates a comprehensive Markdown report with:
- **Field mappings** with confidence scores
- **AI agent insights** from multiple perspectives
- **Cognitive pattern analysis**
- **Business recommendations**
- **Summary statistics**

---

## 🧠 AI Agent System

Your MCP server uses a **multi-agent architecture**:

### Agent Types:
1. **FlipInfoAgent** - Domain-specific knowledge
2. **WorldKnowledgeAgent** - General business context
3. **CognitiveMatchingAgent** - Pattern recognition
4. **MappingCoordinatorAgent** - Synthesis and recommendations

### Free Model Usage:
All agents use the **free OpenRouter model**: `nousresearch/hermes-3-llama-3.1-405b:free`
- No API costs for basic usage
- Rate limits may apply
- Reliable for schema mapping tasks

---

## 📊 Example Use Cases

### 1. **HR System Integration**
Map employee data between different HRIS systems:
```json
{
  "source": "Legacy HR System",
  "target": "Modern HRIS API",
  "fields": ["emp_id → employee_id", "dept → department_id"]
}
```

### 2. **API Migration**
Map fields when upgrading API versions:
```json
{
  "source": "API v1",
  "target": "API v2", 
  "context": "Backward compatibility mapping"
}
```

### 3. **Data Integration**
Map between different data sources:
```json
{
  "source": "CSV Export",
  "target": "REST API",
  "context": "Bulk data import mapping"
}
```

---

## 🔍 Testing Your Integration

### Quick Test Commands:
```bash
# 1. Test RAG system
curl -X POST "http://localhost:8000/test_rag_system"

# 2. List available collections
curl -X POST "http://localhost:8000/list_available_api_specs"

# 3. Test with sample data (included)
curl -X POST "http://localhost:8000/intelligent_schema_mapping" \
  -H "Content-Type: application/json" \
  -d '{
    "source_json_path": "examples/sample_employee_data.json",
    "target_collection_name": "stackone_api",
    "mapping_context": "Employee time off system"
  }'
```

---

## 📝 Output Examples

### Mapping Report Structure:
```markdown
# Schema Mapping Report

## Request Summary
- Source: examples/sample_employee_data.json
- Target: stackone_api
- Context: Employee time off management

## Field Mappings

### emp_id → employee_id
**Confidence:** 95%
**Reasoning:** Direct semantic match, common naming pattern
**AI Insights:**
- FlipInfo: Standard employee identifier pattern
- WorldKnowledge: Universal HR field mapping
- CognitiveMatching: High structural similarity

## Summary Statistics
- Total Fields: 12
- Matched Fields: 11
- Average Confidence: 87%
```

---

## 🛡️ Best Practices

### Security:
- Store API keys in environment variables
- Use `.env` files for local development
- Never commit API keys to version control

### Performance:
- RAG system uses local Qdrant storage
- First API upload creates the collection
- Subsequent queries are fast (vector search)

### Maintenance:
- Regularly update API specifications
- Monitor Qdrant storage size
- Check agent performance with different contexts

---

## 🐞 Troubleshooting

### Common Issues:

#### "Collection not found"
```bash
# Solution: Upload your API spec first
{
  "tool": "upload_api_specification",
  "arguments": {
    "openapi_file_path": "your_api.json",
    "collection_name": "your_collection"
  }
}
```

#### "No matches found"
- Increase `score_threshold` to include more results
- Check if your API spec contains relevant fields
- Verify the `mapping_context` is descriptive

#### "Agent timeout"
- Free model has rate limits
- Wait a moment and retry
- Consider simplifying the request

---

## 📚 Next Steps

1. **Upload your API specs** to the RAG system
2. **Create source data samples** for testing
3. **Run mapping tests** with your real data
4. **Integrate results** into your data pipeline
5. **Monitor and refine** mapping accuracy

Your MCP server is now ready for intelligent schema mapping! 🎉 