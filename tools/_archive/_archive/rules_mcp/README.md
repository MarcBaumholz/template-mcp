# Rules MCP Tool

A simple MCP tool that copies the entire `.cursor/rules` folder structure to the current working directory.

## Purpose

This tool is designed to bootstrap development environments with all the necessary rules, guidelines, and configuration files. It's the first tool you should call when starting development on a new machine or project.

## Usage

### MCP Tool Calls

```json
{
  "tool": "copy_rules_to_working_directory",
  "arguments": {
    "target_directory": "/optional/target/path"
  }
}
```

```json
{
  "tool": "get_rules_source_info",
  "arguments": {}
}
```

### Python Direct Usage

```python
from tools.rules_mcp import copy_rules_to_working_directory, get_rules_source_info

# Copy rules to current working directory
result = copy_rules_to_working_directory()
print(result)

# Get information about what will be copied
info = get_rules_source_info()
print(info)
```

## What Gets Copied

The tool copies the entire `.cursor/rules` folder structure including:

- **Main Rules Files:**
  - `MappingRules.mdc` - API integration workflow rules
  - `mcp-rules.mdc` - MCP development best practices
  - `cognitivemind_rules.mdc` - Cognitive-Mind orchestration
  - `shortrules.mdc` - Quick reference rules

- **Cognitive-Mind Directory:**
  - Complete workflow definition and agent specifications
  - Memory protocols and state schemas
  - Queen agent orchestration rules

- **Learnings Directory:**
  - Endpoint validation guides
  - Improved mapping protocols
  - Project learnings and TODOs
  - Structure documentation

## Features

- **Recursive Copy:** Copies all files and subdirectories
- **Preserves Structure:** Maintains the exact folder hierarchy
- **Detailed Reporting:** Shows exactly what was copied
- **Error Handling:** Graceful error handling with informative messages
- **Optional Target:** Can specify custom target directory

## When to Use

1. **New Development Setup:** First tool to call on a new machine
2. **Project Bootstrap:** When starting a new project that needs the rules
3. **Environment Sync:** When you need to ensure rules are up to date
4. **Development Context:** When working on a different machine

## Example Output

```
✅ Rules successfully copied to: /path/to/working/dir/.cursor/rules

📊 Copy Summary:
- Files copied: 15
- Directories copied: 2
- Total items: 17

📁 Copied Files:
  • MappingRules.mdc
  • cognitivemind/1_cognitive-mind-overview.md
  • cognitivemind/2_worker-agent-specifications.md
  • ...

📂 Copied Directories:
  • cognitivemind
  • learninigs

🚀 Next Steps:
1. Your development environment now has all the rules and guidelines
2. You can start using the MCP tools with full context
3. The .cursor/rules folder contains all necessary configuration
```

## Integration

This tool is integrated into both `server_fast.py` and `server_sse.py` and is available as an MCP tool in the connector-mcp server.
