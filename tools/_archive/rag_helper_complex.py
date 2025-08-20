"""
RAG Helper for Schema Mapping

This module provides structured RAG operations specifically for schema mapping.
It returns structured data instead of formatted strings.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from .rag_tools import get_rag_system


class RAGHelper:
    """Helper class for structured RAG operations."""
    
    def __init__(self, debug_output_dir: Optional[str] = None):
        """
        Initialize RAG helper.
        
        Args:
            debug_output_dir: Directory to save debug files
        """
        self.logger = logging.getLogger("rag_helper")
        self.debug_dir = Path(debug_output_dir) if debug_output_dir else None
        
        if self.debug_dir:
            self.debug_dir.mkdir(exist_ok=True)
            self.logger.info(f"Debug output directory: {self.debug_dir}")
    
    def get_structured_results(self, 
                             query: str, 
                             collection_name: str, 
                             limit: int = 5, 
                             score_threshold: float = 0.5) -> List[Dict[str, Any]]:
        """
        Get structured RAG results for schema mapping.
        
        Args:
            query: Search query
            collection_name: RAG collection name
            limit: Maximum results to return
            score_threshold: Minimum score threshold
            
        Returns:
            List[Dict]: Structured results with text, score, and metadata
        """
        try:
            # Get RAG system and query directly
            rag = get_rag_system()
            results = rag.query(query, collection_name, limit, score_threshold)
            
            # Save debug information if debug dir is set
            if self.debug_dir:
                self._save_debug_file("rag_query", {
                    "query": query,
                    "collection": collection_name,
                    "limit": limit,
                    "score_threshold": score_threshold,
                    "results_count": len(results),
                    "results": results
                })
            
            # Filter out error results
            valid_results = [r for r in results if 'error' not in r]
            
            self.logger.info(f"RAG query '{query}' returned {len(valid_results)} valid results")
            return valid_results
            
        except Exception as e:
            self.logger.error(f"RAG query failed: {e}")
            if self.debug_dir:
                self._save_debug_file("rag_error", {
                    "query": query,
                    "error": str(e)
                })
            return []
    
    def search_field_matches(self, 
                           field_name: str, 
                           field_type: Optional[str] = None,
                           field_description: Optional[str] = None,
                           collection_name: str = "test_api_fixed",
                           max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search for field matches using optimized queries.
        
        Args:
            field_name: Name of the field to search for
            field_type: Optional field type
            field_description: Optional field description
            collection_name: RAG collection to search
            max_results: Maximum results to return
            
        Returns:
            List of potential field matches with enhanced scoring
        """
        # Create multiple search queries with different strategies
        queries = []
        
        # Primary query: exact field name
        queries.append({
            "query": f"field {field_name} property parameter",
            "weight": 1.0,
            "strategy": "exact_name"
        })
        
        # Secondary query: field with type
        if field_type:
            queries.append({
                "query": f"{field_name} {field_type} type",
                "weight": 0.8,
                "strategy": "name_with_type"
            })
        
        # Tertiary query: description-based
        if field_description:
            queries.append({
                "query": f"{field_name} {field_description}",
                "weight": 0.6,
                "strategy": "name_with_description"
            })
        
        # Quaternary query: semantic variations
        semantic_terms = self._get_semantic_variations(field_name)
        if semantic_terms:
            queries.append({
                "query": f"{field_name} {' '.join(semantic_terms)}",
                "weight": 0.7,
                "strategy": "semantic_expansion"
            })
        
        # Execute all queries and combine results
        all_results = []
        
        for query_info in queries:
            results = self.get_structured_results(
                query_info["query"], 
                collection_name, 
                limit=max_results,
                score_threshold=0.3
            )
            
            # Add query strategy info to results
            for result in results:
                result["query_strategy"] = query_info["strategy"]
                result["query_weight"] = query_info["weight"]
                result["original_query"] = query_info["query"]
                # Adjust score with query weight
                result["weighted_score"] = result["score"] * query_info["weight"]
            
            all_results.extend(results)
        
        # Remove duplicates and sort by weighted score
        unique_results = self._deduplicate_results(all_results)
        sorted_results = sorted(unique_results, key=lambda x: x["weighted_score"], reverse=True)
        
        # Save debug info
        if self.debug_dir:
            self._save_debug_file("field_search", {
                "field_name": field_name,
                "field_type": field_type,
                "field_description": field_description,
                "queries_executed": len(queries),
                "total_results": len(all_results),
                "unique_results": len(unique_results),
                "top_results": sorted_results[:max_results]
            })
        
        return sorted_results[:max_results]
    
    def _get_semantic_variations(self, field_name: str) -> List[str]:
        """Get semantic variations for a field name."""
        variations = []
        
        # Common synonyms mapping
        synonyms = {
            'id': ['identifier', 'key', 'uuid', 'number'],
            'user': ['employee', 'person', 'member', 'staff'],
            'employee': ['user', 'staff', 'worker', 'person'],
            'email': ['mail', 'e_mail', 'address'],
            'phone': ['telephone', 'mobile', 'contact'],
            'name': ['title', 'label', 'description'],
            'date': ['time', 'timestamp', 'created', 'updated'],
            'status': ['state', 'active', 'enabled'],
            'department': ['dept', 'division', 'team', 'group']
        }
        
        field_lower = field_name.lower()
        for key, values in synonyms.items():
            if key in field_lower:
                variations.extend(values)
            elif any(v in field_lower for v in values):
                variations.append(key)
        
        return list(set(variations))[:3]  # Limit to top 3 variations
    
    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """Remove duplicate results based on text content."""
        seen_texts = set()
        unique_results = []
        
        for result in results:
            text = result.get("text", "")
            if text not in seen_texts:
                seen_texts.add(text)
                unique_results.append(result)
            else:
                # If we've seen this text, keep the one with higher score
                existing_idx = next(
                    (i for i, r in enumerate(unique_results) if r.get("text") == text), 
                    None
                )
                if existing_idx is not None and result.get("weighted_score", 0) > unique_results[existing_idx].get("weighted_score", 0):
                    unique_results[existing_idx] = result
        
        return unique_results
    
    def _save_debug_file(self, operation: str, data: Dict) -> None:
        """Save debug information to file."""
        if not self.debug_dir:
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{operation}_{timestamp}.json"
            filepath = self.debug_dir / filename
            
            debug_data = {
                "timestamp": timestamp,
                "operation": operation,
                "data": data
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(debug_data, f, indent=2, ensure_ascii=False)
            
            self.logger.debug(f"Debug file saved: {filepath}")
            
        except Exception as e:
            self.logger.warning(f"Failed to save debug file: {e}")


# Convenience functions for direct use
def get_field_matches(field_name: str, 
                     field_type: Optional[str] = None,
                     field_description: Optional[str] = None,
                     collection_name: str = "test_api_fixed",
                     debug_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Convenience function to get field matches.
    
    Args:
        field_name: Name of the field to search for
        field_type: Optional field type
        field_description: Optional field description
        collection_name: RAG collection to search
        debug_dir: Optional debug directory
        
    Returns:
        List of potential field matches
    """
    helper = RAGHelper(debug_dir)
    return helper.search_field_matches(
        field_name, field_type, field_description, collection_name
    ) 