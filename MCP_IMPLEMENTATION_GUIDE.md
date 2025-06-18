# MCP JSON Analysis Server - Implementation Guide

## 🎯 Overview
This guide shows you how to implement the MCP JSON Analysis Server in your MCP client configuration (Claude Desktop, Cursor, etc.).

## 📋 Prerequisites
- Python 3.10+ installed
- Virtual environment activated
- MCP dependencies installed (`pip install -r requirements.txt`)

## 🚀 Implementation Steps

### 1. For Claude Desktop

Add this configuration to your Claude Desktop MCP settings file:

**Location:** `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)

```json
{
  "mcpServers": {
    "mcp-json-analysis": {
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

### 2. For Cursor IDE

Add this to your Cursor MCP configuration:

**Location:** Cursor Settings → MCP Servers

```json
{
  "mcp-json-analysis": {
    "command": "python",
    "args": ["/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/mcp-personal-server-py/template-mcp/server.py"],
    "cwd": "/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/mcp-personal-server-py/template-mcp",
    "env": {
      "PATH": "/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/mcp-personal-server-py/template-mcp/venv/bin:/usr/local/bin:/usr/bin:/bin",
      "VIRTUAL_ENV": "/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/mcp-personal-server-py/template-mcp/venv"
    }
  }
}
```

### 3. Manual Testing

You can test the server manually using the start script:

```bash
cd /Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/mcp-personal-server-py/template-mcp
chmod +x start_server.sh
./start_server.sh
```

## 🛠️ Available Tools

Once implemented, you'll have access to these JSON analysis tools:

### 1. `analyze_json_structure`
Analyzes the structure of a JSON object and returns detailed schema information.

**Usage:**
```
Please analyze this JSON structure: {"user": {"name": "John", "age": 30, "hobbies": ["reading", "coding"]}}
```

### 2. `extract_json_fields`
Extracts specific fields from a JSON object using dot notation paths.

**Usage:**
```
Extract the user name and age from this JSON: {"user": {"name": "John", "age": 30}}
Use paths: user.name, user.age
```

### 3. `flatten_json`
Flattens a nested JSON object into a flat structure with dot notation keys.

**Usage:**
```
Please flatten this nested JSON: {"user": {"profile": {"name": "John", "settings": {"theme": "dark"}}}}
```

## 🔧 Configuration Details

### Environment Variables
The server uses the virtual environment located at:
```
/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/mcp-personal-server-py/template-mcp/venv
```

### Working Directory
```
/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/mcp-personal-server-py/template-mcp
```

### Python Path
The server uses the Python interpreter from the virtual environment:
```
/Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/mcp-personal-server-py/template-mcp/venv/bin/python
```

## 🐛 Troubleshooting

### Server Won't Start
1. Check that the virtual environment exists and has the required packages
2. Verify the paths in the configuration are correct
3. Ensure Python 3.10+ is installed
4. Check that `server.py` is executable

### Tools Not Available
1. Restart your MCP client after adding the configuration
2. Check the MCP client logs for connection errors
3. Test the server manually using `./start_server.sh`

### Permission Issues
```bash
chmod +x start_server.sh
chmod +x server.py
```

## 📝 Example Usage in Claude Desktop

After implementation, you can use the tools like this:

```
Hi! I have this JSON data and need help analyzing it:

{
  "users": [
    {
      "id": 1,
      "profile": {
        "name": "Alice",
        "email": "alice@example.com",
        "preferences": {
          "theme": "dark",
          "notifications": true
        }
      }
    }
  ]
}

Can you:
1. Analyze its structure
2. Extract the user name and email
3. Flatten it for easier processing
```

Claude will automatically use the MCP JSON Analysis tools to help you!

## 🔄 Updates and Maintenance

To update the server:
1. Pull the latest code
2. Restart your MCP client
3. The new functionality will be available immediately

## 📞 Support

If you encounter issues:
1. Check the server logs
2. Verify the configuration paths
3. Test the server manually
4. Check Python and dependency versions