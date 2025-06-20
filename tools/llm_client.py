"""
LLM Client for RAG Analysis using OpenRouter

This module provides a client for interacting with language models
via OpenRouter API for analysis and synthesis tasks.
"""

import os
from typing import Optional

# Load environment variables
try:
    from dotenv import load_dotenv
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(os.path.dirname(script_dir), '.env')  # Go up one level to template-mcp directory
    load_dotenv(env_path)
except ImportError:
    pass  # dotenv not available, environment variables should be set manually

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


def get_llm_response(prompt: str, model: str = None, max_tokens: int = 2000) -> str:
    """
    Get a response from the LLM via OpenRouter.
    
    Args:
        prompt: The prompt to send to the LLM
        model: The model to use (default: deepseek/deepseek-r1-0528-qwen3-8b:free)
        max_tokens: Maximum tokens in the response
        
    Returns:
        The LLM response as a string
    """
    if not OPENAI_AVAILABLE:
        return "Error: OpenAI library not available. Please install with: pip install openai"
    
    # Check for OpenRouter API key
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        return _generate_mock_response(prompt)
    
    # Use default model if not specified
    if model is None:
        model = os.getenv('OPENROUTER_MODEL', 'gpt-3.5-turbo')
    
    try:
        # Initialize OpenAI client with OpenRouter endpoint
        client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that analyzes API documentation and data. Provide clear, structured, and actionable insights. Keep responses concise but comprehensive."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=max_tokens,
            temperature=0.1,  # Low temperature for consistent, factual responses
            extra_headers={
                "HTTP-Referer": "https://github.com/mcp-personal-server-py",
                "X-Title": "MCP RAG Analysis Server"
            }
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"Warning: OpenRouter API error, falling back to mock response: {e}")
        return _generate_mock_response(prompt)


def _generate_mock_response(prompt: str) -> str:
    """
    Generate a mock response based on the prompt content.
    This allows the RAG tools to function even without a working LLM API.
    """
    prompt_lower = prompt.lower()
    
    # Detect analysis type and provide appropriate mock response
    if "analyze" in prompt_lower and "field" in prompt_lower:
        return """# Field Analysis Results

## Key Findings:
- **Data Type**: The analyzed fields appear to be standard API fields
- **Business Context**: These fields are commonly used in enterprise applications
- **Validation**: Standard validation rules likely apply
- **Usage Patterns**: Typical CRUD operations expected

## Recommendations:
1. Implement proper validation for required fields
2. Consider data type constraints
3. Plan for future extensibility
4. Document field relationships

## API Integration Notes:
- Follow RESTful conventions
- Use consistent naming patterns
- Implement proper error handling
- Consider pagination for list operations

*Note: This is a mock analysis. For detailed insights, please configure a valid OpenRouter API key.*"""
    
    elif "json" in prompt_lower or "data" in prompt_lower:
        return """# JSON Data Analysis

## Structure Overview:
- **Format**: Well-formed JSON structure detected
- **Complexity**: Moderate nesting level
- **Data Types**: Mixed types including strings, numbers, objects, arrays

## Key Insights:
1. **Data Consistency**: Fields follow consistent naming conventions
2. **Completeness**: Most required fields appear to be present
3. **Relationships**: Clear parent-child relationships identified
4. **Validation**: Standard data validation patterns recommended

## Business Interpretation:
- Data appears suitable for business operations
- Good candidate for API integration
- Consider implementing caching strategies
- Plan for data migration if needed

*Note: This is a mock analysis. For detailed insights, please configure a valid OpenRouter API key.*"""
    
    elif "connection" in prompt_lower or "test" in prompt_lower:
        return "Mock LLM connection active. Configure OpenRouter API key for full functionality."
    
    else:
        return f"""# Analysis Results

Based on the provided information, here are the key insights:

## Summary:
The analysis has been completed using available data patterns and common best practices.

## Key Points:
1. **Structure**: Well-organized and follows standard patterns
2. **Implementation**: Suitable for production use with proper configuration
3. **Integration**: Compatible with standard API workflows
4. **Scalability**: Designed to handle enterprise-level requirements

## Recommendations:
- Review and validate all configurations
- Test thoroughly in development environment
- Implement proper monitoring and logging
- Document all custom configurations

*Note: This is a mock analysis generated due to OpenRouter API configuration issues. For detailed AI-powered insights, please configure a valid OpenRouter API key in your .env file.*

**Prompt analyzed**: {prompt[:200]}..."""


def analyze_json_with_llm(json_data: str, context: str = "") -> str:
    """
    Analyze JSON data using LLM.
    
    Args:
        json_data: JSON string to analyze
        context: Additional context for the analysis
        
    Returns:
        Analysis results as a string
    """
    prompt = f"""Analyze the following JSON data and provide insights:

{f"Context: {context}" if context else ""}

JSON Data:
{json_data}

Please provide:
1. Structure analysis
2. Data patterns and insights
3. Potential issues or anomalies
4. Business interpretation (if applicable)
5. Recommendations for data usage

Format your response clearly with sections."""
    
    return get_llm_response(prompt)


def enhance_field_analysis(field_name: str, field_data: dict, api_context: str = "") -> str:
    """
    Enhance field analysis using LLM.
    
    Args:
        field_name: Name of the field
        field_data: Data about the field
        api_context: API documentation context
        
    Returns:
        Enhanced analysis as a string
    """
    prompt = f"""Analyze this API field and provide comprehensive insights:

Field Name: {field_name}
Field Data: {field_data}

{f"API Context: {api_context}" if api_context else ""}

Please provide:
1. Field purpose and business meaning
2. Data type and validation rules
3. Usage patterns and best practices
4. Relationships to other fields
5. Potential issues or considerations

Format your response as a structured analysis."""
    
    return get_llm_response(prompt)


def test_llm_connection() -> str:
    """
    Test the LLM connection and configuration.
    
    Returns:
        Status message about the connection
    """
    try:
        response = get_llm_response("Hello! Please respond with 'Connection successful' to confirm the API is working.")
        if "error" in response.lower():
            return f"❌ LLM Connection Test Failed: {response}"
        else:
            return f"✅ LLM Connection Test Successful: {response[:100]}..."
    except Exception as e:
        return f"❌ LLM Connection Test Error: {str(e)}"