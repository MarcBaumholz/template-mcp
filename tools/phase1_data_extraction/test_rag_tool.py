"""
MCP Tool: Test RAG System
Handles testing the RAG system connectivity and functionality
"""

from .rag_core import get_rag_system, QDRANT_AVAILABLE


def test_rag_system() -> str:
    """Test optimized RAG system."""
    try:
        if not QDRANT_AVAILABLE:
            return "❌ Missing dependencies: pip install sentence-transformers qdrant-client pyyaml tiktoken"
        
        rag = get_rag_system()
        collections = rag.list_collections()
        return f"✅ Optimized RAG system working. Collections: {len(collections)}"
    except Exception as e:
        return f"❌ Test failed: {str(e)}"
