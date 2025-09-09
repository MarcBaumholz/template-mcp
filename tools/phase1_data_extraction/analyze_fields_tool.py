"""
MCP Tool: Analyze Fields with RAG and LLM
Handles enhanced field analysis using RAG and LLM integration
"""

import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from .rag_core import OptimizedRAGSystem, get_rag_system
from .rag_querying import RAGQueryingMixin
from tools.shared_utilities.llm_client import get_llm_response


class EnhancedRAGSystem(OptimizedRAGSystem, RAGQueryingMixin):
    """Enhanced RAG system with querying capabilities."""
    pass


def analyze_fields_with_rag_and_llm(fields: List[str], collection_name: str, context_topic: Optional[str] = None, current_path: Optional[str] = None) -> str:
    """Enhanced field analysis with multi-query strategy."""
    try:
        # Create enhanced RAG system instance
        rag = EnhancedRAGSystem()
        
        # Enhanced context gathering with multiple query strategies
        enhanced_context = {}
        for field in fields:
            field_queries = [
                f"{field} parameter definition",
                f"{field} property schema type",
                f"{field} field description validation",
                f"{field} attribute meaning usage"
            ]
            
            if context_topic:
                field_queries.append(f"{context_topic} {field}")
            
            field_results = []
            for query in field_queries:
                results = rag.enhanced_query(query, collection_name, limit=2)
                for result in results:
                    if 'error' not in result:
                        field_results.append({
                            'text': result['text'],
                            'score': result['semantic_score'],
                            'query': query
                        })
            
            # Deduplicate and rank
            unique_results = {}
            for result in field_results:
                    text = result['text']
                    if text not in unique_results or result['score'] > unique_results[text]['score']:
                        unique_results[text] = result
            
            enhanced_context[field] = sorted(unique_results.values(), key=lambda x: x['score'], reverse=True)[:3]
        
        # Create enhanced LLM prompt
        context_str = f"Context: {context_topic}\n\n" if context_topic else ""
        
        prompt = f"""{context_str}Enhanced field analysis based on comprehensive API documentation:

Fields to analyze: {', '.join(fields)}

Comprehensive API Documentation Context:
"""
        
        for field, results in enhanced_context.items():
            prompt += f"\n--- {field} (Enhanced Analysis) ---\n"
            for i, result in enumerate(results, 1):
                prompt += f"Context {i} (Score: {result['score']:.3f}, Query: '{result['query'][:30]}...'):\n"
                prompt += f"{result['text']}\n\n"
        
        prompt += """
ENHANCED ANALYSIS TASK:
For each field, provide comprehensive semantic analysis:

1. **Semantic Description**: Detailed meaning and purpose (1-2 sentences)
2. **Synonyms**: Alternative names in other systems (max 3)
3. **Possible Datatypes**: Supported data types (max 3)
4. **Business Context**: Usage in business processes
5. **API Mapping Hints**: Specific mapping recommendations based on context

Format as structured text with clear sections for each field.
"""
        
        response = get_llm_response(prompt, max_tokens=3000)
        
        # Save enhanced analysis
        if current_path:
            output_dir = Path(current_path)
            output_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"enhanced_field_analysis_{timestamp}.md"
            filepath = output_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# Enhanced Field Analysis\n\n")
                f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Fields:** {', '.join(fields)}\n")
                f.write(f"**Collection:** {collection_name}\n")
                f.write(f"**Context Topic:** {context_topic or 'General'}\n\n")
                f.write(f"## Analysis Results\n\n")
                f.write(response)
                f.write(f"\n\n## Context Sources\n\n")
                
                for field, results in enhanced_context.items():
                    f.write(f"### {field} Sources:\n")
                    for i, result in enumerate(results, 1):
                        f.write(f"{i}. Score: {result['score']:.3f} | Query: {result['query']}\n")
                    f.write(f"\n")
                
            response += f"\n\n📄 Enhanced analysis saved to: {filepath}"
        
        return response
        
    except Exception as e:
        return f"❌ Enhanced analysis error: {str(e)}"
