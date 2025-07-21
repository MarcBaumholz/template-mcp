"""
JSON processing tools for Template MCP Server
"""

import json
import pandas as pd
import os
import requests
from typing import Dict, Any, List
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def flatten_dict(data: Dict[Any, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """
    Flatten a nested dictionary.
    
    Args:
        data: Dictionary to flatten
        parent_key: Parent key for nested structure
        sep: Separator for nested keys
        
    Returns:
        Flattened dictionary
    """
    items = []
    
    for key, value in data.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        
        if isinstance(value, dict):
            items.extend(flatten_dict(value, new_key, sep=sep).items())
        elif isinstance(value, list):
            # Handle lists by creating indexed keys
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    items.extend(flatten_dict(item, f"{new_key}[{i}]", sep=sep).items())
                else:
                    items.append((f"{new_key}[{i}]", item))
        else:
            items.append((new_key, value))
    
    return dict(items)


def flatten_json_file(file_path: str, save_csv: bool = True, output_dir: str = None) -> str:
    """
    Loads a JSON file, flattens it, converts to DataFrame and optionally saves as CSV.
    
    Args:
        file_path: Path to the JSON file to process
        save_csv: Whether to save the flattened data as CSV (default: True)
        output_dir: Directory to save output files (default: same as input file)
        
    Returns:
        String with results summary and DataFrame preview
    """
    try:
        # Validate file exists
        if not os.path.exists(file_path):
            return f"Error: File not found at path '{file_path}'"
        
        # Validate it's a JSON file
        if not file_path.lower().endswith('.json'):
            return f"Error: File '{file_path}' is not a JSON file"
        
        # Load JSON data
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle different JSON structures
        flattened_data = []
        
        if isinstance(data, list):
            # JSON array - flatten each item
            for i, item in enumerate(data):
                if isinstance(item, dict):
                    flattened_item = flatten_dict(item)
                    flattened_item['_array_index'] = i  # Add index for reference
                    flattened_data.append(flattened_item)
                else:
                    # Simple array item
                    flattened_data.append({'_array_index': i, 'value': item})
        
        elif isinstance(data, dict):
            # Single JSON object - flatten it
            flattened_data.append(flatten_dict(data))
        
        else:
            # Simple value
            flattened_data.append({'value': data})
        
        # Convert to DataFrame
        if not flattened_data:
            return "Error: No data found in JSON file"
        
        df = pd.DataFrame(flattened_data)
        
        # Fill NaN values with empty strings for better readability
        df = df.fillna('')
        
        # Generate output summary
        result = f"JSON File: {file_path}\n"
        result += f"Original structure: {'Array' if isinstance(data, list) else 'Object'}\n"
        result += f"Flattened to DataFrame: {df.shape[0]} rows, {df.shape[1]} columns\n\n"
        
        # Show column names
        result += f"Columns ({len(df.columns)}):\n"
        for i, col in enumerate(df.columns, 1):
            result += f"  {i}. {col}\n"
        result += "\n"
        
        # Show first few rows
        preview_rows = min(5, len(df))
        result += f"First {preview_rows} rows:\n"
        result += df.head(preview_rows).to_string(index=False, max_cols=10)
        
        # Save to CSV if requested
        if save_csv:
            # Determine output path
            if output_dir is None:
                output_dir = os.path.dirname(file_path)
            
            # Create output filename
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_filename = f"{base_name}_flattened_{timestamp}.csv"
            csv_path = os.path.join(output_dir, csv_filename)
            
            # Save DataFrame as CSV
            df.to_csv(csv_path, index=False, encoding='utf-8')
            
            result += f"\n\nFlattened data saved to: {csv_path}"
            result += f"\nFile size: {round(os.path.getsize(csv_path) / 1024, 2)} KB"
        
        return result
        
    except json.JSONDecodeError as e:
        return f"Error: Invalid JSON format - {str(e)}"
    except Exception as e:
        return f"Error processing JSON file: {str(e)}"


def get_json_structure(file_path: str) -> str:
    """
    Analyze JSON file structure without flattening.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        String description of JSON structure
    """
    try:
        if not os.path.exists(file_path):
            return f"Error: File not found at path '{file_path}'"
        
        if not file_path.lower().endswith('.json'):
            return f"Error: File '{file_path}' is not a JSON file"
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        def analyze_structure(obj, level=0, max_level=3):
            """Recursively analyze JSON structure"""
            indent = "  " * level
            
            if level > max_level:
                return f"{indent}... (truncated - too deep)"
            
            if isinstance(obj, dict):
                result = f"{indent}Object ({len(obj)} keys):\n"
                for key, value in list(obj.items())[:5]:  # Show first 5 keys
                    result += f"{indent}  {key}: {analyze_structure(value, level+1, max_level)}\n"
                if len(obj) > 5:
                    result += f"{indent}  ... and {len(obj) - 5} more keys\n"
                return result.rstrip()
            
            elif isinstance(obj, list):
                if not obj:
                    return f"Empty array"
                result = f"Array ({len(obj)} items):\n"
                # Show structure of first item
                result += f"{indent}  [0]: {analyze_structure(obj[0], level+1, max_level)}"
                if len(obj) > 1:
                    result += f"\n{indent}  ... and {len(obj) - 1} more items"
                return result
            
            else:
                return f"{type(obj).__name__}: {str(obj)[:50]}{'...' if len(str(obj)) > 50 else ''}"
        
        result = f"JSON File: {file_path}\n"
        result += f"File size: {round(os.path.getsize(file_path) / 1024, 2)} KB\n\n"
        result += "Structure:\n"
        result += analyze_structure(data)
        
        return result
        
    except json.JSONDecodeError as e:
        return f"Error: Invalid JSON format - {str(e)}"
    except Exception as e:
        return f"Error analyzing JSON file: {str(e)}"


def filter_relevant_fields_with_llm(file_path: str, context: str = "business data", save_filtered: bool = True, output_dir: str = None) -> str:
    """
    Uses LLM via OpenRouter to identify relevant fields from flattened JSON and returns only those fields.
    
    Args:
        file_path: Path to the JSON file to process
        context: Context description to help LLM identify relevant fields (default: "business data")
        save_filtered: Whether to save the filtered data as CSV (default: True)
        output_dir: Directory to save output files (default: same as input file)
        
    Returns:
        String with results summary and filtered DataFrame preview
    """
    try:
        # First, flatten the JSON
        if not os.path.exists(file_path):
            return f"Error: File not found at path '{file_path}'"
        
        if not file_path.lower().endswith('.json'):
            return f"Error: File '{file_path}' is not a JSON file"
        
        # Load and flatten JSON data
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle different JSON structures
        flattened_data = []
        
        if isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, dict):
                    flattened_item = flatten_dict(item)
                    flattened_item['_array_index'] = i
                    flattened_data.append(flattened_item)
                else:
                    flattened_data.append({'_array_index': i, 'value': item})
        elif isinstance(data, dict):
            flattened_data.append(flatten_dict(data))
        else:
            flattened_data.append({'value': data})
        
        if not flattened_data:
            return "Error: No data found in JSON file"
        
        df = pd.DataFrame(flattened_data).fillna('')
        
        # Get field names and sample values for LLM analysis
        field_info = []
        for col in df.columns:
            sample_values = df[col].dropna().head(3).tolist()
            field_info.append({
                'field_name': col,
                'sample_values': sample_values
            })
        
        # Call OpenRouter LLM to identify relevant fields
        rag_analysis = _identify_relevant_fields_with_llm(field_info, context)
        
        if not rag_analysis:
            return "Error: Could not identify relevant fields or LLM request failed"
        
        # Extract field names and RAG metadata
        if isinstance(rag_analysis, dict):
            # Use original field names for filtering but clean names for display
            relevant_fields = []
            rag_metadata = []
            
            for field_meta in rag_analysis.get('relevant_fields', []):
                original_name = field_meta.get('original_field_name')
                clean_name = field_meta.get('field_name')
                
                if original_name and original_name in df.columns:
                    relevant_fields.append(original_name)
                    # Update metadata to show clean name for display
                    field_meta['display_name'] = clean_name
                    rag_metadata.append(field_meta)
        else:
            # Fallback for simple list format
            relevant_fields = rag_analysis
            rag_metadata = []
        
        # Filter DataFrame to only include relevant fields
        available_fields = [field for field in relevant_fields if field in df.columns]
        
        if not available_fields:
            return "Error: None of the identified relevant fields exist in the data"
        
        filtered_df = df[available_fields]
        
        # Generate output summary with clean names
        result = f"JSON File: {file_path}\n"
        result += f"Original fields: {len(df.columns)}\n"
        result += f"Relevant fields identified: {len(available_fields)}\n"
        result += f"Context used: {context}\n\n"
        
        result += f"Relevant business variables ({len(available_fields)}):\n"
        for i, field in enumerate(available_fields, 1):
            clean_name = _extract_clean_field_name(field)
            result += f"  {i}. {clean_name} (from: {field})\n"
        result += "\n"
        
        # Show RAG metadata if available
        if rag_metadata:
            result += "Business Variable Analysis:\n"
            for field_meta in rag_metadata:
                display_name = field_meta.get('display_name', field_meta['field_name'])
                result += f"• {display_name}\n"
                result += f"  Purpose: {field_meta.get('business_purpose', 'N/A')}\n"
                result += f"  Type: {field_meta.get('data_type', 'N/A')}\n"
                result += f"  RAG Keywords: {', '.join(field_meta.get('rag_keywords', []))}\n\n"
        
        # Show filtered data preview
        preview_rows = min(5, len(filtered_df))
        result += f"Filtered data preview ({preview_rows} rows):\n"
        result += filtered_df.head(preview_rows).to_string(index=False, max_cols=10)
        
        # Save filtered data if requested
        if save_filtered:
            if output_dir is None:
                output_dir = os.path.dirname(file_path)
            
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_filename = f"{base_name}_relevant_fields_{timestamp}.csv"
            csv_path = os.path.join(output_dir, csv_filename)
            
            # Save filtered CSV data
            filtered_df.to_csv(csv_path, index=False, encoding='utf-8')
            
            result += f"\n\nFiltered data saved to: {csv_path}"
            result += f"\nFile size: {round(os.path.getsize(csv_path) / 1024, 2)} KB"
            
            # Save the LLM analysis results to a JSON file
            if rag_metadata:
                # Create a filename for the analysis results
                analysis_filename = f"{base_name}_llm_analysis_{timestamp}.json"
                analysis_path = os.path.join(output_dir, analysis_filename)
                
                # Extract the clean field names from the metadata
                clean_field_names = [field.get('display_name', field.get('field_name')) for field in rag_metadata]

                # Create the output data in the format you specified
                output_data = {
                    "context_topic": context,
                    "relevant_fields": clean_field_names
                }

                # Write the new JSON file
                with open(analysis_path, 'w', encoding='utf-8') as f:
                    json.dump(output_data, f, indent=2, ensure_ascii=False)
                
                result += f"\n\nLLM analysis saved to: {analysis_path}"
                result += f"\nFile size: {round(os.path.getsize(analysis_path) / 1024, 2)} KB"
        
        return result
        
    except Exception as e:
        return f"Error processing JSON file with LLM filtering: {str(e)}"


def _identify_relevant_fields_with_llm(field_info: List[Dict], context: str) -> List[str]:
    """
    Internal function to call OpenRouter LLM for field relevance analysis.
    
    Args:
        field_info: List of dictionaries with field names and sample values
        context: Context description for relevance analysis
        
    Returns:
        List of relevant field names
    """
    try:
        api_key = os.getenv('OPENROUTER_API_KEY')
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not set")
        
        # Get model name from environment, default to free DeepSeek model
        model_name = os.getenv('OPENROUTER_MODEL', 'deepseek/deepseek-chat:free')
        
        # Prepare field information for LLM - extract clean variable names
        fields_text = "\n".join([
            f"- {_extract_clean_field_name(field['field_name'])}: {field['sample_values']}"
            for field in field_info
        ])
        
        prompt = f"""Analyze the following business variables and identify which ones are most relevant for {context}.

These are the actual business variables extracted from a JSON structure:
{fields_text}

Focus ONLY on the core business variables that matter for {context}. Ignore technical metadata, wrapper fields, and infrastructure data.

Look for:
1. Core business entities (employee_id, user_id, customer_id)
2. Business dates and times (start_date, end_date, created_at)
3. Business status and categories (status, reason, type)
4. Business amounts and quantities
5. Business flags and settings (is_active, enabled, etc.)
6. Business identifiers (id, code, number)
7. Business names and descriptions (name, description, title)
8. Business references and links (url, link, href)‚
9. Paths and events or event types (path, event, event_type)
Return a JSON object with ONLY the clean variable names (not full paths):

{{
  "relevant_fields": [
    {{
      "field_name": "clean_variable_name",
      "business_purpose": "what this variable represents in business terms",
      "data_type": "string|number|boolean|date",
      "rag_keywords": ["business_term1", "business_term2", "business_term3"]
    }}
  ]
}}

Example: If you see "body.input.data.employee_id", return just "employee_id" as the field_name.
Focus on business meaning, not technical structure."""
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': model_name,
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'temperature': 0.1,
            'max_tokens': 4000  # Increased max_tokens
        }
        
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers=headers,
            json=payload,
            timeout=45  # Increased timeout
        )
        
        # Add detailed logging
        print(f"LLM API Status Code: {response.status_code}")
        if response.status_code != 200:
            print(f"LLM API Error Response: {response.text}")
            response.raise_for_status() # Raise an exception for bad status
        
        result = response.json()
        print(f"LLM API Raw Response: {json.dumps(result, indent=2)}")

        content = result['choices'][0]['message']['content'].strip()
        print(f"Extracted LLM Content: {content}")
        
        # Parse the JSON response
        try:
            # Remove any markdown formatting if present
            if content.startswith('```'):
                # Find the actual JSON content between code blocks
                lines = content.split('\n')
                json_lines = []
                in_json = False
                
                for line in lines:
                    if line.strip().startswith('```json') or line.strip().startswith('```'):
                        in_json = not in_json
                        continue
                    if in_json:
                        json_lines.append(line)
                
                content = '\n'.join(json_lines).strip()
            
            rag_analysis = json.loads(content)
            
            if isinstance(rag_analysis, dict) and 'relevant_fields' in rag_analysis:
                # Map clean field names back to original field names for filtering
                clean_to_original = {}
                for field in field_info:
                    clean_name = _extract_clean_field_name(field['field_name'])
                    clean_to_original[clean_name] = field['field_name']
                
                # Update the field names in the analysis to use original names for filtering
                for field_meta in rag_analysis['relevant_fields']:
                    clean_name = field_meta['field_name']
                    if clean_name in clean_to_original:
                        field_meta['original_field_name'] = clean_to_original[clean_name]
                        # Keep the clean name for display but add original for filtering
                
                return rag_analysis
            else:
                raise ValueError("LLM response is not in the expected format")
                
        except json.JSONDecodeError as e:
            print(f"JSON Parse Error: {e}. Content was: {content}")
            # Fallback: try to extract field names from text response
            import re
            field_names = re.findall(r'"([^"]+)"', content)
            return field_names if field_names else []
        
    except requests.exceptions.RequestException as e:
        print(f"Error calling LLM API: {str(e)}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred in LLM analysis: {str(e)}")
        return []


def _extract_clean_field_name(full_field_name: str) -> str:
    """
    Extract the clean business variable name from a full JSON path.
    
    Args:
        full_field_name: Full field path like "body.input.data.employee_id"
        
    Returns:
        Clean variable name like "employee_id"
    """
    # Remove common technical prefixes and get the last meaningful part
    parts = full_field_name.split('.')
    
    # Skip common wrapper parts
    skip_parts = {'body', 'input', 'data', 'payload', 'request', 'response', 'params', 'headers'}
    
    # Find the last meaningful part
    for part in reversed(parts):
        # Remove array indices like [0]
        clean_part = part.split('[')[0]
        if clean_part and clean_part.lower() not in skip_parts:
            return clean_part
    
    # Fallback to the last part if nothing meaningful found
    return parts[-1].split('[')[0] if parts else full_field_name