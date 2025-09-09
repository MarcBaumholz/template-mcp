"""
Core RAG Infrastructure
Contains the main OptimizedRAGSystem class and core configuration
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Add dotenv support for environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, will use system env vars

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams
    from sentence_transformers import SentenceTransformer
    import tiktoken
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class ChunkConfig:
    """Configuration for optimized chunking strategies."""
    max_tokens: int = 800
    overlap_percentage: float = 0.15
    min_tokens: int = 50
    batch_size: int = 100
    prune_vendor_extensions: bool = True


@dataclass
class DocumentChunk:
    """Represents a semantic chunk of API documentation."""
    text: str
    chunk_type: str
    metadata: Dict[str, Any]
    tokens: int
    semantic_weight: float = 1.0


class OptimizedRAGSystem:
    """Enhanced RAG system with semantic chunking and intelligent matching."""
    
    def __init__(self):
        if not QDRANT_AVAILABLE:
            raise ImportError("Install: pip install sentence-transformers qdrant-client pyyaml tiktoken")
        
        # Require Cloud Qdrant configuration (no local fallback)
        qdrant_url = os.getenv('QDRANT_URL')
        qdrant_api_key = os.getenv('QDRANT_API_KEY')
        if not (qdrant_url and qdrant_api_key):
            raise RuntimeError("Qdrant Cloud configuration required: set QDRANT_URL and QDRANT_API_KEY")
        logger.info(f"Connecting to Qdrant Cloud: {qdrant_url}")
        self.client = QdrantClient(
            url=qdrant_url,
            api_key=qdrant_api_key
        )
        storage_type = "Cloud"
        
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self.config = ChunkConfig()
        
        # Initialize tokenizer for precise token counting
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            raise RuntimeError("tiktoken encoding 'cl100k_base' not available") from e
        
        logger.info(f"Optimized RAG initialized: {storage_type} Storage")
    
    def _count_tokens(self, text: str) -> int:
        """Count tokens precisely using tiktoken."""
        return len(self.tokenizer.encode(text))
    
    def create_collection(self, collection_name: str):
        """Create collection with enhanced configuration."""
        try:
            collections = [c.name for c in self.client.get_collections().collections]
            if collection_name not in collections:
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=384,
                        distance=Distance.COSINE,
                    )
                )
        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
    
    def list_collections(self) -> List[str]:
        """List all collections."""
        try:
            return [c.name for c in self.client.get_collections().collections]
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            return []
    
    def delete_collection(self, collection_name: str) -> str:
        """Delete a collection."""
        try:
            self.client.delete_collection(collection_name)
            return f"✅ Deleted collection '{collection_name}'"
        except Exception as e:
            return f"❌ Delete failed: {str(e)}"
    
    def get_storage_info(self) -> str:
        """Get information about the current storage configuration."""
        qdrant_url = os.getenv('QDRANT_URL')
        if qdrant_url:
            return f"Cloud Storage: {qdrant_url}"
        return "Cloud Storage: not configured (set QDRANT_URL and QDRANT_API_KEY)"


# Global instance
_rag_system = None

def get_rag_system():
    """Get or create optimized RAG system."""
    global _rag_system
    if _rag_system is None:
        _rag_system = OptimizedRAGSystem()
    return _rag_system
