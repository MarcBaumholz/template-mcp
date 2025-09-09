#!/usr/bin/env python3
"""
Test RAG System Tool

Simple utility to test RAG system connectivity and basic operations.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

def test_rag_system() -> str:
    """
    Test RAG system and LLM connectivity.
    
    Returns:
        Status message indicating system health
    """
    try:
        # Import RAG tools to test connectivity
        from tools._archive._archive.rag_tools import test_rag_system as rag_test
        
        result = rag_test()
        logger.info("RAG system test completed successfully")
        return result
        
    except Exception as e:
        error_msg = f"❌ RAG system test failed: {str(e)}"
        logger.error(error_msg)
        return error_msg
