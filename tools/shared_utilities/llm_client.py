"""
LLM Client for RAG Analysis using OpenRouter

This module provides a client for interacting with language models
via OpenRouter API for analysis and synthesis tasks.
"""

import os
from typing import Optional
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(os.path.dirname(script_dir), '.env')  # Go up one level to connector-mcp directory
    load_dotenv(env_path)
except ImportError:
    pass  # dotenv not available, environment variables should be set manually

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Import request counter with fallback
try:
    from .request_counter import track_request
except ImportError:
    # Fallback for when imported as standalone module
    try:
        from request_counter import track_request
    except ImportError:
        # Final fallback - create a dummy function
        def track_request(tool_name: str, model: str, tokens: int):
            """Dummy tracking function when request_counter is not available"""
            pass


# --- Function to read the system prompt ---
def get_system_prompt():
    """Reads the system prompt from a markdown file."""
    try:
        # Assumes the prompt file is in the parent directory of 'tools'
        prompt_path = Path(__file__).parent.parent / "system_prompt.md"
        if prompt_path.exists():
            return prompt_path.read_text()
        return ""  # Return empty string if not found
    except Exception:
        return "" # Return empty on any error


def get_llm_response(prompt: str, model: str = None, max_tokens: int = 2000, tool_name: str = "llm_client") -> str:
    """
    Sends a prompt to the LLM and gets a response, prepending the system prompt.
    """
    if not OPENAI_AVAILABLE:
        return "Error: OpenAI library not available. Please install it with `pip install openai`."

    # Use the new API key
    api_key = "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"
    
    if not model:
        model = os.getenv('OPENROUTER_MODEL', 'deepseek/deepseek-chat')
    
    # --- Get the system prompt ---
    system_prompt = get_system_prompt()
    if not system_prompt:
        # Fallback to a default system prompt if the file is missing or empty
        system_prompt = "You are a helpful assistant that analyzes API documentation and data. Provide clear, structured, and actionable insights. Keep responses concise but comprehensive."

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
                    "content": system_prompt
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
        
        # Track the request
        tokens_used = response.usage.total_tokens if hasattr(response, 'usage') and response.usage else 0
        track_request(tool_name, model, tokens_used)
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        # Still track the request even if it failed
        track_request(tool_name, model, 0)
        print(f"Warning: OpenRouter API error, falling back to mock response: {e}")
        return str(e)


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
    
    return get_llm_response(prompt, tool_name="analyze_json_with_llm")


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
    
    return get_llm_response(prompt, tool_name="enhance_field_analysis")


def test_llm_connection() -> str:
    """
    Test the LLM connection and configuration.
    
    Returns:
        Status message about the connection
    """
    try:
        response = get_llm_response("Hello! Please respond with 'Connection successful' to confirm the API is working.", tool_name="test_llm_connection")
        if "error" in response.lower():
            return f"❌ LLM Connection Test Failed: {response}"
        else:
            return f"✅ LLM Connection Test Successful: {response[:100]}..."
    except Exception as e:
        return f"❌ LLM Connection Test Error: {str(e)}"