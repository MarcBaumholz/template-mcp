"""
MCP Tool: List API Specifications
Handles listing available API specification collections
"""

from .rag_core import get_rag_system


def list_rag_collections() -> str:
    """List RAG collections."""
    try:
        rag = get_rag_system()
        collections = rag.list_collections()
        if not collections:
            return "No collections found. Upload an API spec first."
        return f"Enhanced RAG Collections ({len(collections)}): {', '.join(collections)}"
    except Exception as e:
        return f"❌ List error: {str(e)}"
