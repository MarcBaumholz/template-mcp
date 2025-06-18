# MCP Server Setup Guide

This guide shows you how to add your RAG API Analysis MCP Server to your AI assistant's MCP configuration.

## 🚀 Quick Start

### 1. Test Your Server

First, make sure your server is working:

```bash
cd /Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/mcp-personal-server-py/template-mcp
./start_server.sh
```

If you see "Server is ready for MCP client connections", your server is working! Press `Ctrl+C` to stop it.

### 2. Add to Your AI Assistant

Choose your AI assistant below and follow the configuration steps:

---

## 🎯 Claude Desktop Configuration

### Step 1: Find Your Configuration File

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

### Step 2: Add Server Configuration

If the file doesn't exist, create it. Add this configuration:

```json
{
  "mcpServers": {
    "rag-api-analysis": {
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

### Step 3: Restart Claude Desktop

Close and reopen Claude Desktop. You should see your MCP server listed in the available tools.

---

## 🎯 Cursor Configuration

### Step 1: Open Cursor Settings

1. Open Cursor
2. Go to Settings (Cmd+, on Mac, Ctrl+, on Windows)
3. Search for "MCP" or "Model Context Protocol"

### Step 2: Add Server

Add a new MCP server with these settings:

- **Name**: `rag-api-analysis`
- **Command**: `python`
- **Args**: `["/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/mcp-personal-server-py/template-mcp/server.py"]`
- **Working Directory**: `/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/mcp-personal-server-py/template-mcp`
- **Environment Variables**:
  - `PATH`: `/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/mcp-personal-server-py/template-mcp/venv/bin:/usr/local/bin:/usr/bin:/bin`
  - `VIRTUAL_ENV`: `/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/mcp-personal-server-py/template-mcp/venv`

---

## 🎯 Windsurf Configuration

### Step 1: Open Windsurf Settings

1. Open Windsurf
2. Go to Settings
3. Navigate to MCP configuration section

### Step 2: Add Server Configuration

Use the same configuration as Claude Desktop:

```json
{
  "mcpServers": {
    "rag-api-analysis": {
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

---

## 🧪 Testing Your Setup

Once configured, test your MCP server by asking your AI assistant:

### Basic Test
```
"Can you list the available API specifications in the RAG system?"
```

### Advanced Test
```
"Please analyze these fields with the context topic 'AbsenceRequestCreated': 
- absence created
- start date  
- end date
- employee id
- reason"
```

---

## 📋 Available Tools

Your MCP server provides these tools:

| Tool Name | Description |
|-----------|-------------|
| `list_available_api_specs` | Lists all API specification collections |
| `upload_api_specification` | Upload OpenAPI spec to RAG system |
| `query_api_specification` | Query API documentation directly |
| `delete_api_specification` | Delete an API specification collection |
| `analyze_api_fields` | **ENHANCED** Analyze fields with optional context topics |

---

## 🔧 Troubleshooting

### Server Won't Start

1. **Check Virtual Environment**:
   ```bash
   cd /Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/mcp-personal-server-py/template-mcp
   source venv/bin/activate
   python -c "from tools import *; print('✅ Tools working')"
   ```

2. **Check Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Check Environment Variables**:
   - Ensure `.env` file exists with your API keys
   - Verify `QDRANT_URL`, `QDRANT_API_KEY`, and `OPENAI_API_KEY` are set

### MCP Client Can't Connect

1. **Check File Paths**: Ensure all paths in the configuration are absolute and correct
2. **Check Permissions**: Make sure the server script is executable
3. **Check Logs**: Look at your AI assistant's logs for error messages

### No RAG Results

1. **Upload API Specification First**:
   ```
   "Please upload the API specification from sample_data/api_flip.yml to collection 'flip_api_v2'"
   ```

2. **Lower Score Threshold**: Try using a lower score threshold (0.2 or 0.3) in queries

3. **Use Different Keywords**: Try different field names or search terms

---

## 🎯 Example Usage

Once your MCP server is configured, you can use it like this:

### Upload API Specification
```
"Please upload the OpenAPI specification from the file sample_data/api_flip.yml to a collection called 'my_api'"
```

### Analyze Fields with Context
```
"Analyze these employee absence fields with the context 'AbsenceRequestCreated':
- start_date
- end_date  
- employee_id
- absence_type
- reason"
```

### Query API Documentation
```
"Search the API documentation for information about employee time off endpoints"
```

---

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review the server logs for error messages
3. Test individual components using the provided test scripts
4. Ensure all environment variables are properly configured

Your MCP server is now ready to enhance your AI assistant with powerful RAG-based API analysis capabilities! 🚀 