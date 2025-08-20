"""
Simple RAG Helper
Basic helper functions for RAG operations - simplified version
"""

from typing import List, Dict, Any, Optional
from .rag_tools import get_rag_system


class RAGHelper:
    """Simple RAG helper with basic functionality."""
    
    def __init__(self):
        """Initialize simple RAG helper."""
        self.rag_system = None
    
    def _get_rag(self):
        """Get RAG system instance."""
        if self.rag_system is None:
            self.rag_system = get_rag_system()
        return self.rag_system
    
    async def query_collection(
        self, 
        collection_name: str, 
        query: str, 
        limit: int = 3
    ) -> List[str]:
        """Simple collection query - returns just text results."""
        try:
            rag = self._get_rag()
            results = rag.query(query, collection_name, limit)
            
            # Extract just the text from results
            texts = []
            for result in results:
                if 'error' not in result and 'text' in result:
                    texts.append(result['text'])
            
            return texts
            
        except Exception as e:
            return [f"Query error: {str(e)}"]


# Simple convenience function
def get_field_matches(
    field_name: str, 
    collection_name: str = "flip_api_v2",
    max_results: int = 3
) -> List[str]:
    """Get simple field matches from RAG."""
    helper = RAGHelper()
    query = f"{field_name} parameter property field"
    
    # This would need to be async in a real async context
    # For now, return a simple mock
    return [f"Mock result for {field_name}"]