"""
MCP Tool: Delete API Specification
Handles deleting API specification collections
"""

from .rag_core import get_rag_system


def delete_rag_collection(collection_name: str) -> str:
    """Delete RAG collection."""
    try:
        rag = get_rag_system()
        return rag.delete_collection(collection_name)
    except Exception as e:
        return f"❌ Delete error: {str(e)}"
