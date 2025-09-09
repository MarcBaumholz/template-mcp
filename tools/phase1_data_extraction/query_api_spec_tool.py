"""
MCP Tool: Query API Specification
Handles querying API specifications from the RAG system
"""

import json
from pathlib import Path
from typing import Optional
from datetime import datetime
from .rag_core import OptimizedRAGSystem, get_rag_system
from .rag_querying import RAGQueryingMixin


class EnhancedRAGSystem(OptimizedRAGSystem, RAGQueryingMixin):
    """Enhanced RAG system with querying capabilities."""
    pass


def retrieve_from_rag(query: str, collection_name: str, limit: int = 5, score_threshold: float = 0.5, current_path: Optional[str] = None) -> str:
    """Enhanced RAG query with semantic re-ranking."""
    try:
        # Create enhanced RAG system instance
        rag = EnhancedRAGSystem()
        # Use simplified endpoint-first strategy (no re-ranking/boosts)
        results = rag.endpoint_first_query(query, collection_name, limit)
        
        if current_path:
            # Save as enhanced markdown
            markdown = f"# Enhanced RAG Query Results\n\n"
            markdown += f"**Query:** {query}\n"
            markdown += f"**Collection:** {collection_name}\n"
            markdown += f"**Results:** {len([r for r in results if 'error' not in r])}\n"
            markdown += f"**Score Threshold:** {score_threshold}\n\n"
            
            for i, result in enumerate(results, 1):
                if 'error' not in result:
                    markdown += f"## 📋 Result {i}\n"
                    markdown += f"**Score:** {result['score']:.3f} | **Semantic Score:** {result['semantic_score']:.3f}\n"
                    markdown += f"**Type:** {result['chunk_type']} | **Tokens:** {result['tokens']}\n\n"
                    markdown += f"```\n{result['text']}\n```\n\n"
                    
                    if result['metadata']:
                        markdown += f"**Metadata:** {json.dumps(result['metadata'], indent=2)}\n\n"
                else:
                    markdown += f"## ❌ Error\n\n{result['error']}\n\n"
            
            # Save file
            output_dir = Path(current_path)
            output_dir.mkdir(exist_ok=True)
                
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"enhanced_rag_query_{timestamp}.md"
            filepath = output_dir / filename
                
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(markdown)
            
            return f"✅ Enhanced query completed. Results saved to: {filepath}\n\n{markdown}"
        
        # Return JSON results if no current_path specified
        return json.dumps(results, indent=2)
        
    except Exception as e:
        return f"❌ Query error: {str(e)}"
