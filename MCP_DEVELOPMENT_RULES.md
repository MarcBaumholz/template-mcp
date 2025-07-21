# 🚀 MCP Development Rules & Best Practices

## 📚 Overview
These rules distill all learnings from building production-quality MCP (Model Context Protocol) servers. They ensure clean, maintainable, and robust MCP implementations.

---

## 🎯 Core MCP Development Principles

### 🔑 Golden Rules
1. **Keep it Simple**: MCP servers should be focused, not monolithic
2. **Modular Design**: Split functionality into clear modules (≤200 lines per file)
3. **Lazy Loading**: Use lazy imports to minimize startup time
4. **Graceful Degradation**: Always provide fallbacks when external services fail
5. **Environment-First**: All configurations via environment variables
6. **Virtual Environment**: Always use venv for dependency isolation
7. **Test Early**: Unit tests for every function/tool

### 📋 Project Structure Template
```
your-mcp-server/
├── server.py              # Main MCP server (FastMCP preferred)
├── server_fast.py          # Alternative fast-loading server
├── requirements.txt        # Pinned dependencies
├── .env.example           # Template environment variables
├── .env                   # Actual environment (git-ignored)
├── start_server.sh        # Server startup script
├── README.md              # Clear setup and usage docs
├── PLANNING.md            # High-level architecture & decisions
├── TASK.md                # Current tasks and backlog
├── tools/                 # Modular tool implementations
│   ├── __init__.py
│   ├── core_tools.py      # Basic functionality
│   ├── advanced_tools.py  # Complex features
│   └── clients/           # External service clients
├── tests/                 # Unit tests mirroring structure
│   ├── test_core_tools.py
│   └── test_advanced_tools.py
├── examples/              # Sample data and usage
├── outputs/               # Generated files/reports
└── venv/                  # Virtual environment
```

---

## 🧱 Code Organization Rules

### File Size Limits
- **Never exceed 200 lines** per file
- **Split at 150 lines** to maintain readability
- **Break into modules** when functionality grows
- **Use lazy imports** for heavy dependencies

### Import Strategy
```python
# ✅ Good: Lazy imports for heavy dependencies
def get_ml_tools():
    global _ml_tools
    if _ml_tools is None:
        from sentence_transformers import SentenceTransformer
        from qdrant_client import QdrantClient
        _ml_tools = {...}
    return _ml_tools

# ❌ Bad: Heavy imports at module level
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
```

### Module Separation
```python
# Core tools (fast loading, basic functionality)
@mcp.tool()
def analyze_json_structure(json_data: str) -> str:
    """Basic JSON analysis - no external dependencies"""

# Advanced tools (lazy loaded, complex functionality)  
@mcp.tool()
def intelligent_schema_mapping(source: str, target: str) -> str:
    """Complex AI-powered mapping - lazy loaded"""
    tools = get_advanced_tools()
    return tools['schema_mapper'](source, target)
```

---

## 🔧 MCP Server Implementation

### FastMCP Pattern (Preferred)
```python
#!/usr/bin/env python3
from fastmcp import FastMCP
import os
import logging

# Environment loading
try:
    from dotenv import load_dotenv
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(script_dir, '.env')
    load_dotenv(env_path)
except ImportError:
    pass

# Initialize MCP server
mcp = FastMCP("Your MCP Server Name")

# Basic tools (fast loading)
@mcp.tool()
def simple_tool(input_data: str) -> str:
    """Simple tool description"""
    return f"Processed: {input_data}"

# Lazy-loaded complex tools
_advanced_tools = None

def get_advanced_tools():
    global _advanced_tools
    if _advanced_tools is None:
        from .tools import AdvancedProcessor
        _advanced_tools = {'processor': AdvancedProcessor()}
    return _advanced_tools

@mcp.tool()
def complex_tool(input_data: str) -> str:
    """Complex tool with lazy loading"""
    tools = get_advanced_tools()
    return tools['processor'].process(input_data)

if __name__ == "__main__":
    mcp.run()
```

### Error Handling Pattern
```python
@mcp.tool()
def robust_tool(input_data: str) -> str:
    """Tool with proper error handling and fallbacks"""
    try:
        # Primary processing
        result = primary_processor(input_data)
        return result
    except ExternalAPIError as e:
        # Fallback to local processing
        logger.warning(f"API failed, using fallback: {e}")
        return fallback_processor(input_data)
    except Exception as e:
        # Graceful error response
        logger.error(f"Tool failed: {e}")
        return f"Error processing request: {str(e)[:100]}"
```

---

## 🛠️ Tool Development Standards

### Tool Function Signature
```python
@mcp.tool()
def tool_name(
    required_param: str,
    optional_param: Optional[str] = "",
    typed_param: List[str] = [],
    config_param: int = 5
) -> str:
    """
    Clear, concise tool description that explains what it does.
    
    Args:
        required_param: Clear description of required parameter
        optional_param: Description of optional parameter
        typed_param: List of strings for batch processing
        config_param: Configuration parameter with sensible default
        
    Returns:
        String result that can be displayed or processed further
    """
```

### Tool Implementation Pattern
```python
@mcp.tool()
def example_tool(data: str, config: str = "default") -> str:
    """Tool following best practices"""
    
    # 1. Input validation
    if not data or not data.strip():
        return "Error: data parameter cannot be empty"
    
    # 2. Environment/config handling
    config_value = config if config else os.getenv('DEFAULT_CONFIG', 'fallback')
    
    # 3. Processing with error handling
    try:
        result = process_data(data, config_value)
        
        # 4. Output formatting
        return format_result(result)
        
    except Exception as e:
        # 5. Graceful error handling
        logger.error(f"Tool failed: {e}")
        return f"Processing failed: {str(e)}"
```

---

## 🔒 Environment & Security

### Environment Variables Pattern
```bash
# .env.example
# Core Configuration
SERVER_NAME=my-mcp-server
SERVER_PORT=8000

# External API Keys (if needed)
OPENROUTER_API_KEY=your_openrouter_key_here
OPENROUTER_MODEL=gpt-3.5-turbo

# Database Configuration (if applicable)
QDRANT_URL=https://your-qdrant-instance.com
QDRANT_API_KEY=your_qdrant_key

# Optional Configuration
DEFAULT_COLLECTION=my_collection
DEBUG_MODE=false
```

### Environment Loading
```python
import os
from dotenv import load_dotenv

# Always load from script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, '.env')
load_dotenv(env_path)

# Validation with fallbacks
def get_env_var(key: str, default: str = None) -> str:
    value = os.getenv(key)
    if not value and default is None:
        raise ValueError(f"Required environment variable {key} not set")
    return value or default
```

### Security Rules
- **Never hardcode API keys** in source code
- **Use environment variables** for all secrets
- **Validate all inputs** before processing
- **Sanitize file paths** to prevent directory traversal
- **Log security events** but not sensitive data

---

## 🧪 Testing & Quality Assurance

### Unit Testing Pattern
```python
# tests/test_tools.py
import pytest
from unittest.mock import patch, MagicMock
from tools.core_tools import example_tool

class TestExampleTool:
    def test_successful_processing(self):
        """Test normal operation"""
        result = example_tool("test data")
        assert "Processed" in result
        assert result != ""
    
    def test_empty_input(self):
        """Test edge case: empty input"""
        result = example_tool("")
        assert "Error" in result
    
    @patch('tools.core_tools.external_api_call')
    def test_api_failure_fallback(self, mock_api):
        """Test fallback when external API fails"""
        mock_api.side_effect = ConnectionError("API down")
        result = example_tool("test data")
        assert "fallback" in result.lower()
```

### Testing Rules
- **Test every public function** with at least 3 cases:
  - ✅ **Success case**: Normal operation
  - ⚠️ **Edge case**: Boundary conditions
  - ❌ **Failure case**: Error handling
- **Mock external services** to avoid flaky tests
- **Test error messages** are user-friendly
- **Run tests in CI/CD** before deployment

---

## 📊 Performance & Optimization

### Lazy Loading Implementation
```python
# Global cache for heavy resources
_heavy_resources = {}

def get_heavy_resource(resource_name: str):
    """Lazy load expensive resources"""
    if resource_name not in _heavy_resources:
        if resource_name == 'ml_model':
            from sentence_transformers import SentenceTransformer
            _heavy_resources[resource_name] = SentenceTransformer('all-MiniLM-L6-v2')
        elif resource_name == 'vector_db':
            from qdrant_client import QdrantClient
            _heavy_resources[resource_name] = QdrantClient(url=get_env_var('QDRANT_URL'))
    
    return _heavy_resources[resource_name]
```

### Caching Strategy
```python
from functools import lru_cache
import time

@lru_cache(maxsize=100)
def expensive_computation(input_hash: str) -> str:
    """Cache expensive computations"""
    # Expensive processing here
    return result

# Cache with TTL for external API calls
_api_cache = {}
_cache_ttl = 300  # 5 minutes

def cached_api_call(query: str) -> dict:
    now = time.time()
    cache_key = f"api_{hash(query)}"
    
    if cache_key in _api_cache:
        cached_result, timestamp = _api_cache[cache_key]
        if now - timestamp < _cache_ttl:
            return cached_result
    
    result = external_api_call(query)
    _api_cache[cache_key] = (result, now)
    return result
```

---

## 📝 Documentation Standards

### README.md Structure
```markdown
# MCP Server Name

Brief description of what the server does.

## 🚀 Features
- List key capabilities
- Highlight unique features

## 📋 Prerequisites
- Python 3.10+
- Required system dependencies

## 🛠️ Installation
Step-by-step setup instructions

## 🔧 Configuration
Environment variables and config options

## 🧪 Testing
How to test the server

## 📁 Project Structure
Directory layout explanation

## 🔍 Example Usage
Practical examples for each tool
```

### Function Documentation
```python
def complex_function(param1: str, param2: Optional[int] = None) -> Dict[str, Any]:
    """
    Brief summary of what the function does.
    
    Detailed explanation of the function's purpose, behavior, and any
    important considerations for usage.
    
    Args:
        param1: Description of the parameter, including valid values
        param2: Optional parameter with default behavior explanation
        
    Returns:
        Dictionary containing:
        - 'result': Processed output
        - 'metadata': Processing information
        - 'status': Success/error status
        
    Raises:
        ValueError: When param1 is invalid
        ConnectionError: When external service is unreachable
        
    Example:
        >>> result = complex_function("input data", 42)
        >>> print(result['status'])
        'success'
    """
```

---

## 🚦 Development Workflow

### Planning Phase
1. **Create PLANNING.md** with architecture decisions
2. **Define TASK.md** with specific implementation tasks
3. **Set up virtual environment** and dependencies
4. **Create project structure** following template

### Implementation Phase
```python
# 1. Start with core functionality (basic tools)
@mcp.tool()
def basic_tool(input: str) -> str:
    """Core functionality - no external dependencies"""
    return process_basic(input)

# 2. Add advanced features incrementally
@mcp.tool() 
def advanced_tool(input: str) -> str:
    """Advanced functionality - lazy loaded"""
    processor = get_advanced_processor()
    return processor.handle(input)

# 3. Implement error handling and fallbacks
@mcp.tool()
def robust_tool(input: str) -> str:
    """Production-ready tool with full error handling"""
    try:
        return primary_process(input)
    except ExternalError:
        return fallback_process(input)
    except Exception as e:
        return f"Error: {str(e)}"
```

### Testing & Deployment
```bash
# 1. Run unit tests
python -m pytest tests/ -v

# 2. Test MCP server manually  
./start_server.sh

# 3. Integration test with MCP client
# Configure in Claude Desktop/Cursor and test tools

# 4. Performance testing
python -c "from server import *; test_performance()"
```

---

## 🎯 MCP-Specific Best Practices

### Tool Naming Convention
```python
# ✅ Good: Clear, action-oriented names
@mcp.tool()
def analyze_json_structure(data: str) -> str:

@mcp.tool() 
def upload_api_specification(file_path: str, collection: str) -> str:

@mcp.tool()
def query_api_documentation(query: str, limit: int = 5) -> str:

# ❌ Bad: Vague or unclear names
@mcp.tool()
def process_data(data: str) -> str:

@mcp.tool()
def do_stuff(input: str) -> str:
```

### Parameter Design
```python
# ✅ Good: Clear types, sensible defaults, validation
@mcp.tool()
def search_documentation(
    query: str,                          # Required, clear purpose
    collection_name: str = "default",    # Optional with fallback
    limit: int = 5,                      # Reasonable default
    score_threshold: float = 0.5         # Tunable parameter
) -> str:
    if not query.strip():
        return "Error: query cannot be empty"
    # ... implementation

# ❌ Bad: Unclear parameters, no validation
@mcp.tool()
def search(q, db=None, n=None) -> str:
    # ... implementation
```

### Output Formatting
```python
@mcp.tool()
def generate_report(data: str) -> str:
    """Generate formatted report for MCP client display"""
    try:
        results = process_data(data)
        
        # Format for readability
        report = f"""
# Analysis Report

## Summary
- Total items: {len(results)}
- Processing time: {results['time']:.2f}s

## Results
{format_results_table(results['items'])}

## Recommendations
{generate_recommendations(results)}
"""
        return report.strip()
        
    except Exception as e:
        return f"❌ Report generation failed: {str(e)}"
```

---

## 🔄 Error Handling & Resilience

### Layered Error Handling
```python
class MCPToolError(Exception):
    """Base exception for MCP tool errors"""
    pass

class ExternalServiceError(MCPToolError):
    """External service unavailable"""
    pass

class InputValidationError(MCPToolError):
    """Input validation failed"""
    pass

@mcp.tool()
def resilient_tool(input_data: str) -> str:
    """Tool with comprehensive error handling"""
    
    # Layer 1: Input validation
    try:
        validated_input = validate_input(input_data)
    except ValueError as e:
        return f"❌ Input error: {str(e)}"
    
    # Layer 2: External service calls
    try:
        external_result = call_external_service(validated_input)
    except ExternalServiceError:
        logger.warning("External service failed, using fallback")
        external_result = fallback_service(validated_input)
    
    # Layer 3: Processing
    try:
        final_result = process_result(external_result)
        return format_success_response(final_result)
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        return f"❌ Processing error: {str(e)[:100]}"
```

### Graceful Degradation
```python
@mcp.tool()
def smart_analysis(data: str) -> str:
    """Analysis with AI enhancement and local fallback"""
    
    # Try AI-enhanced analysis first
    try:
        if os.getenv('OPENROUTER_API_KEY'):
            return ai_enhanced_analysis(data)
    except Exception as e:
        logger.warning(f"AI analysis failed: {e}")
    
    # Fallback to local analysis
    try:
        return local_analysis(data)
    except Exception as e:
        # Last resort: basic processing
        return basic_analysis(data)
```

---

## 📈 Monitoring & Logging

### Logging Setup
```python
import logging
import os

def setup_logging():
    """Configure logging for MCP server"""
    level = logging.DEBUG if os.getenv('DEBUG_MODE') == 'true' else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('mcp_server.log'),
            logging.StreamHandler()
        ]
    )
    
    # Suppress noisy third-party loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('openai').setLevel(logging.WARNING)

# Usage in tools
logger = logging.getLogger(__name__)

@mcp.tool()
def monitored_tool(input_data: str) -> str:
    """Tool with comprehensive logging"""
    logger.info(f"Processing request: {input_data[:50]}...")
    
    start_time = time.time()
    try:
        result = process_data(input_data)
        processing_time = time.time() - start_time
        
        logger.info(f"Request completed in {processing_time:.2f}s")
        return result
        
    except Exception as e:
        logger.error(f"Request failed after {time.time() - start_time:.2f}s: {e}")
        raise
```

---

## 🔧 Deployment & Operations

### Server Startup Script
```bash
#!/bin/bash
# start_server.sh

set -e  # Exit on any error

echo "🚀 Starting MCP Server..."

# Check virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Activating virtual environment..."
    source venv/bin/activate
fi

# Check dependencies
python -c "import mcp, fastmcp" 2>/dev/null || {
    echo "❌ Dependencies missing. Installing..."
    pip install -r requirements.txt
}

# Check environment file
if [[ ! -f .env ]]; then
    echo "⚠️  No .env file found. Copying from .env.example"
    cp .env.example .env
    echo "📝 Please edit .env with your configuration"
    exit 1
fi

# Start server
echo "✅ Starting MCP server..."
python server.py
```

### Health Check Implementation
```python
@mcp.tool()
def health_check() -> str:
    """Health check for MCP server status"""
    checks = {
        "server": "✅ Running",
        "environment": "✅ Loaded" if os.getenv('SERVER_NAME') else "❌ Missing",
        "tools": "✅ Available",
    }
    
    # Test external dependencies
    try:
        # Test database connection
        test_db_connection()
        checks["database"] = "✅ Connected"
    except:
        checks["database"] = "❌ Disconnected"
    
    try:
        # Test AI service
        test_ai_service()
        checks["ai_service"] = "✅ Available"
    except:
        checks["ai_service"] = "⚠️  Fallback mode"
    
    status_report = "\n".join([f"- {k}: {v}" for k, v in checks.items()])
    return f"🏥 MCP Server Health Check\n\n{status_report}"
```

---

## 📚 Common Patterns & Examples

### JSON Processing Tools
```python
@mcp.tool()
def analyze_json_structure(json_data: str) -> str:
    """Analyze JSON structure - fast, no external dependencies"""
    try:
        data = json.loads(json_data)
        analysis = analyze_structure_recursive(data)
        return json.dumps(analysis, indent=2)
    except json.JSONDecodeError as e:
        return f"❌ Invalid JSON: {str(e)}"

@mcp.tool()
def extract_json_fields(json_data: str, field_paths: List[str]) -> str:
    """Extract specific fields using dot notation"""
    try:
        data = json.loads(json_data)
        results = {}
        for path in field_paths:
            results[path] = extract_nested_field(data, path)
        return json.dumps(results, indent=2)
    except Exception as e:
        return f"❌ Extraction failed: {str(e)}"
```

### RAG/AI Integration Pattern
```python
_rag_client = None

def get_rag_client():
    """Lazy load RAG client"""
    global _rag_client
    if _rag_client is None:
        from qdrant_client import QdrantClient
        _rag_client = QdrantClient(url=os.getenv('QDRANT_URL'))
    return _rag_client

@mcp.tool()
def intelligent_analysis(
    query: str, 
    collection: str = "default",
    context: str = ""
) -> str:
    """AI-powered analysis with RAG enhancement"""
    try:
        # RAG retrieval
        rag_results = retrieve_context(query, collection)
        
        # AI analysis
        enhanced_context = f"{context}\n\nRelevant context:\n{rag_results}"
        analysis = ai_analyze(query, enhanced_context)
        
        return format_analysis_report(analysis, rag_results)
        
    except Exception as e:
        logger.warning(f"AI analysis failed: {e}")
        return basic_analysis(query)
```

---

## ⚠️ Common Pitfalls to Avoid

### ❌ Don't Do This
```python
# Heavy imports at module level (slows startup)
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

# Hardcoded configurations
API_KEY = "sk-12345..."  # ❌ Never do this

# No error handling
@mcp.tool()
def brittle_tool(data: str) -> str:
    result = external_api_call(data)  # Can fail
    return result['field']  # Can fail

# Unclear function signatures
@mcp.tool()
def process(data, opts=None) -> str:  # ❌ Unclear types/purpose
    pass

# Long functions (>100 lines)
@mcp.tool()
def monolithic_tool(data: str) -> str:
    # ... 200+ lines of mixed concerns
    pass
```

### ✅ Do This Instead
```python
# Lazy loading
def get_ml_tools():
    if 'transformers' not in globals():
        global transformers
        from sentence_transformers import SentenceTransformer
        transformers = SentenceTransformer('model')
    return transformers

# Environment variables
API_KEY = os.getenv('OPENROUTER_API_KEY')

# Comprehensive error handling
@mcp.tool()
def robust_tool(data: str) -> str:
    try:
        validated_data = validate_input(data)
        result = safe_api_call(validated_data)
        return format_response(result)
    except Exception as e:
        return handle_error(e)

# Clear function signatures
@mcp.tool()
def analyze_schema(
    schema_data: str,
    analysis_depth: int = 3,
    include_examples: bool = True
) -> str:
    """Analyze schema structure with configurable depth."""
    pass

# Modular functions
@mcp.tool()
def coordinated_analysis(data: str) -> str:
    """Coordinate multiple analysis steps"""
    parsed = parse_input(data)
    analyzed = analyze_structure(parsed)
    formatted = format_results(analyzed)
    return formatted
```

---

## 🎯 Final Checklist

Before deploying your MCP server, ensure:

### Code Quality
- [ ] No file exceeds 200 lines
- [ ] All functions have type hints and docstrings
- [ ] Error handling covers all failure modes
- [ ] Lazy loading for heavy dependencies
- [ ] Input validation for all tools

### Testing
- [ ] Unit tests for all public functions
- [ ] Integration tests with MCP client
- [ ] Performance tests for heavy operations
- [ ] Error scenario testing

### Documentation
- [ ] Clear README with setup instructions
- [ ] PLANNING.md with architecture decisions
- [ ] TASK.md with current status
- [ ] Function docstrings with examples
- [ ] Environment variable documentation

### Deployment
- [ ] Virtual environment with pinned dependencies
- [ ] Environment variables via .env
- [ ] Startup script with health checks
- [ ] Logging configuration
- [ ] Security review (no hardcoded secrets)

### Operations
- [ ] Health check tool implemented
- [ ] Monitoring/logging in place
- [ ] Graceful error handling
- [ ] Performance optimization applied
- [ ] Backup/recovery plan

---

## 🎉 Success Patterns

Your MCP server is production-ready when:

✅ **Fast Startup**: Server starts in <3 seconds  
✅ **Reliable**: Handles failures gracefully with fallbacks  
✅ **Clear**: Tools have obvious purposes and good documentation  
✅ **Modular**: Easy to add new tools without breaking existing ones  
✅ **Testable**: Comprehensive test suite catches regressions  
✅ **Maintainable**: Code is organized and well-documented  
✅ **Secure**: No hardcoded secrets, proper input validation  
✅ **Observable**: Good logging and health monitoring  

---

*These rules were distilled from building production MCP servers. Follow them to build robust, maintainable, and scalable MCP implementations.* 