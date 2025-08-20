"""
Input parser for handling JSON and Markdown files for schema mapping.
Extracts field information from various input formats.
"""

import json
import re
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from .mapping_models import SourceField


class InputParser:
    """Parse various input formats for schema mapping."""
    
    def __init__(self):
        """Initialize input parser with logging."""
        self.logger = logging.getLogger("input_parser")
    
    def parse_json_file(self, json_path: str) -> List[SourceField]:
        """
        Parse a JSON file and extract field information.
        
        Args:
            json_path: Path to the JSON file
            
        Returns:
            List[SourceField]: List of extracted source fields
        """
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            fields = []
            self._extract_fields_recursive(data, fields, parent_path="")
            
            self.logger.info(f"Parsed {len(fields)} fields from {json_path}")
            return fields
            
        except Exception as e:
            self.logger.error(f"Failed to parse JSON file {json_path}: {e}")
            return []
    
    def parse_markdown_analysis(self, md_path: str) -> Dict[str, Any]:
        """
        Parse an analyze_api_fields.md file for field context.
        
        Args:
            md_path: Path to the markdown analysis file
            
        Returns:
            Dict[str, Any]: Parsed analysis data with field descriptions
        """
        try:
            with open(md_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            analysis = {
                'field_descriptions': {},
                'context': '',
                'business_logic': '',
                'api_purpose': ''
            }
            
            # Extract field descriptions from markdown sections
            field_sections = re.findall(
                r'#{1,3}\s*([^#\n]+)\n(.*?)(?=#{1,3}|\Z)', 
                content, 
                re.DOTALL
            )
            
            for title, section_content in field_sections:
                title = title.strip()
                
                # Look for field descriptions
                field_matches = re.findall(
                    r'\*\*([^*]+)\*\*[:\-]?\s*([^\n]+)', 
                    section_content
                )
                
                for field_name, description in field_matches:
                    clean_field = field_name.strip()
                    clean_desc = description.strip()
                    analysis['field_descriptions'][clean_field] = clean_desc
                
                # Extract context information
                if 'context' in title.lower() or 'purpose' in title.lower():
                    analysis['context'] += f"{title}: {section_content.strip()}\n"
                elif 'business' in title.lower() or 'logic' in title.lower():
                    analysis['business_logic'] += f"{title}: {section_content.strip()}\n"
                elif 'api' in title.lower() or 'endpoint' in title.lower():
                    analysis['api_purpose'] += f"{title}: {section_content.strip()}\n"
            
            self.logger.info(f"Parsed {len(analysis['field_descriptions'])} field descriptions from {md_path}")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Failed to parse markdown file {md_path}: {e}")
            return {'field_descriptions': {}, 'context': '', 'business_logic': '', 'api_purpose': ''}
    
    def merge_json_and_analysis(self, 
                              json_fields: List[SourceField], 
                              md_analysis: Dict[str, Any]) -> List[SourceField]:
        """
        Merge JSON field data with markdown analysis.
        
        Args:
            json_fields: List of fields from JSON
            md_analysis: Analysis data from markdown
            
        Returns:
            List[SourceField]: Enhanced fields with analysis data
        """
        field_descriptions = md_analysis.get('field_descriptions', {})
        global_context = md_analysis.get('context', '')
        
        enhanced_fields = []
        
        for field in json_fields:
            # Find matching description from markdown
            description = field.description or ""
            
            # Try exact match first
            if field.name in field_descriptions:
                description = field_descriptions[field.name]
            else:
                # Try partial matches
                for md_field, md_desc in field_descriptions.items():
                    if self._fields_match(field.name, md_field):
                        description = md_desc
                        break
            
            # Enhanced field with context
            enhanced_field = SourceField(
                name=field.name,
                path=field.path,
                type=field.type,
                description=description,
                context=f"{global_context}\n{field.context}".strip(),
                examples=field.examples
            )
            
            enhanced_fields.append(enhanced_field)
        
        return enhanced_fields
    
    def _extract_fields_recursive(self, 
                                data: Any, 
                                fields: List[SourceField], 
                                parent_path: str = "",
                                level: int = 0) -> None:
        """
        Recursively extract fields from nested data structures.
        
        Args:
            data: The data to extract from
            fields: List to append fields to
            parent_path: Current path in the data structure
            level: Current nesting level
        """
        if level > 10:  # Prevent infinite recursion
            return
        
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{parent_path}.{key}" if parent_path else key
                
                # Determine field type
                field_type = self._determine_type(value)
                
                # Create field entry
                field = SourceField(
                    name=key,
                    path=current_path,
                    type=field_type,
                    description="",  # Will be filled from markdown analysis
                    context=f"Found at path: {current_path}",
                    examples=[str(value)] if not isinstance(value, (dict, list)) else []
                )
                
                fields.append(field)
                
                # Recurse into nested structures
                if isinstance(value, (dict, list)):
                    self._extract_fields_recursive(value, fields, current_path, level + 1)
        
        elif isinstance(data, list) and data:
            # Handle arrays - analyze first element for structure
            first_item = data[0]
            if isinstance(first_item, dict):
                self._extract_fields_recursive(first_item, fields, parent_path, level + 1)
    
    def _determine_type(self, value: Any) -> str:
        """Determine the type of a field value."""
        if isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "number"
        elif isinstance(value, str):
            # Try to detect special string types
            if re.match(r'^\d{4}-\d{2}-\d{2}', value):
                return "date"
            elif re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
                return "email"
            elif re.match(r'^\+?[\d\s\-\(\)]+$', value):
                return "phone"
            elif re.match(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$', value):
                return "uuid"
            else:
                return "string"
        elif isinstance(value, list):
            return "array"
        elif isinstance(value, dict):
            return "object"
        else:
            return "unknown"
    
    def _fields_match(self, json_field: str, md_field: str) -> bool:
        """
        Check if two field names likely refer to the same field.
        
        Args:
            json_field: Field name from JSON
            md_field: Field name from markdown
            
        Returns:
            bool: True if fields likely match
        """
        # Normalize both field names
        json_norm = self._normalize_field_name(json_field)
        md_norm = self._normalize_field_name(md_field)
        
        # Exact match
        if json_norm == md_norm:
            return True
        
        # One contains the other
        if json_norm in md_norm or md_norm in json_norm:
            return True
        
        # Similar with common variations
        variations = [
            (json_norm.replace('_', ''), md_norm.replace('_', '')),
            (json_norm.replace('-', ''), md_norm.replace('-', '')),
            (json_norm.lower(), md_norm.lower())
        ]
        
        for j_var, m_var in variations:
            if j_var == m_var:
                return True
        
        return False
    
    def _normalize_field_name(self, field_name: str) -> str:
        """Normalize field name for comparison."""
        # Remove common prefixes/suffixes and normalize case
        normalized = field_name.lower().strip()
        normalized = re.sub(r'[_\-\.]', '', normalized)
        normalized = re.sub(r'^(field|attr|prop|data)', '', normalized)
        normalized = re.sub(r'(field|attr|prop|data)$', '', normalized)
        return normalized 