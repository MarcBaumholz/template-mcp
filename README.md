# MCP JSON Analysis and RAG Server

A comprehensive Model Context Protocol (MCP) server that provides JSON analysis tools, RAG (Retrieval-Augmented Generation) functionality for OpenAPI specification analysis, and intelligent schema mapping capabilities.

## 🚀 Features

### JSON Analysis Tools
- **analyze_json_structure**: Analyze JSON structure and return detailed schema information
- **extract_json_fields**: Extract specific fields using dot notation paths
- **flatten_json**: Flatten nested JSON objects into flat structures

### RAG Tools (Requires OpenRouter API Key)
- **list_available_api_specs**: List all API specification collections
- **upload_api_specification**: Upload OpenAPI specs to RAG system
- **query_api_specification**: Query API documentation with semantic search
- **delete_api_specification**: Delete API specification collections
- **analyze_api_fields**: Analyze fields using RAG retrieval + LLM synthesis
- **enhance_json_fields**: Enhance JSON analysis with RAG context
- **enhance_csv_with_rag**: Enhance CSV data with API context

### Intelligent Schema Mapping (New!)
- **intelligent_schema_mapping**: AI-powered schema field mapping with cognitive pattern matching
  - Uses multiple AI agents (FlipInfoAgent, WorldKnowledgeAgent, CognitiveMatchingAgent)
  - Semantic similarity analysis with sentence transformers
  - RAG-based target field discovery
  - Comprehensive mapping reports with confidence scores
  - Supports JSON source data and Markdown analysis files

## 📋 Prerequisites

- Python 3.10 or higher
- OpenRouter API key (for RAG functionality and schema mapping)

## 🛠️ Installation

1. **Clone and navigate to the project:**
   ```bash
   cd /path/to/mcp-personal-server-py/template-mcp
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

## 🔧 Configuration

### Claude Desktop

Add to your Claude Desktop config file (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "mcp-json-rag-server": {
      "command": "python",
      "args": ["/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/mcp-personal-server-py/template-mcp/server.py"],
      "cwd": "/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/mcp-personal-server-py/template-mcp",
      "env": {
        "PATH": "/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/mcp-personal-server-py/template-mcp/venv/bin:/usr/local/bin:/usr/bin:/bin",
        "VIRTUAL_ENV": "/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/mcp-personal-server-py/template-mcp/venv"
      }
    }
  }
}
```

### Cursor IDE

Add to your Cursor MCP settings:

```json
{
  "mcpServers": {
    "mcp-json-rag-server": {
      "command": "python",
      "args": ["/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/mcp-personal-server-py/template-mcp/server.py"],
      "cwd": "/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/mcp-personal-server-py/template-mcp",
      "env": {
        "PATH": "/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/mcp-personal-server-py/template-mcp/venv/bin:/usr/local/bin:/usr/bin:/bin",
        "VIRTUAL_ENV": "/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/mcp-personal-server-py/template-mcp/venv"
      }
    }
  }
}
```

## 🧪 Testing

### Manual Testing

1. **Start the server:**
   ```bash
   ./start_server.sh
   ```

2. **Test JSON analysis:**
   ```bash
   source venv/bin/activate
   python -c "
   import json
   from server import analyze_structure
   result = analyze_structure('{\"name\": \"John\", \"age\": 30}')
   print(json.dumps(result, indent=2))
   "
   ```

### Available Tools

#### JSON Analysis Tools

1. **analyze_json_structure**
   - Input: `json_data` (string)
   - Output: Structure analysis with type information, key counts, and depth

2. **extract_json_fields**
   - Input: `json_data` (string), `field_paths` (array of dot notation paths)
   - Output: Extracted field values

3. **flatten_json**
   - Input: `json_data` (string)
   - Output: Flattened object with dot notation keys

#### RAG Tools

1. **list_available_api_specs**
   - Input: None
   - Output: List of available collections

2. **upload_api_specification**
   - Input: `openapi_file_path` (string), `collection_name` (string), `metadata` (optional object)
   - Output: Upload status and chunk count

3. **query_api_specification**
   - Input: `query` (string), `collection_name` (string), `limit` (optional int), `score_threshold` (optional float)
   - Output: Relevant documentation snippets with scores

4. **analyze_api_fields**
   - Input: `fields_to_analyze` (array), `collection_name` (optional string), `context_topic` (optional string)
   - Output: Comprehensive field analysis using RAG + LLM

5. **enhance_json_fields**
   - Input: `input_json` (string), `database_name` (optional string)
   - Output: Enhanced field analysis with RAG context

6. **enhance_csv_with_rag**
   - Input: `csv_file_path` (string), `collection_name` (string), `context_query` (string), `output_dir` (optional string)
   - Output: Enhanced CSV analysis with business insights

#### Schema Mapping Tools

7. **intelligent_schema_mapping**
   - Input: `source_json_path` (string), `source_analysis_md_path` (string), `target_collection_name` (string), `mapping_context` (string), `max_matches_per_field` (optional int), `output_path` (optional string)
   - Output: Comprehensive field mapping report with AI analysis
   - Features:
     - Cognitive pattern matching using sentence transformers
     - Multi-agent AI analysis (FlipInfoAgent, WorldKnowledgeAgent, CognitiveMatchingAgent)
     - RAG-based target field discovery
     - Confidence scoring and mapping recommendations
     - Detailed Markdown report generation

## 📁 Project Structure

```
template-mcp/
├── server.py                 # Main MCP server
├── requirements.txt          # Python dependencies
├── start_server.sh          # Server startup script
├── .env.example             # Environment variables template
├── mcp_config.json          # MCP configuration
├── tools/                   # Schema mapping and RAG tools package
│   ├── __init__.py
│   ├── mapping.py           # Schema mapping tool
│   ├── mapping_models.py    # Data models for mapping
│   ├── cognitive_matcher.py # Cognitive pattern matching
│   ├── input_parser.py      # JSON/Markdown parsing
│   ├── ai_agents.py         # AI analysis agents
│   ├── report_generator.py  # Markdown report generation
│   ├── rag_tools.py         # RAG system implementation
│   ├── llm_client.py        # LLM client for analysis
│   └── field_enhancer.py    # Field enhancement utilities
├── tests/                   # Unit tests
│   └── test_schema_mapping.py
└── README.md                # This file
```

## 🔍 Example Usage

### JSON Analysis
```python
# Analyze JSON structure
{
  "json_data": "{\"user\": {\"name\": \"John\", \"age\": 30}, \"active\": true}"
}

# Extract specific fields
{
  "json_data": "{\"user\": {\"name\": \"John\", \"age\": 30}}",
  "field_paths": ["user.name", "user.age"]
}

# Flatten nested JSON
{
  "json_data": "{\"user\": {\"profile\": {\"name\": \"John\"}}}"
}
```

### RAG Analysis
```python
# Upload OpenAPI specification
{
  "openapi_file_path": "/path/to/api-spec.yaml",
  "collection_name": "my_api_v1"
}

# Query API documentation
{
  "query": "user authentication endpoints",
  "collection_name": "my_api_v1",
  "limit": 5
}

# Analyze fields with context
{
  "fields_to_analyze": ["user_id", "email", "created_at"],
  "collection_name": "my_api_v1",
  "context_topic": "User Management"
}
```

### Schema Mapping
```python
# Intelligent schema mapping
{
  "source_json_path": "/path/to/source_data.json",
  "source_analysis_md_path": "/path/to/field_analysis.md", 
  "target_collection_name": "target_api_v2",
  "mapping_context": "Mapping user data from legacy system to new API",
  "max_matches_per_field": 3,
  "output_path": "/path/to/mapping_report.md"
}
```

## 🐛 Troubleshooting

### Common Issues

1. **"RAG tools not available"**
   - Install missing dependencies: `pip install sentence-transformers qdrant-client PyYAML pandas`

2. **"OPENROUTER_API_KEY environment variable not set"**
   - Create `.env` file with your OpenRouter API key

3. **"ValidationError: capabilities field required"**
   - This indicates an MCP SDK version mismatch. Ensure you're using compatible versions.

4. **Import errors**
   - Activate virtual environment: `source venv/bin/activate`
   - Reinstall dependencies: `pip install -r requirements.txt`

### Debug Mode

Run with debug logging:
```bash
PYTHONPATH=. python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
import server
"
```

## 🔧 Development

### Adding New Tools

1. Add tool definition to `handle_list_tools()` in `server.py`
2. Add tool handler to `handle_call_tool()` in `server.py`
3. Implement tool logic in appropriate module under `tools/`
4. Update documentation and tests

### Testing Changes

```bash
# Test imports
python -c "import server; print('OK')"

# Test specific functionality
python -c "from server import analyze_structure; print(analyze_structure('{\"test\": 1}'))"

# Run schema mapping tests
python -m pytest tests/test_schema_mapping.py -v
```

## 📝 License

This project is part of the MCP ecosystem and follows the same licensing terms.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review MCP documentation
3. Create an issue with detailed error information