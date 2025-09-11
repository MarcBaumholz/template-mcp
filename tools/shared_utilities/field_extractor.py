"""
Flexible Field Extraction System
Provides domain-agnostic field extraction without hardcoded values
"""

import json
import re
from typing import Dict, Any, List, Set, Optional, Tuple
from dataclasses import dataclass
from .config_manager import get_config, FieldExtractionConfig


@dataclass
class FieldExtractionResult:
    """Result of field extraction"""
    fields: List[str]
    metadata: Dict[str, Any]
    confidence_score: float
    extraction_method: str


class FieldExtractor:
    """Flexible field extractor that adapts to any data structure"""
    
    def __init__(self, config: Optional[FieldExtractionConfig] = None):
        self.config = config or get_config().field_extraction
        self._field_patterns = self._initialize_field_patterns()
    
    def _initialize_field_patterns(self) -> Dict[str, List[str]]:
        """Initialize flexible field patterns for different data types"""
        return {
            "identifiers": [
                "id", "uuid", "key", "code", "reference", "ref", "identifier",
                "primary_key", "external_id", "remote_id", "unique_id", "productid",
                "product_id", "employeeid", "employee_id", "customerid", "customer_id"
            ],
            "timestamps": [
                "created_at", "updated_at", "timestamp", "date", "time",
                "created_date", "updated_date", "modified_at", "last_modified",
                "created_time", "updated_time", "modified_time"
            ],
            "status_fields": [
                "status", "state", "condition", "phase", "stage", "level",
                "active", "enabled", "disabled", "approved", "pending", "rejected"
            ],
            "amount_fields": [
                "amount", "value", "price", "cost", "total", "sum", "quantity",
                "count", "number", "rate", "fee", "charge", "balance", "stock",
                "inventory", "reserved", "available"
            ],
            "text_fields": [
                "name", "title", "description", "comment", "note", "message",
                "content", "text", "label", "caption", "summary", "productname",
                "product_name", "firstname", "first_name", "lastname", "last_name",
                "category", "brand", "sku"
            ],
            "contact_fields": [
                "email", "phone", "address", "contact", "location", "city",
                "country", "zip", "postal_code", "street", "region"
            ],
            "relationship_fields": [
                "user_id", "customer_id", "order_id", "product_id", "account_id",
                "parent_id", "child_id", "related_id", "associated_id"
            ]
        }
    
    def extract_fields(self, json_data: Dict[str, Any]) -> FieldExtractionResult:
        """Extract fields from JSON data using flexible patterns"""
        all_fields = self._extract_all_fields(json_data)
        filtered_fields = self._filter_fields(all_fields)
        categorized_fields = self._categorize_fields(filtered_fields)
        
        return FieldExtractionResult(
            fields=filtered_fields,
            metadata={
                "total_fields": len(all_fields),
                "filtered_fields": len(filtered_fields),
                "categories": categorized_fields,
                "extraction_config": {
                    "max_depth": self.config.max_depth,
                    "exclude_fields": self.config.exclude_fields,
                    "include_patterns": self.config.include_patterns
                }
            },
            confidence_score=self._calculate_confidence_score(filtered_fields, categorized_fields),
            extraction_method="flexible_pattern_matching"
        )
    
    def _extract_all_fields(self, json_data: Dict[str, Any]) -> List[str]:
        """Extract all fields from JSON structure"""
        fields = []
        
        def extract_fields_recursive(obj, prefix="", current_depth=0):
            if current_depth >= self.config.max_depth:
                return
            
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{prefix}.{key}" if prefix else key
                    
                    # Skip excluded fields at top level
                    if key in self.config.exclude_fields and current_depth == 0:
                        continue
                    
                    fields.append(current_path)
                    
                    # Recursively extract nested fields
                    if isinstance(value, (dict, list)) and current_depth < self.config.max_depth - 1:
                        extract_fields_recursive(value, current_path, current_depth + 1)
            
            elif isinstance(obj, list) and obj:
                # For arrays, extract fields from the first item if it's a dict
                if isinstance(obj[0], dict):
                    extract_fields_recursive(obj[0], prefix, current_depth)
        
        extract_fields_recursive(json_data)
        return fields
    
    def _filter_fields(self, fields: List[str]) -> List[str]:
        """Filter fields based on include patterns and business relevance"""
        filtered = []
        
        for field in fields:
            # Check if field matches include patterns
            if self._matches_include_patterns(field):
                filtered.append(field)
                continue
            
            # Check if field contains business-relevant patterns
            if self._is_business_relevant(field):
                filtered.append(field)
        
        return filtered
    
    def _matches_include_patterns(self, field: str) -> bool:
        """Check if field matches include patterns"""
        for pattern in self.config.include_patterns:
            if re.match(pattern.replace("*", ".*"), field):
                return True
        return False
    
    def _is_business_relevant(self, field: str) -> bool:
        """Check if field is business relevant based on patterns"""
        field_name = field.split(".")[-1].lower()
        
        # Check against all field patterns
        for pattern_type, patterns in self._field_patterns.items():
            if any(pattern in field_name for pattern in patterns):
                return True
        
        # Check for common business field patterns
        business_patterns = [
            r".*_id$",  # Foreign keys
            r".*_at$",  # Timestamps
            r".*_by$",  # User references
            r".*_type$",  # Type fields
            r".*_status$",  # Status fields
            r".*_name$",  # Name fields
            r".*_code$",  # Code fields
        ]
        
        for pattern in business_patterns:
            if re.match(pattern, field_name):
                return True
        
        return False
    
    def _categorize_fields(self, fields: List[str]) -> Dict[str, List[str]]:
        """Categorize fields by type"""
        categories = {category: [] for category in self._field_patterns.keys()}
        categories["other"] = []
        
        for field in fields:
            field_name = field.split(".")[-1].lower()
            categorized = False
            
            for category, patterns in self._field_patterns.items():
                if any(pattern in field_name for pattern in patterns):
                    categories[category].append(field)
                    categorized = True
                    break
            
            if not categorized:
                categories["other"].append(field)
        
        return categories
    
    def _calculate_confidence_score(self, fields: List[str], categories: Dict[str, List[str]]) -> float:
        """Calculate confidence score for field extraction"""
        if not fields:
            return 0.0
        
        # Base score from field count
        base_score = min(len(fields) / 20.0, 1.0)  # Normalize to 0-1
        
        # Bonus for having diverse categories
        category_bonus = min(len([cat for cat, fields in categories.items() if fields]) / 5.0, 0.3)
        
        # Bonus for having common business fields
        business_field_bonus = 0.0
        for field in fields:
            field_name = field.split(".")[-1].lower()
            if field_name in ["id", "name", "status", "created_at", "updated_at"]:
                business_field_bonus += 0.1
        
        business_field_bonus = min(business_field_bonus, 0.2)
        
        return min(base_score + category_bonus + business_field_bonus, 1.0)
    
    def get_field_suggestions(self, field_name: str) -> List[str]:
        """Get suggestions for field names based on patterns"""
        suggestions = []
        field_lower = field_name.lower()
        
        for category, patterns in self._field_patterns.items():
            for pattern in patterns:
                if pattern in field_lower:
                    suggestions.extend(patterns)
                    break
        
        return list(set(suggestions))
    
    def analyze_field_relationships(self, fields: List[str]) -> Dict[str, List[str]]:
        """Analyze relationships between fields"""
        relationships = {}
        
        for field in fields:
            field_name = field.split(".")[-1].lower()
            
            # Find related fields
            related = []
            for other_field in fields:
                if field == other_field:
                    continue
                
                other_name = other_field.split(".")[-1].lower()
                
                # Check for common prefixes/suffixes
                if (field_name.endswith("_id") and other_name.startswith(field_name[:-3])) or \
                   (other_name.endswith("_id") and field_name.startswith(other_name[:-3])):
                    related.append(other_field)
            
            if related:
                relationships[field] = related
        
        return relationships


def extract_fields_from_json(json_data: Dict[str, Any], 
                           config: Optional[FieldExtractionConfig] = None) -> FieldExtractionResult:
    """Convenience function to extract fields from JSON data"""
    extractor = FieldExtractor(config)
    return extractor.extract_fields(json_data)


def get_field_categories(fields: List[str]) -> Dict[str, List[str]]:
    """Get field categories for a list of fields"""
    extractor = FieldExtractor()
    return extractor._categorize_fields(fields)
