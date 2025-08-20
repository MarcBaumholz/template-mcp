"""
RAG Tools for OpenAPI Specification Analysis

This module provides tools for uploading, querying, and analyzing OpenAPI specifications
using a RAG (Retrieval-Augmented Generation) system with Qdrant vector database.
Enhanced with optimized chunking strategies for better semantic retrieval.
"""

import os
import json
import logging
import tempfile
import re
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import pandas as pd

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    from sentence_transformers import SentenceTransformer
    import yaml
    import tiktoken
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

from .llm_client import get_llm_response


@dataclass
class ChunkConfig:
    """Configuration for chunking strategies."""
    max_tokens: int = 800  # Increased for better context coverage
    overlap_percentage: float = 0.15  # 15% overlap for continuity
    min_tokens: int = 50   # Minimum viable chunk size
    batch_size: int = 32   # Embedding batch size for efficiency
    prune_vendor_extensions: bool = True  # Remove x-* fields by default


@dataclass
class DocumentChunk:
    """Represents a semantic chunk of API documentation."""
    text: str
    chunk_type: str  # 'info', 'server', 'operation_metadata', 'operation_params', etc.
    metadata: Dict[str, Any]
    tokens: int
    semantic_weight: float = 1.0  # Higher weight = more important for retrieval


class OpenAPIChunker:
    """Comprehensive OpenAPI specification chunker with full-spec coverage."""
    
    def __init__(self, encoder: SentenceTransformer, config: ChunkConfig):
        """Initialize chunker with encoder and configuration."""
        self.encoder = encoder
        self.config = config
        self.tokenizer = None
        
        # Initialize tokenizer for precise token counting
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception:
            logging.warning("Tiktoken not available, using approximate token counting")
    
    def _count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken or approximation."""
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        else:
            # Approximation: ~4 characters per token
            return len(text) // 4
    
    def _prune_vendor_extensions(self, obj: Dict) -> Dict:
        """Remove vendor-specific extensions (x-* fields) to reduce noise."""
        if not self.config.prune_vendor_extensions or not isinstance(obj, dict):
            return obj
        
        return {k: v for k, v in obj.items() if not k.startswith('x-')}
    
    def _sliding_window_chunks(self, text: str) -> List[str]:
        """Create sliding window chunks with token-aware splitting."""
        total_tokens = self._count_tokens(text)
        
        if total_tokens <= self.config.max_tokens:
            return [text]
        
        chunks = []
        words = text.split()
        overlap_tokens = int(self.config.max_tokens * self.config.overlap_percentage)
        
        current_chunk = []
        current_tokens = 0
        
        for word in words:
            word_tokens = self._count_tokens(word + " ")
            
            if current_tokens + word_tokens > self.config.max_tokens and current_chunk:
                # Create chunk and start new one with overlap
                chunk_text = " ".join(current_chunk)
                chunks.append(chunk_text)
                
                # Calculate overlap words
                overlap_words = []
                overlap_token_count = 0
                for i in range(len(current_chunk) - 1, -1, -1):
                    word_token_count = self._count_tokens(current_chunk[i] + " ")
                    if overlap_token_count + word_token_count <= overlap_tokens:
                        overlap_words.insert(0, current_chunk[i])
                        overlap_token_count += word_token_count
                else:
                        break
                
                current_chunk = overlap_words
                current_tokens = overlap_token_count
            
            current_chunk.append(word)
            current_tokens += word_tokens
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks
    
    def _make_info_chunk(self, info: Dict) -> DocumentChunk:
        """Create chunk for OpenAPI info section."""
        info = self._prune_vendor_extensions(info)
        
        parts = [
            f"API Info: {info.get('title', 'Unknown')} v{info.get('version', 'Unknown')}",
        ]
        
        if 'description' in info:
            parts.append(f"Description: {info['description']}")
        
        if 'contact' in info:
            contact = info['contact']
            contact_parts = []
            if 'name' in contact:
                contact_parts.append(f"Contact: {contact['name']}")
            if 'email' in contact:
                contact_parts.append(f"Email: {contact['email']}")
            if 'url' in contact:
                contact_parts.append(f"URL: {contact['url']}")
            if contact_parts:
                parts.extend(contact_parts)
        
        if 'license' in info:
            license_info = info['license']
            if 'name' in license_info:
                parts.append(f"License: {license_info['name']}")
        
        text = "\n".join(parts)
        
        return DocumentChunk(
            text=text,
            chunk_type='info',
            metadata={'type': 'info'},
            tokens=self._count_tokens(text),
            semantic_weight=1.3  # Higher weight for API overview
        )
    
    def _make_server_chunks(self, servers: List[Dict]) -> List[DocumentChunk]:
        """Create chunks for server configurations."""
        chunks = []
        
        for i, server in enumerate(servers):
            server = self._prune_vendor_extensions(server)
            
            parts = [f"Server {i + 1}: {server.get('url', 'Unknown URL')}"]
            
            if 'description' in server:
                parts.append(f"Description: {server['description']}")
            
            if 'variables' in server:
                var_parts = ["Variables:"]
                for var_name, var_data in server['variables'].items():
                    var_text = f"  - {var_name}"
                    if 'default' in var_data:
                        var_text += f" (default: {var_data['default']})"
                    if 'description' in var_data:
                        var_text += f" - {var_data['description']}"
                    var_parts.append(var_text)
                parts.extend(var_parts)
            
            text = "\n".join(parts)
            
            chunks.append(DocumentChunk(
                text=text,
                chunk_type='server',
                metadata={'type': 'server', 'server_index': i},
                tokens=self._count_tokens(text),
                semantic_weight=1.1
            ))
        
        return chunks
    
    def _make_components_chunks(self, components: Dict) -> List[DocumentChunk]:
        """Create chunks for all components subsections."""
        chunks = []
        
        # Component types to process
        component_types = [
            'parameters', 'requestBodies', 'responses', 'headers',
            'securitySchemes', 'examples', 'links', 'callbacks'
        ]
        
        for comp_type in component_types:
            if comp_type not in components:
                continue
            
            for name, obj in components[comp_type].items():
                obj = self._prune_vendor_extensions(obj)
                
                # Create a structured representation
                parts = [f"{comp_type[:-1].title()}: {name}"]
                
                if 'description' in obj:
                    parts.append(f"Description: {obj['description']}")
                
                # Add type-specific information
                if comp_type == 'parameters':
                    if 'in' in obj:
                        parts.append(f"Location: {obj['in']}")
                    if 'schema' in obj:
                        schema = obj['schema']
                        if '$ref' in schema:
                            parts.append(f"Schema Reference: {schema['$ref']}")
                        elif 'type' in schema:
                            parts.append(f"Type: {schema['type']}")
                
                elif comp_type == 'requestBodies':
                    if 'content' in obj:
                        content_types = list(obj['content'].keys())
                        parts.append(f"Content Types: {', '.join(content_types)}")
                
                elif comp_type == 'responses':
                    if 'content' in obj:
                        content_types = list(obj['content'].keys())
                        parts.append(f"Content Types: {', '.join(content_types)}")
                
                elif comp_type == 'securitySchemes':
                    if 'type' in obj:
                        parts.append(f"Security Type: {obj['type']}")
                    if 'scheme' in obj:
                        parts.append(f"Scheme: {obj['scheme']}")
                
                # Add raw YAML for detailed structure
                try:
                    yaml_content = yaml.dump(obj, default_flow_style=False)
                    parts.append(f"Structure:\n{yaml_content}")
                except Exception:
                    # Fallback to JSON if YAML fails
                    parts.append(f"Structure:\n{json.dumps(obj, indent=2)}")
                
                text = "\n".join(parts)
                
                # Split large components into chunks
                text_chunks = self._sliding_window_chunks(text)
                
                for chunk_idx, chunk_text in enumerate(text_chunks):
                    if self._count_tokens(chunk_text) >= self.config.min_tokens:
                        chunks.append(DocumentChunk(
                            text=chunk_text,
                            chunk_type=f'component_{comp_type[:-1]}',
                            metadata={
                                'type': comp_type[:-1],
                                'name': name,
                                'chunk_index': chunk_idx if len(text_chunks) > 1 else None
                            },
                            tokens=self._count_tokens(chunk_text),
                            semantic_weight=1.0
                        ))
        
        return chunks
    
    def _make_operation_metadata_chunk(self, path: str, method: str, operation: Dict) -> DocumentChunk:
        """Create metadata chunk for an API operation."""
        operation = self._prune_vendor_extensions(operation)
        
        parts = [
            f"Operation: {method.upper()} {path}",
        ]
        
        if 'operationId' in operation:
            parts.append(f"Operation ID: {operation['operationId']}")
        
        if 'tags' in operation and operation['tags']:
            parts.append(f"Tags: {', '.join(operation['tags'])}")
        
        if 'summary' in operation:
            parts.append(f"Summary: {operation['summary']}")
        
        if 'description' in operation:
            parts.append(f"Description: {operation['description']}")
        
        if 'deprecated' in operation and operation['deprecated']:
            parts.append("Status: DEPRECATED")
        
        text = "\n".join(parts)
        
        return DocumentChunk(
            text=text,
            chunk_type='operation_metadata',
            metadata={
                'type': 'operation_metadata',
                                'path': path,
                'method': method.lower(),
                'operation_id': operation.get('operationId')
            },
            tokens=self._count_tokens(text),
            semantic_weight=1.2
        )
    
    def _make_operation_parameters_chunk(self, path: str, method: str, operation: Dict) -> Optional[DocumentChunk]:
        """Create parameters chunk for an API operation."""
        if 'parameters' not in operation or not operation['parameters']:
            return None
        
        parts = [f"Parameters for {method.upper()} {path}:"]
        
        for param in operation['parameters']:
            param = self._prune_vendor_extensions(param)
            
            param_text = f"• {param.get('name', 'unnamed')}"
            
            if 'in' in param:
                param_text += f" (in: {param['in']})"
            
            if 'required' in param and param['required']:
                param_text += " - REQUIRED"
            
            # Schema information
            schema = param.get('schema', {})
            if '$ref' in schema:
                ref_name = schema['$ref'].split('/')[-1]
                param_text += f" - ref: {ref_name}"
            elif 'type' in schema:
                param_text += f" - type: {schema['type']}"
                if 'format' in schema:
                    param_text += f" ({schema['format']})"
            
            # Style and explode for query/path parameters
            if 'style' in param or 'explode' in param:
                style_info = []
                if 'style' in param:
                    style_info.append(f"style: {param['style']}")
                if 'explode' in param:
                    style_info.append(f"explode: {param['explode']}")
                param_text += f" [{', '.join(style_info)}]"
            
            if 'description' in param:
                param_text += f" - {param['description']}"
            
            if 'example' in param:
                param_text += f" - example: {param['example']}"
            
            parts.append(param_text)
        
        text = "\n".join(parts)
        
        # Split large parameter lists if needed
        text_chunks = self._sliding_window_chunks(text)
        
        if len(text_chunks) == 1:
            return DocumentChunk(
                text=text,
                chunk_type='operation_parameters',
                metadata={
                    'type': 'operation_parameters',
                    'path': path,
                    'method': method.lower(),
                    'operation_id': operation.get('operationId')
                },
                tokens=self._count_tokens(text),
                semantic_weight=1.0
            )
        
        # For multiple chunks, return the first one (others would be handled separately)
        return DocumentChunk(
            text=text_chunks[0],
            chunk_type='operation_parameters',
            metadata={
                'type': 'operation_parameters',
                'path': path,
                'method': method.lower(),
                'operation_id': operation.get('operationId'),
                'chunk_index': 0,
                'total_chunks': len(text_chunks)
            },
            tokens=self._count_tokens(text_chunks[0]),
            semantic_weight=1.0
        )
    
    def _make_operation_responses_chunk(self, path: str, method: str, operation: Dict) -> Optional[DocumentChunk]:
        """Create responses chunk for an API operation."""
        if 'responses' not in operation:
            return None
        
        parts = [f"Responses for {method.upper()} {path}:"]
        
        for status_code, response in operation['responses'].items():
            response = self._prune_vendor_extensions(response)
            
            response_text = f"• Status {status_code}"
            
            if 'description' in response:
                response_text += f": {response['description']}"
            
            # Handle OpenAPI 3.x content
            if 'content' in response:
                content_types = list(response['content'].keys())
                response_text += f" - Content-Type: {', '.join(content_types)}"
                
                # Get schema references from content
                for content_type, content_data in response['content'].items():
                    if 'schema' in content_data:
                        schema = content_data['schema']
                        if '$ref' in schema:
                            ref_name = schema['$ref'].split('/')[-1]
                            response_text += f" - Schema: {ref_name}"
                        elif 'type' in schema:
                            response_text += f" - Type: {schema['type']}"
            
            # Handle OpenAPI 2.0 schema
            elif 'schema' in response:
                schema = response['schema']
                if '$ref' in schema:
                    ref_name = schema['$ref'].split('/')[-1]
                    response_text += f" - Schema: {ref_name}"
                elif 'type' in schema:
                    response_text += f" - Type: {schema['type']}"
            
            # Headers
            if 'headers' in response:
                header_names = list(response['headers'].keys())
                response_text += f" - Headers: {', '.join(header_names)}"
            
            parts.append(response_text)
        
        text = "\n".join(parts)
        
        return DocumentChunk(
            text=text,
            chunk_type='operation_responses',
            metadata={
                'type': 'operation_responses',
                'path': path,
                'method': method.lower(),
                'operation_id': operation.get('operationId')
            },
            tokens=self._count_tokens(text),
            semantic_weight=0.9
        )
    
    def _make_schema_chunks(self, schema_name: str, schema_data: Dict, is_definition: bool = False) -> List[DocumentChunk]:
        """Create optimized chunks for schemas/definitions with comprehensive coverage."""
        chunks = []
        schema_type = 'definition' if is_definition else 'schema'
        schema_data = self._prune_vendor_extensions(schema_data)
        
        # 1. Schema summary chunk
        summary_parts = [f"{'Definition' if is_definition else 'Schema'}: {schema_name}"]
        
        if 'type' in schema_data:
            summary_parts.append(f"Type: {schema_data['type']}")
                
        if 'description' in schema_data:
            summary_parts.append(f"Description: {schema_data['description']}")
        
        if 'required' in schema_data:
            required_fields = schema_data['required']
            if isinstance(required_fields, list) and required_fields:
                summary_parts.append(f"Required Fields: {', '.join(required_fields)}")
        
        # Add discriminator information
        if 'discriminator' in schema_data:
            discriminator = schema_data['discriminator']
            if isinstance(discriminator, dict) and 'propertyName' in discriminator:
                summary_parts.append(f"Discriminator: {discriminator['propertyName']}")
            elif isinstance(discriminator, str):
                summary_parts.append(f"Discriminator: {discriminator}")
        
        summary_text = "\n".join(summary_parts)
        
        if self._count_tokens(summary_text) >= self.config.min_tokens:
            chunks.append(DocumentChunk(
                text=summary_text,
                chunk_type=f'{schema_type}_summary',
                metadata={
                    'type': f'{schema_type}_summary',
                    f'{schema_type}_name': schema_name
                },
                tokens=self._count_tokens(summary_text),
                semantic_weight=1.1
            ))
        
        # 2. Properties chunks with comprehensive extraction
        all_properties = {}
        
        # Direct properties
        if 'properties' in schema_data:
            all_properties.update(schema_data['properties'])
        
        # allOf properties
        if 'allOf' in schema_data:
            for all_of_item in schema_data['allOf']:
                if 'properties' in all_of_item:
                    all_properties.update(all_of_item['properties'])
        
        # oneOf properties (collect from all alternatives)
        if 'oneOf' in schema_data:
            for one_of_item in schema_data['oneOf']:
                if 'properties' in one_of_item:
                    all_properties.update(one_of_item['properties'])
        
        # anyOf properties
        if 'anyOf' in schema_data:
            for any_of_item in schema_data['anyOf']:
                if 'properties' in any_of_item:
                    all_properties.update(any_of_item['properties'])
        
        if all_properties:
            # Group properties semantically for better chunks
            property_groups = self._group_properties_semantically(all_properties)
            
            for group_name, group_props in property_groups.items():
                prop_parts = [f"Properties for {schema_name} ({group_name}):"]
                
                for prop_name, prop_data in group_props.items():
                    prop_text = f"• {prop_name}"
                    
                    if isinstance(prop_data, dict):
                        prop_data = self._prune_vendor_extensions(prop_data)
                        
                        # Type information
                        if 'type' in prop_data:
                            prop_text += f" ({prop_data['type']})"
                            if 'format' in prop_data:
                                prop_text += f" - format: {prop_data['format']}"
                        
                        # Reference
                        if '$ref' in prop_data:
                            ref_name = prop_data['$ref'].split('/')[-1]
                            prop_text += f" - ref: {ref_name}"
                        
                        # Array items
                        if 'items' in prop_data:
                            items = prop_data['items']
                            if '$ref' in items:
                                ref_name = items['$ref'].split('/')[-1]
                                prop_text += f" - items: {ref_name}"
                            elif 'type' in items:
                                prop_text += f" - items: {items['type']}"
                        
                        # Enum values
                        if 'enum' in prop_data:
                            enum_values = prop_data['enum'][:5]  # Limit to first 5
                            prop_text += f" - values: {', '.join(map(str, enum_values))}"
                            if len(prop_data['enum']) > 5:
                                prop_text += f" (and {len(prop_data['enum']) - 5} more)"
                        
                        # Constraints
                        constraints = []
                        for constraint in ['minimum', 'maximum', 'minLength', 'maxLength', 'pattern']:
                            if constraint in prop_data:
                                constraints.append(f"{constraint}: {prop_data[constraint]}")
                        if constraints:
                            prop_text += f" - constraints: {', '.join(constraints)}"
                        
                        # Description
                        if 'description' in prop_data:
                            prop_text += f" - {prop_data['description']}"
                        
                        # Example
                        if 'example' in prop_data:
                            prop_text += f" - example: {prop_data['example']}"
                    
                    prop_parts.append(prop_text)
                
                prop_text = "\n".join(prop_parts)
                
                # Split large property groups into chunks
                prop_chunks = self._sliding_window_chunks(prop_text)
                
                for i, chunk_text in enumerate(prop_chunks):
                    if self._count_tokens(chunk_text) >= self.config.min_tokens:
                        chunks.append(DocumentChunk(
                            text=chunk_text,
                            chunk_type=f'{schema_type}_properties',
                            metadata={
                                'type': f'{schema_type}_properties',
                                f'{schema_type}_name': schema_name,
                                'property_group': group_name,
                                'chunk_index': i if len(prop_chunks) > 1 else None
                            },
                            tokens=self._count_tokens(chunk_text),
                            semantic_weight=1.0
                        ))
        
        return chunks
    
    def _group_properties_semantically(self, properties: Dict) -> Dict[str, Dict]:
        """Enhanced semantic grouping of properties for better chunk organization."""
        # Enhanced semantic groupings for comprehensive API patterns
        semantic_groups = {
            'identifiers': ['id', 'uuid', 'external_id', 'reference', 'key', 'code', 'identifier', 'ref'],
            'temporal': ['date', 'time', 'created', 'updated', 'modified', 'start', 'end', 'duration', 'timestamp', 'expires'],
            'personal': ['name', 'first', 'last', 'email', 'phone', 'address', 'contact', 'user', 'person', 'customer'],
            'status': ['status', 'state', 'active', 'enabled', 'disabled', 'deleted', 'archived', 'published', 'visible'],
            'metadata': ['meta', 'attributes', 'tags', 'labels', 'custom', 'extra', 'properties', 'data'],
            'financial': ['amount', 'cost', 'price', 'currency', 'rate', 'budget', 'payment', 'billing', 'invoice'],
            'location': ['location', 'address', 'city', 'country', 'region', 'zone', 'coordinates', 'latitude', 'longitude'],
            'content': ['title', 'description', 'content', 'body', 'text', 'message', 'comment', 'note'],
            'technical': ['version', 'type', 'format', 'encoding', 'protocol', 'algorithm', 'checksum', 'hash'],
            'relationships': ['parent', 'child', 'owner', 'belongs', 'related', 'linked', 'associated', 'foreign']
        }
        
        grouped = {}
        ungrouped = {}
        
        # First pass: group by known semantic patterns
        for prop_name, prop_data in properties.items():
            prop_lower = prop_name.lower()
            assigned = False
            
            for group_name, keywords in semantic_groups.items():
                if any(keyword in prop_lower for keyword in keywords):
                    if group_name not in grouped:
                        grouped[group_name] = {}
                    grouped[group_name][prop_name] = prop_data
                    assigned = True
                    break
            
            if not assigned:
                ungrouped[prop_name] = prop_data
        
        # Second pass: create balanced groups from ungrouped properties
        if ungrouped:
            # Split ungrouped into reasonable chunks
            ungrouped_items = list(ungrouped.items())
            max_chunk_size = 8  # Maximum properties per chunk
            
            for i in range(0, len(ungrouped_items), max_chunk_size):
                group_props = dict(ungrouped_items[i:i + max_chunk_size])
                if group_props:
                    group_index = i // max_chunk_size + 1
                    grouped[f'other_properties_{group_index}'] = group_props
        
        # Ensure we have at least one group
        if not grouped and properties:
            grouped['properties'] = properties
        
        return grouped
    
    async def _batch_encode_chunks(self, chunks: List[DocumentChunk]) -> List[PointStruct]:
        """Batch encode chunks for efficient embedding generation."""
        if not chunks:
            return []
        
        points = []
        
        # Process chunks in batches for optimal performance
        for i in range(0, len(chunks), self.config.batch_size):
            batch_chunks = chunks[i:i + self.config.batch_size]
            batch_texts = [chunk.text for chunk in batch_chunks]
            
            try:
                # Generate embeddings in batch
                batch_embeddings = self.encoder.encode(
                    batch_texts, 
                    batch_size=len(batch_texts),
                    show_progress_bar=False  # Disable progress bar for cleaner output
                )
                
                # Create PointStruct objects
                for j, (chunk, embedding) in enumerate(zip(batch_chunks, batch_embeddings)):
                        points.append(PointStruct(
                        id=i + j,
                        vector=embedding.tolist(),
                        payload={
                            'text': chunk.text,
                            'chunk_type': chunk.chunk_type,
                            'tokens': chunk.tokens,
                            'semantic_weight': chunk.semantic_weight,
                            **chunk.metadata
                        }
                    ))
                    
            except Exception as e:
                logging.warning(f"Failed to encode batch {i//self.config.batch_size + 1}: {e}")
                
                # Fallback to individual encoding
                for j, chunk in enumerate(batch_chunks):
                    try:
                        embedding = self.encoder.encode(chunk.text)
                        points.append(PointStruct(
                            id=i + j,
                            vector=embedding.tolist(),
                            payload={
                                'text': chunk.text,
                                'chunk_type': chunk.chunk_type,
                                'tokens': chunk.tokens,
                                'semantic_weight': chunk.semantic_weight,
                                **chunk.metadata
                            }
                        ))
                    except Exception as inner_e:
                        logging.error(f"Failed to encode individual chunk: {inner_e}")
        
        return points
    
    async def process_spec(self, spec: Dict, metadata: Dict) -> List[PointStruct]:
        """Comprehensive processing of OpenAPI specification with full coverage."""
        all_chunks = []
        
        # 1. Process Info section
        if 'info' in spec:
            info_chunk = self._make_info_chunk(spec['info'])
            all_chunks.append(info_chunk)
        
        # 2. Process Servers
        if 'servers' in spec:
            server_chunks = self._make_server_chunks(spec['servers'])
            all_chunks.extend(server_chunks)
        
        # 3. Process Components (OpenAPI 3.x)
        if 'components' in spec:
            component_chunks = self._make_components_chunks(spec['components'])
            all_chunks.extend(component_chunks)
            
            # Process schemas within components
            if 'schemas' in spec['components']:
                for schema_name, schema_data in spec['components']['schemas'].items():
                    schema_chunks = self._make_schema_chunks(schema_name, schema_data, is_definition=False)
                    all_chunks.extend(schema_chunks)
        
        # 4. Process Definitions (OpenAPI 2.0)
        if 'definitions' in spec:
            for def_name, def_data in spec['definitions'].items():
                definition_chunks = self._make_schema_chunks(def_name, def_data, is_definition=True)
                all_chunks.extend(definition_chunks)
        
        # 5. Process Paths and Operations
        if 'paths' in spec:
            for path, path_data in spec['paths'].items():
                for method, operation in path_data.items():
                    if isinstance(operation, dict):
                        # Create metadata chunk
                        metadata_chunk = self._make_operation_metadata_chunk(path, method, operation)
                        all_chunks.append(metadata_chunk)
                        
                        # Create parameters chunk
                        params_chunk = self._make_operation_parameters_chunk(path, method, operation)
                        if params_chunk:
                            all_chunks.append(params_chunk)
                        
                        # Create responses chunk
                        responses_chunk = self._make_operation_responses_chunk(path, method, operation)
                        if responses_chunk:
                            all_chunks.append(responses_chunk)
        
        # 6. Batch encode all chunks
        points = await self._batch_encode_chunks(all_chunks)
        
        # Log statistics
        total_tokens = sum(chunk.tokens for chunk in all_chunks)
        avg_tokens = total_tokens / len(all_chunks) if all_chunks else 0
        
        logging.info(f"Comprehensive processing stats:")
        logging.info(f"  - Total chunks: {len(all_chunks)}")
        logging.info(f"  - Total tokens: {total_tokens:,}")
        logging.info(f"  - Average tokens/chunk: {avg_tokens:.1f}")
        logging.info(f"  - Chunk types: {set(chunk.chunk_type for chunk in all_chunks)}")
        
        return points


class EnhancedRAGSystem:
    """Enhanced RAG system with comprehensive OpenAPI processing and optimized chunking."""
    
    def __init__(self):
        """Initialize enhanced RAG system with comprehensive OpenAPI chunker."""
        if not QDRANT_AVAILABLE:
            raise ImportError("Required packages not available. Install with: pip install sentence-transformers qdrant-client pyyaml pandas tiktoken")
        
        # Initialize Qdrant client
        self._init_qdrant_client()
        
        # Initialize sentence transformer with caching
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize comprehensive chunker
        self.chunk_config = ChunkConfig()
        self.chunker = OpenAPIChunker(self.encoder, self.chunk_config)
        
        # Thread pool for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    def _init_qdrant_client(self):
        """Initialize Qdrant client with cloud or local storage."""
        qdrant_url = os.getenv('QDRANT_URL')
        qdrant_api_key = os.getenv('QDRANT_API_KEY')
        
        if qdrant_url and qdrant_api_key:
            self.client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
            self.storage_path = "cloud"
            self.logger = logging.getLogger("enhanced_rag_system")
            self.logger.info(f"Enhanced RAG system initialized with cloud Qdrant: {qdrant_url}")
        else:
            storage_path = os.path.join(os.getcwd(), "qdrant_storage")
            try:
                os.makedirs(storage_path, exist_ok=True)
                test_file = os.path.join(storage_path, ".write_test")
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
            except Exception as e:
                storage_path = tempfile.mkdtemp(prefix="qdrant_")
                logging.warning(f"Using temporary storage at {storage_path} due to: {e}")
            
            self.client = QdrantClient(path=storage_path)
            self.storage_path = storage_path
            self.logger = logging.getLogger("enhanced_rag_system")
            self.logger.info(f"Enhanced RAG system initialized with local storage at: {storage_path}")
    
    def _extract_vendor_extensions(self, obj: dict) -> dict:
        """Recursively extract all vendor extension fields (x-*) from the OpenAPI spec."""
        vendor_extensions = {}
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k.startswith('x-'):
                    vendor_extensions[k] = v
                elif isinstance(v, dict):
                    nested = self._extract_vendor_extensions(v)
                    if nested:
                        vendor_extensions.update(nested)
                elif isinstance(v, list):
                    for item in v:
                        nested = self._extract_vendor_extensions(item)
                        if nested:
                            vendor_extensions.update(nested)
        elif isinstance(obj, list):
            for item in obj:
                nested = self._extract_vendor_extensions(item)
                if nested:
                    vendor_extensions.update(nested)
        return vendor_extensions

    def upload_openapi_spec(self, file_path: str, collection_name: str, metadata: Optional[Dict] = None) -> str:
        """
        Sync wrapper for upload_openapi_spec using OpenAPIChunker (unified).
        In async environments, use the async method directly.
        """
        import asyncio
        try:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                return (
                    "Error: upload_openapi_spec cannot be called from a running event loop. "
                    "Use 'await _upload_openapi_spec_async(...)' instead."
                )
            else:
                return asyncio.run(self._upload_openapi_spec_async(file_path, collection_name, metadata))
        except Exception as e:
            return f"Error uploading specification: {str(e)}"
    
    async def _upload_openapi_spec_async(self, file_path: str, collection_name: str, metadata: Optional[Dict] = None) -> str:
        """Async implementation of upload_openapi_spec using OpenAPIChunker (unified)."""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return f"Error: File {file_path} does not exist"
            
            # Parse the file
            file_suffix = file_path.suffix.lower()
            if file_suffix not in ['.json', '.yaml', '.yml']:
                raise ValueError(f"Unsupported file format: {file_suffix}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_suffix in ['.yaml', '.yml']:
                    spec = yaml.safe_load(f)
                else:
                    spec = json.load(f)
            
            # Create collection
            self.create_collection(collection_name)
            
            # Unified: Use OpenAPIChunker for all chunking
            points = await self.chunker.process_spec(spec, metadata or {})
            
            # Upload to Qdrant in batches
            batch_size = 100  # Qdrant batch limit
            for i in range(0, len(points), batch_size):
                batch_points = points[i:i + batch_size]
            self.client.upsert(
                collection_name=collection_name,
                    points=batch_points
                )

            # Calculate statistics
            total_tokens = sum(point.payload.get('tokens', 0) for point in points)
            avg_tokens = total_tokens / len(points) if points else 0
            chunk_types = set(point.payload.get('chunk_type', 'unknown') for point in points)

            return (f"✅ Comprehensive upload successful!\n"
                   f"📄 File: {file_path.name}\n"
                   f"📊 Chunks: {len(points)} optimized chunks\n"
                   f"🎯 Avg tokens/chunk: {avg_tokens:.1f}\n"
                   f"📝 Total tokens: {total_tokens:,}\n"
                   f"🏷️ Collection: '{collection_name}'\n"
                   f"🔍 Chunk types: {', '.join(sorted(chunk_types))}")
        
        except Exception as e:
                return f"Error uploading specification: {str(e)}"

    def query(self, query: str, collection_name: str, limit: int = 5, score_threshold: float = 0.5) -> List[Dict]:
        """Enhanced query with hierarchical search and semantic re-ranking."""
        try:
            # Multi-stage query approach
            
            # 1. Broad semantic search with relaxed threshold
            enhanced_query = self._enhance_query_for_semantic_search(query)
            query_embedding = self.encoder.encode(enhanced_query).tolist()
            
            # Get more candidates for better re-ranking
            search_limit = min(limit * 4, 100)
            
            initial_results = self.client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=search_limit,
                score_threshold=max(score_threshold - 0.2, 0.2)
            )
            
            # 2. Enhanced re-ranking with semantic weights
            ranked_results = self._enhanced_rerank_results(query, initial_results)
            
            # 3. Hierarchical filtering (prefer summaries for broad queries)
            filtered_results = self._apply_hierarchical_filtering(query, ranked_results, limit)
            
            # Return enhanced results
            return [
                {
                    'text': result['text'],
                    'score': result['score'],
                    'semantic_score': result['semantic_score'],
                    'chunk_type': result.get('chunk_type', 'unknown'),
                    'tokens': result.get('tokens', 0),
                    'metadata': result['metadata']
                }
                for result in filtered_results
                if result['semantic_score'] >= score_threshold
            ]
        
        except Exception as e:
            return [{'error': f"Enhanced query failed: {str(e)}"}]
    
    def _enhance_query_for_semantic_search(self, query: str) -> str:
        """Enhanced query enhancement with better context awareness."""
        query_lower = query.lower()
        enhanced_parts = [query]
        
        # API-specific context enhancement
        api_patterns = {
            'endpoint': ['api', 'endpoint', 'path', 'method', 'operation'],
            'parameters': ['parameter', 'param', 'query', 'body', 'header'],
            'schema': ['schema', 'definition', 'model', 'object', 'property'],
            'response': ['response', 'return', 'output', 'result', 'status'],
            'authentication': ['auth', 'token', 'key', 'security', 'login'],
            'data_types': ['string', 'integer', 'boolean', 'array', 'object', 'date']
        }
        
        # Add contextual terms based on query intent
        for category, terms in api_patterns.items():
            if any(term in query_lower for term in terms):
                enhanced_parts.extend(terms[:2])  # Add top 2 related terms
                break
        
        # Limit enhancement to prevent noise
        return " ".join(enhanced_parts[:6])

    def _enhanced_rerank_results(self, original_query: str, results) -> List[Dict]:
        """Enhanced re-ranking with semantic weights and chunk type priorities."""
        if not results:
            return []
        
        ranked_results = []
        query_lower = original_query.lower()
        query_words = set(query_lower.split())
        
        for result in results:
            text = result.payload['text']
            text_lower = text.lower()
            text_words = set(text_lower.split())
            
            # Base score from vector similarity
            semantic_score = result.score
            
            # Apply semantic weight from chunk
            chunk_weight = result.payload.get('semantic_weight', 1.0)
            semantic_score *= chunk_weight
            
            # Boost for exact keyword matches
            exact_matches = len(query_words.intersection(text_words))
            if exact_matches > 0:
                semantic_score += (exact_matches / len(query_words)) * 0.15
            
            # Boost for chunk type relevance
            chunk_type = result.payload.get('chunk_type', '')
            type_boost = self._get_chunk_type_boost(query_lower, chunk_type)
            semantic_score += type_boost
            
            # Boost for token density (prefer concise, relevant chunks)
            tokens = result.payload.get('tokens', 100)
            if 50 <= tokens <= 200:  # Sweet spot for focused chunks
                semantic_score += 0.05
            
            # Penalize very generic or short content
            if len(text.split()) < 10:
                semantic_score -= 0.1
            
            ranked_results.append({
                'text': text,
                'score': result.score,
                'semantic_score': min(semantic_score, 1.0),
                'chunk_type': chunk_type,
                'tokens': tokens,
                'metadata': {k: v for k, v in result.payload.items() 
                           if k not in ['text', 'chunk_type', 'tokens', 'semantic_weight']}
            })
        
        return sorted(ranked_results, key=lambda x: x['semantic_score'], reverse=True)

    def _get_chunk_type_boost(self, query: str, chunk_type: str) -> float:
        """Calculate relevance boost based on query intent and chunk type."""
        intent_patterns = {
            'summary': ['what is', 'overview', 'describe', 'about', 'summary'],
            'parameters': ['parameter', 'param', 'input', 'request', 'field'],
            'responses': ['response', 'output', 'return', 'result', 'status'],
            'properties': ['property', 'field', 'attribute', 'column']
        }
        
        for intent, patterns in intent_patterns.items():
            if any(pattern in query for pattern in patterns):
                if intent in chunk_type:
                    return 0.1  # Boost for matching intent
                elif 'summary' in chunk_type and intent != 'summary':
                    return 0.05  # Slight boost for summaries as fallback
        
        return 0.0

    def _apply_hierarchical_filtering(self, query: str, results: List[Dict], limit: int) -> List[Dict]:
        """Apply hierarchical filtering to balance summary and detail chunks."""
        if len(results) <= limit:
            return results
        
        # Separate results by hierarchy level
        summaries = [r for r in results if 'summary' in r.get('chunk_type', '')]
        details = [r for r in results if 'summary' not in r.get('chunk_type', '')]
        
        # For broad queries, prefer summaries
        query_words = len(query.split())
        if query_words <= 3:  # Broad query
            summary_ratio = 0.6
        else:  # Specific query
            summary_ratio = 0.3
        
        summary_limit = int(limit * summary_ratio)
        detail_limit = limit - summary_limit
        
        selected_results = summaries[:summary_limit] + details[:detail_limit]
        
        # Fill remaining slots with best overall scores
        remaining_slots = limit - len(selected_results)
        if remaining_slots > 0:
            remaining_results = [r for r in results if r not in selected_results]
            selected_results.extend(remaining_results[:remaining_slots])
        
        return selected_results
    
    def create_collection(self, collection_name: str) -> None:
        """Create a new collection in Qdrant with enhanced vector configuration."""
        try:
            existing_collections = self.list_collections()
            if collection_name in existing_collections:
                self.logger.info(f"Collection '{collection_name}' already exists")
                return
                
            # Enhanced vector configuration for better precision
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=384,  # all-MiniLM-L6-v2 embedding size
                    distance=Distance.COSINE,
                )
            )
            self.logger.info(f"Created enhanced collection: {collection_name}")
        except Exception as e:
            self.logger.error(f"Failed to create collection {collection_name}: {e}")
            raise
    
    def list_collections(self) -> List[str]:
        """List all available collections."""
        try:
            collections_response = self.client.get_collections()
            collection_names = []
            
            if hasattr(collections_response, 'collections'):
                for collection in collections_response.collections:
                    if hasattr(collection, 'name'):
                        collection_names.append(collection.name)
                    else:
                        collection_names.append(str(collection))
            elif isinstance(collections_response, list):
                for collection in collections_response:
                    if hasattr(collection, 'name'):
                        collection_names.append(collection.name)
                    elif isinstance(collection, dict) and 'name' in collection:
                        collection_names.append(collection['name'])
                    else:
                        collection_names.append(str(collection))
            
            self.logger.info(f"Found {len(collection_names)} collections: {collection_names}")
            return collection_names
        except Exception as e:
            error_msg = f"Error listing collections: {str(e)}"
            self.logger.error(error_msg)
            return []
    
    def delete_collection(self, collection_name: str) -> str:
        """Delete a collection."""
        try:
            self.client.delete_collection(collection_name)
            self.logger.info(f"Deleted collection: {collection_name}")
            return f"Successfully deleted collection '{collection_name}'"
        except Exception as e:
            error_msg = f"Error deleting collection: {str(e)}"
            self.logger.error(error_msg)
            return error_msg


# Use EnhancedRAGSystem as the main RAGSystem class
RAGSystem = EnhancedRAGSystem


# Global RAG system instance
_rag_system = None

def get_rag_system():
    """Get or create the global RAG system instance."""
    global _rag_system
    if _rag_system is None:
        if not QDRANT_AVAILABLE:
            raise ImportError("Qdrant and sentence-transformers are required for RAG functionality")
        _rag_system = RAGSystem()
    return _rag_system


# Public API functions
async def upload_openapi_spec_to_rag(file_path: str, collection_name: str, metadata: Optional[Dict] = None) -> str:
    """
    Upload an OpenAPI specification to the RAG system.
    This is the async version for use in async environments.
    """
    try:
        rag = get_rag_system()
        # Directly await the async implementation
        return await rag._upload_openapi_spec_async(file_path, collection_name, metadata)
    except Exception as e:
        return f"Error: {str(e)}"


def retrieve_from_rag(query: str, collection_name: str, limit: int = 5, score_threshold: float = 0.5, current_path: Optional[str] = None) -> str:
    """Retrieve relevant information from the RAG system and optionally save as markdown."""
    try:
        rag = get_rag_system()
        results = rag.query(query, collection_name, limit, score_threshold)
        
        # If current_path is provided, create markdown and save file
        if current_path:
            # Format results as markdown content
            from datetime import datetime
            
            markdown_content = f"# API Query Results\n\n"
            markdown_content += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            markdown_content += f"**Query:** {query}\n"
            markdown_content += f"**Collection:** {collection_name}\n"
            markdown_content += f"**Results Found:** {len([r for r in results if 'error' not in r])}\n"
            markdown_content += f"**Score Threshold:** {score_threshold}\n"
            markdown_content += f"**Current Path:** {current_path}\n"
            markdown_content += f"\n---\n\n"
            
            # Format each result
            for i, result in enumerate(results, 1):
                if 'error' in result:
                    markdown_content += f"## ❌ Error\n\n{result['error']}\n\n"
                else:
                    markdown_content += f"## 📋 Result {i} (Score: {result['score']:.3f})\n\n"
                    markdown_content += f"```\n{result['text']}\n```\n\n"
                    
                    # Add metadata if available
                    if 'metadata' in result and result['metadata']:
                        markdown_content += f"**Metadata:**\n"
                        for key, value in result['metadata'].items():
                            markdown_content += f"- {key}: `{value}`\n"
                        markdown_content += f"\n"
            
            # Save markdown file
            try:
                import os
                
                # Use the provided current_path
                current_dir = Path(current_path)
                if not current_dir.exists():
                    return f"Error: Provided path does not exist: {current_path}"
                if not os.access(current_dir, os.W_OK):
                    return f"Error: No write permission for path: {current_path}"
                
                # Create outputs subdirectory to keep files organized
                outputs_dir = current_dir / "outputs"
                outputs_dir.mkdir(exist_ok=True)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                # Clean query for filename (remove special chars, limit length)
                safe_query = "".join(c for c in query if c.isalnum() or c in (' ', '_')).strip()
                safe_query = safe_query.replace(' ', '_')[:30]
                filename = f"query_{safe_query}_{timestamp}.md"
                filepath = outputs_dir / filename
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                
                return f"Query completed successfully!\n\nResults: {len([r for r in results if 'error' not in r])} relevant documents found\nMarkdown report saved to: {filepath}\n\n{markdown_content}"
                
            except Exception as e:
                # Fallback: save to home directory
                try:
                    home_dir = Path.home() / "mcp_query_output"
                    home_dir.mkdir(exist_ok=True)
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    safe_query = "".join(c for c in query if c.isalnum() or c in (' ', '_')).strip()
                    safe_query = safe_query.replace(' ', '_')[:30]
                    filename = f"query_{safe_query}_{timestamp}.md"
                    filepath = home_dir / filename
                    
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(markdown_content)
                    
                    return f"Query completed! Markdown saved to home directory: {filepath}\n\n{markdown_content}"
                    
                except Exception as final_error:
                    return f"Query completed but file save failed: {str(e)}, Final fallback failed: {str(final_error)}\n\n{markdown_content}"
        
        else:
            # Return the original JSON format for backward compatibility when no current_path
            import json
            return json.dumps(results, indent=2)
        
    except Exception as e:
        return f"Error: Retrieval failed: {str(e)}"


def list_rag_collections() -> str:
    """List all available RAG collections."""
    try:
        rag = get_rag_system()
        collections = rag.list_collections()
        
        if not collections:
            return "No collections available. Upload an OpenAPI specification first using the 'upload_api_specification' tool."
        
        return f"Available collections ({len(collections)}): {', '.join(collections)}"
    except Exception as e:
        return f"Error listing collections: {str(e)}"


def delete_rag_collection(collection_name: str) -> str:
    """Delete a RAG collection."""
    try:
        rag = get_rag_system()
        return rag.delete_collection(collection_name)
    except Exception as e:
        return f"Error: {str(e)}"


def analyze_fields_with_rag_and_llm(fields: List[str], collection_name: str, context_topic: Optional[str] = None, current_path: Optional[str] = None) -> str:
    """Analyze fields using RAG retrieval and LLM synthesis with enhanced context searching."""
    try:
        # Create search queries for the fields
        field_context = {}
        rag = get_rag_system()
        
        for field in fields:
            # Enhanced search queries with broader context patterns
            queries = [
                f"{field}",  # Direct field name
                f"{field} parameter definition",
                f"{field} property field",
                f"{field} data type schema",
                f"endpoint {field} request",  # Context: where field is used
                f"response {field} object",   # Context: response structure
                f"{field} validation rules"   # Context: validation/constraints
            ]
            
            # Add context-specific queries if provided
            if context_topic:
                queries.extend([
                    f"{context_topic} {field}",
                    f"{field} {context_topic} API"
                ])
            
            all_results = []
            for query in queries:
                results = rag.query(query, collection_name, limit=4, score_threshold=0.25)
                all_results.extend(results)
            
            # Remove duplicates and sort by score
            unique_results = {}
            for result in all_results:
                if 'error' not in result:
                    text = result['text']
                    if text not in unique_results or result['score'] > unique_results[text]['score']:
                        unique_results[text] = result
            
            field_context[field] = list(unique_results.values())[:3]  # Top 3 results
        
        # Create LLM prompt
        context_str = ""
        if context_topic:
            context_str = f"Context: {context_topic}\n\n"
        
        prompt = f"""{context_str}Analyze the following fields based on the API documentation context provided:

Fields to analyze: {', '.join(fields)}

API Documentation Context:
"""
        
        for field, results in field_context.items():
            prompt += f"\n--- {field} ---\n"
            for result in results:
                if 'error' not in result:
                    prompt += f"Score: {result['score']:.3f}\n{result['text']}\n\n"
        
        prompt += """
        TASK:
        For each field in extracted_fields, create a comprehensive semantic analysis:

        1. **Semantic Description**: Detailed description of what the field means/purpose and represents, 1 sentence
        2. **Synonyms**: Alternative names in other systems (e.g. emp_id, worker_id for employee_id)
        3. **Possible Datatypes**: Which data types are possible (string, integer, date, boolean, etc.)
        4. **Business Context**: Classification in the business context, where is the field used?

        IMPORTANT RULES:s
        - SHORT, concise descriptions (max. 50 words per field)
        - MAXIMUM 3 synonyms per field
        - MAXIMUM 3 data types per field  
        - Answer ONLY with valid JSON, NO Markdown blocks


        Format your response as structured text with clear sections for each field."""
        
        # Get LLM response
        response = get_llm_response(prompt)
        
        # Save result as MD file with unique name in the USER'S current working directory
        try:
            from datetime import datetime
            import os
            
            # Use the provided current_path or detect the user's actual current directory
            if current_path:
                # User provided specific path - use it directly
                current_dir = Path(current_path)
                if not current_dir.exists():
                    return response + f"\n\n⚠️ Provided path does not exist: {current_path}"
                if not os.access(current_dir, os.W_OK):
                    return response + f"\n\n⚠️ No write permission for path: {current_path}"
            else:
                # Fallback to detecting user's current directory from environment
                try:
                    # Try to get the user's actual current directory
                    user_cwd = os.environ.get('PWD', None) or os.getcwd()
                    current_dir = Path(user_cwd)
                    
                    # Verify this directory exists and is writable
                    if not current_dir.exists() or not os.access(current_dir, os.W_OK):
                        # Fall back to user's home directory if current dir isn't writable
                        current_dir = Path.home()
                        
                except Exception:
                    # Final fallback to home directory
                    current_dir = Path.home()
            
            # Create outputs subdirectory to keep files organized
            outputs_dir = current_dir / "outputs"
            outputs_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            fields_name = "_".join(fields[:2])[:30]  # First 2 fields, max 30 chars
            filename = f"analysis_{fields_name}_{timestamp}.md"
            filepath = outputs_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# API Fields Analysis\n\n")
                f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Collection:** {collection_name}\n")
                f.write(f"**Fields:** {', '.join(fields)}\n")
                if current_path:
                    f.write(f"**Current Path:** {current_path}\n")
                f.write(f"\n")
                f.write(response)
            
            response += f"\n\n📄 Saved to: {filepath}"
            
        except Exception as e:
            # Final fallback: create file in user's home directory
            try:
                home_dir = Path.home() / "mcp_analysis_output"
                home_dir.mkdir(exist_ok=True)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                fields_name = "_".join(fields[:2])[:30]
                filename = f"analysis_{fields_name}_{timestamp}.md"
                filepath = home_dir / filename
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"# API Fields Analysis\n\n")
                    f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"**Collection:** {collection_name}\n")
                    f.write(f"**Fields:** {', '.join(fields)}\n")
                    if current_path:
                        f.write(f"**Current Path:** {current_path}\n")
                    f.write(f"\n")
                    f.write(response)
                
                response += f"\n\n📄 Saved to home: {filepath}"
                
            except Exception as final_error:
                response += f"\n\n⚠️ File save failed: {str(e)}, Final fallback failed: {str(final_error)}"
        
        return response
        
    except Exception as e:
        return f"Error analyzing fields: {str(e)}"


def enhance_csv_with_rag(csv_file_path: str, collection_name: str, context_query: str, output_dir: Optional[str] = None) -> str:
    """Enhance a CSV file using RAG system for context and LLM for insights."""
    try:
        # Read CSV
        df = pd.read_csv(csv_file_path)
        
        # Get relevant context from RAG
        rag = get_rag_system()
        context_results = rag.query(context_query, collection_name, limit=5, score_threshold=0.3)
        
        # Prepare context for LLM
        context_text = "\n".join([
            f"Score: {result['score']:.3f}\n{result['text']}"
            for result in context_results if 'error' not in result
        ])
        
        # Create LLM prompt
        prompt = f"""Based on the following API documentation context, analyze this CSV data and provide business insights:

API Context:
{context_text}

CSV Data (first 5 rows):
{df.head().to_string()}

CSV Columns: {', '.join(df.columns.tolist())}
Total Rows: {len(df)}

Please provide:
1. Business interpretation of the data based on the API context
2. Key insights and patterns
3. Potential data quality issues
4. Recommendations for data usage
5. Field mappings to API endpoints if applicable

Format your response as a structured analysis."""
        
        # Get LLM insights
        insights = get_llm_response(prompt)
        
        # Prepare output directory
        if output_dir is None:
            output_dir = Path(csv_file_path).parent
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(exist_ok=True)
        
        # Save enhanced files
        base_name = Path(csv_file_path).stem
        
        # Save insights
        insights_file = output_dir / f"{base_name}_insights.txt"
        with open(insights_file, 'w', encoding='utf-8') as f:
            f.write(insights)
        
        # Save context
        context_file = output_dir / f"{base_name}_context.json"
        with open(context_file, 'w', encoding='utf-8') as f:
            json.dump(context_results, f, indent=2)
        
        return f"Enhanced CSV analysis saved to:\n- Insights: {insights_file}\n- Context: {context_file}"
        
    except Exception as e:
        return f"Error enhancing CSV: {str(e)}"


def test_rag_system() -> str:
    """Test the RAG system functionality."""
    try:
        if not QDRANT_AVAILABLE:
            return "❌ RAG System Test Failed: Missing dependencies (sentence-transformers, qdrant-client)"
        
        rag = get_rag_system()
        collections = rag.list_collections()
        
        return f"✅ RAG System Test Successful: {len(collections)} collections available"
    except Exception as e:
        return f"❌ RAG System Test Error: {str(e)}"


def upload_openapi_spec_async(file_path: str, collection_name: str, metadata: Optional[Dict] = None) -> 'coroutine':
    """
    Public async API for uploading an OpenAPI specification to the RAG system.
    Use this in async environments: await upload_openapi_spec_async(...)
    """
    rag = get_rag_system()
    return rag._upload_openapi_spec_async(file_path, collection_name, metadata)


class RAGTools:
    """
    Wrapper class for all RAG tools to provide a unified interface.
    This class wraps all the existing RAG functions to make them accessible as methods.
    """
    
    def __init__(self):
        """Initialize the RAG tools wrapper."""
        self.rag_system = None
    
    def _ensure_rag_system(self):
        """Ensure RAG system is initialized."""
        if self.rag_system is None:
            self.rag_system = get_rag_system()
        return self.rag_system
    
    def test_rag_system(self) -> str:
        """Test the RAG system functionality."""
        return test_rag_system()
    
    def list_rag_collections(self) -> str:
        """List all available RAG collections."""
        return list_rag_collections()
    
    def upload_openapi_spec_to_rag(self, file_path: str, collection_name: str, metadata: Optional[Dict] = None) -> str:
        """Upload an OpenAPI specification to the RAG system."""
        return upload_openapi_spec_to_rag(file_path, collection_name, metadata)
    
    def retrieve_from_rag(self, query: str, collection_name: str, limit: int = 5, score_threshold: float = 0.5, current_path: Optional[str] = None) -> str:
        """Retrieve relevant information from the RAG system."""
        return retrieve_from_rag(query, collection_name, limit, score_threshold, current_path)
    
    def delete_rag_collection(self, collection_name: str) -> str:
        """Delete a RAG collection."""
        return delete_rag_collection(collection_name)
    
    def analyze_fields_with_rag_and_llm(self, fields: List[str], collection_name: str, context_topic: Optional[str] = None, current_path: Optional[str] = None) -> str:
        """Analyze fields using RAG retrieval and LLM synthesis."""
        return analyze_fields_with_rag_and_llm(fields, collection_name, context_topic, current_path)
    
    def enhance_csv_with_rag(self, csv_file_path: str, collection_name: str, context_query: str, output_dir: Optional[str] = None) -> str:
        """Enhance a CSV file using RAG system for context and LLM for insights."""
        return enhance_csv_with_rag(csv_file_path, collection_name, context_query, output_dir)
    
    # Async methods
    async def upload_openapi_spec_to_rag_async(self, file_path: str, collection_name: str, metadata: Optional[Dict] = None) -> str:
        """Upload an OpenAPI specification to the RAG system (async version)."""
        return await upload_openapi_spec_to_rag(file_path, collection_name, metadata)
    
    async def upload_openapi_spec_async(self, file_path: str, collection_name: str, metadata: Optional[Dict] = None) -> str:
        """Public async API for uploading an OpenAPI specification to the RAG system."""
        rag = self._ensure_rag_system()
        return await rag._upload_openapi_spec_async(file_path, collection_name, metadata)