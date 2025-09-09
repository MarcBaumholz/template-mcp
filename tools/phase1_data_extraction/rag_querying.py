"""
RAG Querying Methods
Contains all query and search methods for API specifications
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from .rag_core import OptimizedRAGSystem

logger = logging.getLogger(__name__)


class RAGQueryingMixin:
    """Mixin class providing querying functionality for OptimizedRAGSystem."""
    
    def _enhance_query_semantically(self, query: str) -> str:
        """Enhance query with semantic context."""
        query_lower = query.lower()
        enhanced_parts = [query]
        
        # API-specific context enhancement
        api_patterns = {
            'endpoint': ['api', 'endpoint', 'path', 'method', 'operation'],
            'parameters': ['parameter', 'param', 'query', 'body', 'header'],
            'schema': ['schema', 'definition', 'model', 'object', 'property'],
            'response': ['response', 'return', 'output', 'result', 'status'],
            'authentication': ['auth', 'token', 'key', 'security', 'login'],
        }
        
        for category, terms in api_patterns.items():
            if any(term in query_lower for term in terms):
                enhanced_parts.extend(terms[:2])
                break
        
        return " ".join(enhanced_parts[:6])
    
    def _semantic_rerank(self, original_query: str, results) -> List[Dict]:
        """Enhanced re-ranking with semantic weights."""
        if not results:
            return []
        
        ranked_results = []
        query_lower = original_query.lower()
        query_words = set(query_lower.split())
        
        for result in results:
            try:
                # Handle different result structures
                if hasattr(result, 'payload') and result.payload:
                    payload = result.payload
                    score = getattr(result, 'score', 0.0)
                elif isinstance(result, dict):
                    payload = result.get('payload', {})
                    score = result.get('score', 0.0)
                else:
                    logger.warning(f"Unexpected result structure: {type(result)}")
                    continue
                
                # Handle different payload formats
                text = payload.get('text', '')
                
                # If no 'text' field, construct text from other fields
                if not text:
                    text_parts = []
                    if 'api_name' in payload:
                        text_parts.append(f"API: {payload['api_name']}")
                    if 'api_description' in payload:
                        text_parts.append(f"Description: {payload['api_description']}")
                    if 'endpoint' in payload:
                        text_parts.append(f"Endpoint: {payload['endpoint']}")
                    if 'method' in payload:
                        text_parts.append(f"Method: {payload['method']}")
                    if 'field_name' in payload:
                        text_parts.append(f"Field: {payload['field_name']}")
                    if 'description' in payload:
                        text_parts.append(f"Field Description: {payload['description']}")
                    if 'field_type' in payload:
                        text_parts.append(f"Type: {payload['field_type']}")
                    
                    text = " | ".join(text_parts)
                
                if not text:
                    continue
                
                text_lower = text.lower()
                text_words = set(text_lower.split())
                
                # Base score from vector similarity
                semantic_score = score
                
                # Apply semantic weight from chunk
                chunk_weight = payload.get('semantic_weight', 1.0)
                semantic_score *= chunk_weight
                
                # Boost for exact keyword matches
                exact_matches = len(query_words.intersection(text_words))
                if exact_matches > 0:
                    semantic_score += (exact_matches / len(query_words)) * 0.15
                
                # Boost for chunk type relevance
                chunk_type = payload.get('chunk_type', '')
                type_boost = self._get_chunk_type_boost(query_lower, chunk_type)
                semantic_score += type_boost
                
                # Boost for optimal token density
                tokens = payload.get('tokens', 100)
                if 50 <= tokens <= 200:
                    semantic_score += 0.05
                
                # Penalize very short content
                if len(text.split()) < 10:
                    semantic_score -= 0.1
                
                ranked_results.append({
                    'text': text,
                    'score': score,
                    'semantic_score': min(semantic_score, 1.0),
                    'chunk_type': chunk_type,
                    'tokens': tokens,
                    'metadata': {k: v for k, v in payload.items() 
                               if k not in ['text', 'chunk_type', 'tokens', 'semantic_weight']}
                })
                
            except Exception as e:
                logger.warning(f"Error processing result in semantic rerank: {e}")
                continue
        
        return sorted(ranked_results, key=lambda x: x['semantic_score'], reverse=True)
    
    def _get_chunk_type_boost(self, query: str, chunk_type: str) -> float:
        """Calculate relevance boost based on query intent."""
        intent_patterns = {
            'summary': ['what is', 'overview', 'describe', 'about', 'summary'],
            'parameters': ['parameter', 'param', 'input', 'request', 'field'],
            'responses': ['response', 'output', 'return', 'result', 'status'],
            'properties': ['property', 'field', 'attribute', 'column']
        }
        
        for intent, patterns in intent_patterns.items():
            if any(pattern in query for pattern in patterns):
                if intent in chunk_type:
                    return 0.1
                elif 'summary' in chunk_type and intent != 'summary':
                    return 0.05
        
        return 0.0
    
    def enhanced_query(self, query: str, collection_name: str, limit: int = 5) -> List[Dict]:
        """Enhanced query with multi-stage processing."""
        try:
            # 1. Enhance query semantically
            enhanced_query = self._enhance_query_semantically(query)
            query_embedding = self.encoder.encode(enhanced_query).tolist()
            
            # 2. Get broader candidates for re-ranking
            search_limit = min(limit * 4, 100)
            
            initial_results = self.client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=search_limit,
                score_threshold=0.2
            )
            
            # 3. Semantic re-ranking
            ranked_results = self._semantic_rerank(query, initial_results)
            
            # 4. Apply hierarchical filtering
            filtered_results = self._apply_hierarchical_filtering(query, ranked_results, limit)
            
            # 5. Format results with proper error handling
            formatted_results = []
            for result in filtered_results:
                if result['semantic_score'] >= 0.1:  # Reduced from 0.3 to 0.1
                    try:
                        formatted_results.append({
                            'text': result.get('text', ''),
                            'score': result.get('score', 0.0),
                            'semantic_score': result.get('semantic_score', 0.0),
                            'chunk_type': result.get('chunk_type', 'unknown'),
                            'tokens': result.get('tokens', 0),
                            'metadata': result.get('metadata', {})
                        })
                    except Exception as e:
                        logger.warning(f"Error formatting result: {e}")
                        continue
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Enhanced query failed: {e}")
            return [{'error': f"Enhanced query failed: {str(e)}"}]

    def _basic_search(self, query: str, collection_name: str, limit: int = 5) -> List[Dict]:
        """Basic vector search without re-ranking or boosts."""
        try:
            query_vector = self.encoder.encode(query).tolist()
            raw_results = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=0.2,
            )

            formatted: List[Dict[str, Any]] = []
            for result in raw_results:
                try:
                    if hasattr(result, 'payload') and result.payload:
                        payload = result.payload
                        score = getattr(result, 'score', 0.0)
                    elif isinstance(result, dict):
                        payload = result.get('payload', {})
                        score = result.get('score', 0.0)
                    else:
                        continue

                    text = payload.get('text', '')
                    if not text:
                        continue

                    chunk_type = payload.get('chunk_type', 'unknown')
                    tokens = int(payload.get('tokens', 0) or self._count_tokens(text))
                    metadata = {k: v for k, v in payload.items() if k not in ['text', 'chunk_type', 'tokens', 'semantic_weight']}

                    formatted.append({
                        'text': text,
                        'score': score,
                        'semantic_score': score,
                        'chunk_type': chunk_type,
                        'tokens': tokens,
                        'metadata': metadata,
                    })
                except Exception:
                    continue

            return formatted
        except Exception as e:
            logger.error(f"Basic search failed: {e}")
            return [{'error': f"Basic search failed: {str(e)}"}]

    def endpoint_first_query(self, query: str, collection_name: str, limit: int = 5) -> List[Dict]:
        """
        Simple and effective two-phase query:

        1) Endpoint discovery: find top endpoints/paths relevant to the query
        2) Field discovery: within those endpoints, return key fields (parameters, request body, responses, schema properties)

        No re-ranking, no boosts. Pure vector search + lightweight filtering.
        """
        try:
            # Phase 1: endpoint discovery
            endpoint_query = f"{query} endpoint path operation method"
            endpoint_vector = self.encoder.encode(endpoint_query).tolist()
            endpoint_results = self.client.search(
                collection_name=collection_name,
                query_vector=endpoint_vector,
                limit=max(limit * 4, 20),
                score_threshold=0.2,
            )

            # Collect unique endpoints by (path, method)
            endpoint_map: Dict[tuple, Dict[str, Any]] = {}
            for res in endpoint_results:
                try:
                    payload = res.payload if hasattr(res, 'payload') else (res.get('payload', {}) if isinstance(res, dict) else {})
                    chunk_type = payload.get('chunk_type', '')
                    if chunk_type not in ('operation_metadata', 'path_metadata'):
                        continue
                    path = payload.get('path')
                    method = payload.get('method')
                    if not path and not method:
                        continue
                    key = (path or '', method or '')
                    score = getattr(res, 'score', 0.0) if not isinstance(res, dict) else res.get('score', 0.0)
                    # Keep best score per endpoint
                    if key not in endpoint_map or score > endpoint_map[key]['score']:
                        endpoint_map[key] = {
                            'path': path,
                            'method': method,
                            'score': score,
                            'payload': payload,
                        }
                except Exception:
                    continue

            # Select top endpoints
            sorted_endpoints = sorted(endpoint_map.values(), key=lambda x: x['score'], reverse=True)[:max(limit, 3)]

            # If no endpoints were found, fallback to basic search
            if not sorted_endpoints:
                return self._basic_search(query, collection_name, limit)

            # Phase 2: field discovery (single broad field-query once, then filter by endpoint)
            field_query = f"{query} parameter request body schema properties field"
            field_vector = self.encoder.encode(field_query).tolist()
            field_results = self.client.search(
                collection_name=collection_name,
                query_vector=field_vector,
                limit=max(limit * 10, 50),
                score_threshold=0.2,
            )

            # Prepare final list: include an endpoint summary item followed by its field items
            final_results: List[Dict[str, Any]] = []

            for ep in sorted_endpoints:
                path = ep.get('path')
                method = ep.get('method')
                ep_score = float(ep.get('score', 0.0))
                op_id = ep.get('payload', {}).get('operation_id')
                tags = ep.get('payload', {}).get('tags')
                ep_text_parts: List[str] = []
                if method or path:
                    ep_text_parts.append(f"Endpoint: {(method.upper() + ' ') if method else ''}{path or ''}")
                if op_id:
                    ep_text_parts.append(f"Operation ID: {op_id}")
                if tags:
                    try:
                        ep_text_parts.append(f"Tags: {', '.join(tags) if isinstance(tags, list) else str(tags)}")
                    except Exception:
                        pass
                ep_text = "\n".join(ep_text_parts) or "Endpoint"
                final_results.append({
                    'text': ep_text,
                    'score': ep_score,
                    'semantic_score': ep_score,
                    'chunk_type': 'endpoint_summary',
                    'tokens': self._count_tokens(ep_text),
                    'metadata': {
                        'type': 'endpoint_summary',
                        'path': path,
                        'method': method,
                    },
                })

                # Collect field items associated with this endpoint
                field_added = 0
                for fres in field_results:
                    try:
                        fpay = fres.payload if hasattr(fres, 'payload') else (fres.get('payload', {}) if isinstance(fres, dict) else {})
                        if not fpay:
                            continue
                        # Match on same path/method when present in payload
                        fpath = fpay.get('path')
                        fmethod = fpay.get('method')
                        if fpath and path and fpath != path:
                            continue
                        if fmethod and method and fmethod != method:
                            continue

                        fct = fpay.get('chunk_type', '')
                        if fct not in ('operation_parameters', 'operation_request_body', 'operation_responses', 'schema_properties', 'schema_summary'):
                            continue

                        ftext = fpay.get('text', '')
                        if not ftext:
                            continue
                        fscore = getattr(fres, 'score', 0.0) if not isinstance(fres, dict) else fres.get('score', 0.0)
                        ftokens = int(fpay.get('tokens', 0) or self._count_tokens(ftext))
                        fmeta = {k: v for k, v in fpay.items() if k not in ['text', 'chunk_type', 'tokens', 'semantic_weight']}
                        final_results.append({
                            'text': ftext,
                            'score': fscore,
                            'semantic_score': fscore,
                            'chunk_type': fct,
                            'tokens': ftokens,
                            'metadata': fmeta,
                        })
                        field_added += 1
                        if field_added >= limit:
                            break
                    except Exception:
                        continue

            return final_results or self._basic_search(query, collection_name, limit)
        except Exception as e:
            logger.error(f"Endpoint-first query failed: {e}")
            return [{'error': f"Endpoint-first query failed: {str(e)}"}]
    
    def _apply_hierarchical_filtering(self, query: str, results: List[Dict], limit: int) -> List[Dict]:
        """Apply hierarchical filtering for balanced results."""
        if len(results) <= limit:
            return results
        
        # Separate by hierarchy level
        summaries = [r for r in results if 'summary' in r.get('chunk_type', '')]
        details = [r for r in results if 'summary' not in r.get('chunk_type', '')]
        
        # Adjust ratio based on query complexity
        query_words = len(query.split())
        summary_ratio = 0.6 if query_words <= 3 else 0.3
        
        summary_limit = int(limit * summary_ratio)
        detail_limit = limit - summary_limit
        
        selected_results = summaries[:summary_limit] + details[:detail_limit]
        
        # Fill remaining slots
        remaining_slots = limit - len(selected_results)
        if remaining_slots > 0:
            remaining_results = [r for r in results if r not in selected_results]
            selected_results.extend(remaining_results[:remaining_slots])
        
        return selected_results
