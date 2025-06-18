"""
LLM Client for RAG Analysis using OpenRouter

This module provides a client for interacting with language models
via OpenRouter API for analysis and synthesis tasks.
"""

import os
from typing import Optional

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
        return "Error: OPENROUTER_API_KEY environment variable not set. Please add your OpenRouter API key to .env file."
    
    # Use default model if not specified
    if model is None:
        model = os.getenv('OPENROUTER_MODEL', 'deepseek/deepseek-r1-0528-qwen3-8b:free')
    
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
        return f"Error getting LLM response from OpenRouter: {str(e)}"


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