"""
MCP Tool: Upload API Specification
Handles uploading OpenAPI specifications to the RAG system
"""

from typing import Dict, Optional
from .rag_core import OptimizedRAGSystem, get_rag_system
from .rag_chunking import RAGChunkingMixin


class EnhancedRAGSystem(OptimizedRAGSystem, RAGChunkingMixin):
    """Enhanced RAG system with chunking capabilities."""
    pass


def upload_openapi_spec_to_rag(file_path: str, collection_name: str, metadata: Optional[Dict] = None) -> str:
    """Upload OpenAPI spec with optimized chunking."""
    try:
        # Create enhanced RAG system instance
        rag = EnhancedRAGSystem()
        return rag.upload_spec(file_path, collection_name)
    except Exception as e:
        return f"❌ Upload error: {str(e)}"
