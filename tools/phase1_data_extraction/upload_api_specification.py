"""
Optimized RAG Tools for OpenAPI Specification Analysis
Enhanced with semantic chunking, intelligent matching, and advanced re-ranking
"""

import os
import json
import logging
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

# Add dotenv support for environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, will use system env vars

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    from sentence_transformers import SentenceTransformer
    import yaml
    import tiktoken
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

from tools.shared_utilities.llm_client import get_llm_response

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
    
    def _prune_vendor_extensions(self, obj: Dict) -> Dict:
        """Remove vendor-specific extensions (x-* fields)."""
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
                chunk_text = " ".join(current_chunk)
                chunks.append(chunk_text)
                
                # Create overlap
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
    
    def _build_info_chunks(self, spec: Dict) -> List[DocumentChunk]:
        chunks: List[DocumentChunk] = []
        if 'info' in spec:
            info = self._prune_vendor_extensions(spec['info'])
            info_parts = [f"API: {info.get('title', 'Unknown')} v{info.get('version', '1.0')}"]
            if 'description' in info:
                info_parts.append(f"Description: {info['description']}")
            if 'contact' in info:
                contact = info['contact']
                if 'name' in contact:
                    info_parts.append(f"Contact: {contact['name']}")
                if 'email' in contact:
                    info_parts.append(f"Email: {contact['email']}")
            text = "\n".join(info_parts)
            chunks.append(DocumentChunk(
                text=text,
                chunk_type='info',
                metadata={'type': 'info'},
                tokens=self._count_tokens(text),
                semantic_weight=1.3
            ))
        return chunks

    def _build_operation_chunks(self, spec: Dict) -> List[DocumentChunk]:
        chunks: List[DocumentChunk] = []
        if 'paths' in spec:
            for path, methods in spec['paths'].items():
                # Path-level metadata and parameters
                if isinstance(methods, dict):
                    path_meta_parts: List[str] = []
                    if 'summary' in methods:
                        path_meta_parts.append(f"Path Summary: {methods['summary']}")
                    if 'description' in methods:
                        path_meta_parts.append(f"Path Description: {methods['description']}")
                    if 'servers' in methods and isinstance(methods['servers'], list) and methods['servers']:
                        servers_list = []
                        for srv in methods['servers']:
                            url = srv.get('url') if isinstance(srv, dict) else None
                            if url:
                                servers_list.append(url)
                        if servers_list:
                            path_meta_parts.append(f"Path Servers: {', '.join(servers_list[:3])}")
                    if path_meta_parts:
                        text = "\n".join(path_meta_parts)
                        chunks.append(DocumentChunk(
                            text=text,
                            chunk_type='path_metadata',
                            metadata={'type': 'path_metadata', 'path': path},
                            tokens=self._count_tokens(text),
                            semantic_weight=1.0
                        ))

                    if 'parameters' in methods and isinstance(methods['parameters'], list) and methods['parameters']:
                        param_parts = [f"Path Parameters for {path}:"]
                        for param in methods['parameters']:
                            param = self._prune_vendor_extensions(param)
                            ptxt = f"• {param.get('name', 'unnamed')}"
                            if 'in' in param:
                                ptxt += f" (in: {param['in']})"
                            if param.get('required'):
                                ptxt += " - REQUIRED"
                            schema = param.get('schema', {})
                            if isinstance(schema, dict) and 'type' in schema:
                                ptxt += f" - type: {schema['type']}"
                            if 'description' in param:
                                ptxt += f" - {param['description']}"
                            param_parts.append(ptxt)
                        text = "\n".join(param_parts)
                        chunks.append(DocumentChunk(
                            text=text,
                            chunk_type='path_parameters',
                            metadata={'type': 'path_parameters', 'path': path},
                            tokens=self._count_tokens(text),
                            semantic_weight=1.0
                        ))
                for method, operation in methods.items():
                    if not isinstance(operation, dict):
                        continue
                    operation = self._prune_vendor_extensions(operation)

                    # Operation metadata
                    op_parts = [f"Operation: {method.upper()} {path}"]
                    if 'operationId' in operation:
                        op_parts.append(f"Operation ID: {operation['operationId']}")
                    if 'tags' in operation and operation['tags']:
                        op_parts.append(f"Tags: {', '.join(operation['tags'])}")
                    if 'summary' in operation:
                        op_parts.append(f"Summary: {operation['summary']}")
                    if 'description' in operation:
                        op_parts.append(f"Description: {operation['description']}")
                    text = "\n".join(op_parts)
                    chunks.append(DocumentChunk(
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
                    ))

                    # Parameters
                    if 'parameters' in operation and operation['parameters']:
                        param_parts = [f"Parameters for {method.upper()} {path}:"]
                        for param in operation['parameters']:
                            param = self._prune_vendor_extensions(param)
                            param_text = f"• {param.get('name', 'unnamed')}"
                            if 'in' in param:
                                param_text += f" (in: {param['in']})"
                            if 'required' in param and param['required']:
                                param_text += " - REQUIRED"
                            schema = param.get('schema', {})
                            if 'type' in schema:
                                param_text += f" - type: {schema['type']}"
                            if 'description' in param:
                                param_text += f" - {param['description']}"
                            param_parts.append(param_text)
                        text = "\n".join(param_parts)
                        chunks.append(DocumentChunk(
                            text=text,
                            chunk_type='operation_parameters',
                            metadata={'type': 'operation_parameters', 'path': path, 'method': method.lower()},
                            tokens=self._count_tokens(text),
                            semantic_weight=1.0
                        ))

                    # Request Body
                    if 'requestBody' in operation and isinstance(operation['requestBody'], dict):
                        rb = self._prune_vendor_extensions(operation['requestBody'])
                        rb_parts = [f"Request Body for {method.upper()} {path}:"]
                        if rb.get('required'):
                            rb_parts.append("- REQUIRED")
                        if 'description' in rb:
                            rb_parts.append(f"- Description: {rb['description']}")
                        content = rb.get('content', {}) if isinstance(rb.get('content', {}), dict) else {}
                        if content:
                            for ctype, cdata in content.items():
                                c_line = f"• Content-Type: {ctype}"
                                if isinstance(cdata, dict):
                                    schema = cdata.get('schema')
                                    if isinstance(schema, dict):
                                        if '$ref' in schema:
                                            c_line += f" - schema: {schema['$ref']}"
                                        elif 'type' in schema:
                                            c_line += f" - schema.type: {schema['type']}"
                                    # examples
                                    example = cdata.get('example')
                                    if example is not None:
                                        c_line += " - example: present"
                                    examples = cdata.get('examples')
                                    if isinstance(examples, dict) and examples:
                                        c_line += f" - examples: {', '.join(list(examples.keys())[:3])}"
                                rb_parts.append(c_line)
                        text = "\n".join(rb_parts)
                        chunks.append(DocumentChunk(
                            text=text,
                            chunk_type='operation_request_body',
                            metadata={'type': 'operation_request_body', 'path': path, 'method': method.lower()},
                            tokens=self._count_tokens(text),
                            semantic_weight=1.0
                        ))

                    # Responses
                    if 'responses' in operation:
                        resp_parts = [f"Responses for {method.upper()} {path}:"]
                        for status_code, response in operation['responses'].items():
                            response = self._prune_vendor_extensions(response)
                            resp_text = f"• Status {status_code}"
                            if 'description' in response:
                                resp_text += f": {response['description']}"
                            if 'content' in response:
                                content_types = list(response['content'].keys())
                                resp_text += f" - Content-Type: {', '.join(content_types)}"
                                # indicate examples presence
                                try:
                                    for ctype, cdata in response['content'].items():
                                        if isinstance(cdata, dict):
                                            if 'example' in cdata:
                                                resp_text += " - example: present"
                                                break
                                            if isinstance(cdata.get('examples'), dict) and cdata.get('examples'):
                                                example_keys = list(cdata['examples'].keys())
                                                if example_keys:
                                                    resp_text += f" - examples: {', '.join(example_keys[:3])}"
                                                    break
                                except Exception:
                                    pass
                            resp_parts.append(resp_text)
                        text = "\n".join(resp_parts)
                        chunks.append(DocumentChunk(
                            text=text,
                            chunk_type='operation_responses',
                            metadata={'type': 'operation_responses', 'path': path, 'method': method.lower()},
                            tokens=self._count_tokens(text),
                            semantic_weight=0.9
                        ))
        return chunks

    def _build_root_chunks(self, spec: Dict) -> List[DocumentChunk]:
        chunks: List[DocumentChunk] = []
        # Servers
        if isinstance(spec.get('servers'), list) and spec['servers']:
            srv_lines: List[str] = ["Servers:"]
            for srv in spec['servers'][:10]:
                if isinstance(srv, dict):
                    url = srv.get('url', '')
                    desc = srv.get('description')
                    line = f"• {url}" if url else "• server"
                    if desc:
                        line += f" - {desc}"
                    srv_lines.append(line)
            text = "\n".join(srv_lines)
            chunks.append(DocumentChunk(
                text=text,
                chunk_type='servers',
                metadata={'type': 'servers'},
                tokens=self._count_tokens(text),
                semantic_weight=1.0
            ))
        # Tags
        if isinstance(spec.get('tags'), list) and spec['tags']:
            tag_lines: List[str] = ["Tags:"]
            for tag in spec['tags'][:50]:
                if isinstance(tag, dict):
                    name = tag.get('name', 'unnamed')
                    desc = tag.get('description')
                    line = f"• {name}"
                    if desc:
                        line += f": {desc}"
                    tag_lines.append(line)
            text = "\n".join(tag_lines)
            chunks.append(DocumentChunk(
                text=text,
                chunk_type='tags',
                metadata={'type': 'tags'},
                tokens=self._count_tokens(text),
                semantic_weight=0.9
            ))
        # externalDocs
        if isinstance(spec.get('externalDocs'), dict):
            ed = spec['externalDocs']
            url = ed.get('url')
            desc = ed.get('description')
            parts = ["External Docs:"]
            if url:
                parts.append(f"• {url}")
            if desc:
                parts.append(f"{desc}")
            text = "\n".join(parts)
            chunks.append(DocumentChunk(
                text=text,
                chunk_type='external_docs',
                metadata={'type': 'external_docs'},
                tokens=self._count_tokens(text),
                semantic_weight=0.8
            ))
        return chunks

    def _build_components_chunks(self, spec: Dict) -> List[DocumentChunk]:
        chunks: List[DocumentChunk] = []
        components = spec.get('components', {})
        if not isinstance(components, dict):
            return chunks

        # Parameters
        params = components.get('parameters', {})
        if isinstance(params, dict) and params:
            lines: List[str] = ["Components/Parameters:"]
            for name, p in list(params.items())[:200]:
                if not isinstance(p, dict):
                    continue
                p = self._prune_vendor_extensions(p)
                line = f"• {name}"
                if p.get('in'):
                    line += f" (in: {p['in']})"
                if p.get('required'):
                    line += " - REQUIRED"
                schema = p.get('schema', {})
                if isinstance(schema, dict) and schema.get('type'):
                    line += f" - type: {schema['type']}"
                if p.get('description'):
                    line += f" - {p['description']}"
                lines.append(line)
            text = "\n".join(lines)
            for chunk_text in self._sliding_window_chunks(text):
                chunks.append(DocumentChunk(
                    text=chunk_text,
                    chunk_type='components_parameters',
                    metadata={'type': 'components_parameters'},
                    tokens=self._count_tokens(chunk_text),
                    semantic_weight=1.0
                ))

        # RequestBodies
        rbs = components.get('requestBodies', {})
        if isinstance(rbs, dict) and rbs:
            lines = ["Components/RequestBodies:"]
            for name, rb in list(rbs.items())[:200]:
                if not isinstance(rb, dict):
                    continue
                rb = self._prune_vendor_extensions(rb)
                line = f"• {name}"
                if rb.get('required'):
                    line += " - REQUIRED"
                if rb.get('description'):
                    line += f" - {rb['description']}"
                content = rb.get('content', {})
                if isinstance(content, dict) and content:
                    ctypes = list(content.keys())
                    line += f" - content: {', '.join(ctypes[:3])}"
                lines.append(line)
            text = "\n".join(lines)
            for chunk_text in self._sliding_window_chunks(text):
                chunks.append(DocumentChunk(
                    text=chunk_text,
                    chunk_type='components_request_bodies',
                    metadata={'type': 'components_request_bodies'},
                    tokens=self._count_tokens(chunk_text),
                    semantic_weight=0.95
                ))

        # Responses
        resps = components.get('responses', {})
        if isinstance(resps, dict) and resps:
            lines = ["Components/Responses:"]
            for name, resp in list(resps.items())[:200]:
                if not isinstance(resp, dict):
                    continue
                resp = self._prune_vendor_extensions(resp)
                line = f"• {name}"
                if resp.get('description'):
                    line += f": {resp['description']}"
                content = resp.get('content', {})
                if isinstance(content, dict) and content:
                    ctypes = list(content.keys())
                    line += f" - content: {', '.join(ctypes[:3])}"
                lines.append(line)
            text = "\n".join(lines)
            for chunk_text in self._sliding_window_chunks(text):
                chunks.append(DocumentChunk(
                    text=chunk_text,
                    chunk_type='components_responses',
                    metadata={'type': 'components_responses'},
                    tokens=self._count_tokens(chunk_text),
                    semantic_weight=0.95
                ))

        # Examples
        exs = components.get('examples', {})
        if isinstance(exs, dict) and exs:
            lines = ["Components/Examples:"]
            for name, ex in list(exs.items())[:200]:
                if not isinstance(ex, dict):
                    continue
                line = f"• {name}"
                if ex.get('summary'):
                    line += f" - {ex['summary']}"
                elif ex.get('description'):
                    line += f" - {ex['description']}"
                if 'value' in ex:
                    line += " - value: present"
                lines.append(line)
            text = "\n".join(lines)
            for chunk_text in self._sliding_window_chunks(text):
                chunks.append(DocumentChunk(
                    text=chunk_text,
                    chunk_type='components_examples',
                    metadata={'type': 'components_examples'},
                    tokens=self._count_tokens(chunk_text),
                    semantic_weight=0.8
                ))

        # Headers
        headers = components.get('headers', {})
        if isinstance(headers, dict) and headers:
            lines = ["Components/Headers:"]
            for name, h in list(headers.items())[:200]:
                if not isinstance(h, dict):
                    continue
                line = f"• {name}"
                schema = h.get('schema', {})
                if isinstance(schema, dict) and schema.get('type'):
                    line += f" - type: {schema['type']}"
                if h.get('description'):
                    line += f" - {h['description']}"
                lines.append(line)
            text = "\n".join(lines)
            for chunk_text in self._sliding_window_chunks(text):
                chunks.append(DocumentChunk(
                    text=chunk_text,
                    chunk_type='components_headers',
                    metadata={'type': 'components_headers'},
                    tokens=self._count_tokens(chunk_text),
                    semantic_weight=0.8
                ))

        # Security Schemes
        sec = components.get('securitySchemes', {})
        if isinstance(sec, dict) and sec:
            lines = ["Components/SecuritySchemes:"]
            for name, s in list(sec.items())[:200]:
                if not isinstance(s, dict):
                    continue
                stype = s.get('type')
                line = f"• {name}"
                if stype:
                    line += f" - type: {stype}"
                if s.get('scheme'):
                    line += f" - scheme: {s['scheme']}"
                if s.get('bearerFormat'):
                    line += f" - bearerFormat: {s['bearerFormat']}"
                lines.append(line)
            text = "\n".join(lines)
            for chunk_text in self._sliding_window_chunks(text):
                chunks.append(DocumentChunk(
                    text=chunk_text,
                    chunk_type='components_security_schemes',
                    metadata={'type': 'components_security_schemes'},
                    tokens=self._count_tokens(chunk_text),
                    semantic_weight=1.0
                ))

        # Links
        links = components.get('links', {})
        if isinstance(links, dict) and links:
            lines = ["Components/Links:"]
            for name, l in list(links.items())[:200]:
                if not isinstance(l, dict):
                    continue
                line = f"• {name}"
                if l.get('operationId'):
                    line += f" - operationId: {l['operationId']}"
                elif l.get('operationRef'):
                    line += f" - operationRef: {l['operationRef']}"
                lines.append(line)
            text = "\n".join(lines)
            for chunk_text in self._sliding_window_chunks(text):
                chunks.append(DocumentChunk(
                    text=chunk_text,
                    chunk_type='components_links',
                    metadata={'type': 'components_links'},
                    tokens=self._count_tokens(chunk_text),
                    semantic_weight=0.7
                ))

        # Callbacks
        callbacks = components.get('callbacks', {})
        if isinstance(callbacks, dict) and callbacks:
            lines = ["Components/Callbacks:"]
            for name, cb in list(callbacks.items())[:200]:
                line = f"• {name}"
                lines.append(line)
            text = "\n".join(lines)
            for chunk_text in self._sliding_window_chunks(text):
                chunks.append(DocumentChunk(
                    text=chunk_text,
                    chunk_type='components_callbacks',
                    metadata={'type': 'components_callbacks'},
                    tokens=self._count_tokens(chunk_text),
                    semantic_weight=0.6
                ))

        return chunks

    def _build_schema_chunks(self, spec: Dict) -> List[DocumentChunk]:
        chunks: List[DocumentChunk] = []
        schemas = spec.get('components', {}).get('schemas', {}) or spec.get('definitions', {})
        for schema_name, schema_data in schemas.items():
            schema_data = self._prune_vendor_extensions(schema_data)

            # Schema summary
            summary_parts = [f"Schema: {schema_name}"]
            if 'type' in schema_data:
                summary_parts.append(f"Type: {schema_data['type']}")
            if 'description' in schema_data:
                summary_parts.append(f"Description: {schema_data['description']}")
            if 'required' in schema_data and isinstance(schema_data['required'], list):
                summary_parts.append(f"Required Fields: {', '.join(schema_data['required'])}")
            text = "\n".join(summary_parts)
            chunks.append(DocumentChunk(
                text=text,
                chunk_type='schema_summary',
                metadata={'type': 'schema_summary', 'schema_name': schema_name},
                tokens=self._count_tokens(text),
                semantic_weight=1.1
            ))

            # Properties (no semantic grouping)
            if 'properties' in schema_data:
                prop_lines: List[str] = [f"Properties for {schema_name}:"]
                for prop_name, prop_data in schema_data['properties'].items():
                    line = f"• {prop_name}"
                    if isinstance(prop_data, dict):
                        if 'type' in prop_data:
                            line += f" ({prop_data['type']})"
                        if 'description' in prop_data:
                            line += f": {prop_data['description']}"
                        if 'enum' in prop_data:
                            enum_values = prop_data['enum'][:3]
                            line += f" - values: {', '.join(map(str, enum_values))}"
                    prop_lines.append(line)
                text = "\n".join(prop_lines)
                text_chunks = self._sliding_window_chunks(text)
                for i, chunk_text in enumerate(text_chunks):
                    tokens = self._count_tokens(chunk_text)
                    if tokens >= self.config.min_tokens or (len(text_chunks) == 1 and i == 0):
                        chunks.append(DocumentChunk(
                            text=chunk_text,
                            chunk_type='schema_properties',
                            metadata={'type': 'schema_properties', 'schema_name': schema_name, 'chunk_index': i if len(text_chunks) > 1 else None},
                            tokens=tokens,
                            semantic_weight=1.0
                        ))
        return chunks

    def _extract_comprehensive_api_content(self, spec: Dict) -> List[DocumentChunk]:
        """Extract comprehensive API content with semantic chunking (refactored)."""
        chunks: List[DocumentChunk] = []
        chunks.extend(self._build_info_chunks(spec))
        chunks.extend(self._build_root_chunks(spec))
        chunks.extend(self._build_operation_chunks(spec))
        chunks.extend(self._build_schema_chunks(spec))
        chunks.extend(self._build_components_chunks(spec))
        return chunks
    
    def upload_spec(self, file_path: str, collection_name: str) -> str:
        """Upload API spec with optimized chunking."""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return f"❌ File not found: {file_path}"
            
            # Load spec
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.suffix.lower() in ['.yaml', '.yml']:
                    spec = yaml.safe_load(f)
                else:
                    spec = json.load(f)
            
            # Create collection
            self.create_collection(collection_name)
            
            # Extract comprehensive content
            chunks = self._extract_comprehensive_api_content(spec)
            
            # Create embeddings and points
            points = []
            for i, chunk in enumerate(chunks):
                embedding = self.encoder.encode(chunk.text).tolist()
                points.append(PointStruct(
                    id=i,
                    vector=embedding,
                    payload={
                        'text': chunk.text,
                        'chunk_type': chunk.chunk_type,
                        'tokens': chunk.tokens,
                        'semantic_weight': chunk.semantic_weight,
                        **chunk.metadata
                    }
                ))
            
            # Upload in batches
            batch_size = self.config.batch_size
            for i in range(0, len(points), batch_size):
                batch_points = points[i:i + batch_size]
                self.client.upsert(collection_name=collection_name, points=batch_points)
            
            # Statistics
            total_tokens = sum(chunk.tokens for chunk in chunks)
            avg_tokens = total_tokens / len(chunks) if chunks else 0
            chunk_types = set(chunk.chunk_type for chunk in chunks)
            
            return (f"✅ Optimized upload successful!\n"
                   f"📄 File: {file_path.name}\n"
                   f"📊 Chunks: {len(chunks)} semantic chunks\n"
                   f"🎯 Avg tokens/chunk: {avg_tokens:.1f}\n"
                   f"📝 Total tokens: {total_tokens:,}\n"
                   f"🏷️ Collection: '{collection_name}'\n"
                   f"🔍 Chunk types: {', '.join(sorted(chunk_types))}")
        
        except Exception as e:
            return f"❌ Upload failed: {str(e)}"
    
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

    def upload_markdown(self, file_path: str, collection_name: str, metadata: Optional[Dict] = None) -> str:
        """Upload a Markdown/text document into a collection with heading-aware chunks.

        - Splits by headings (#, ##, ###) and also enforces token windows (~800-1200 tokens) with ~100 token overlap.
        - Attaches metadata for filtering (doc, section, phase, topics, severity, version, updated_at) if provided.
        """
        try:
            p = Path(file_path)
            if not p.exists():
                return f"❌ File not found: {file_path}"

            text = p.read_text(encoding="utf-8")

            # Extract YAML front-matter if present
            fm: Dict[str, Any] = {}
            if text.startswith("---\n"):
                try:
                    end = text.find("\n---\n", 4)
                    if end != -1:
                        fm_block = text[4:end]
                        fm = yaml.safe_load(fm_block) or {}
                        text = text[end + 5 :]
                except Exception:
                    pass

            # Simple heading-based splitter
            lines = text.splitlines()
            chunks: List[Tuple[str, str]] = []  # (section_title, section_text)
            current_title = "Intro"
            current_lines: List[str] = []

            def flush():
                if current_lines:
                    chunks.append((current_title, "\n".join(current_lines).strip()))

            for line in lines:
                if line.startswith("# ") or line.startswith("## ") or line.startswith("### "):
                    flush()
                    current_title = line.lstrip("# ").strip() or current_title
                    current_lines = []
                else:
                    current_lines.append(line)
            flush()

            # Token-window sub-chunking with ~100 token overlap
            def count_tokens(txt: str) -> int:
                return self._count_tokens(txt)

            window_min, window_max, overlap = 800, 1200, 100
            final_chunks: List[Tuple[str, str]] = []

            for title, body in chunks:
                words = body.split()
                buf: List[str] = []
                start_idx = 0
                i = 0
                while i < len(words):
                    buf.append(words[i])
                    if count_tokens(" ".join(buf)) >= window_max:
                        # emit chunk
                        final_chunks.append((title, " ".join(buf)))
                        # overlap window
                        overlap_words = []
                        j = len(buf) - 1
                        overlap_count = 0
                        while j >= 0 and overlap_count < overlap:
                            w = buf[j]
                            t = count_tokens(w + " ")
                            if overlap_count + t > overlap:
                                break
                            overlap_words.insert(0, w)
                            overlap_count += t
                            j -= 1
                        buf = overlap_words[:]
                    i += 1
                if buf and count_tokens(" ".join(buf)) >= window_min:
                    final_chunks.append((title, " ".join(buf)))
                elif buf and not final_chunks:
                    # small document fallback
                    final_chunks.append((title, " ".join(buf)))

            # Ensure collection exists
            self.create_collection(collection_name)

            # Prepare points
            from qdrant_client.models import PointStruct
            points: List[PointStruct] = []
            base_meta = {"doc": p.name}
            if metadata:
                base_meta.update(metadata)
            if fm:
                base_meta.update(fm)

            for idx, (title, chunk_text) in enumerate(final_chunks):
                vec = self.encoder.encode(chunk_text).tolist()
                payload = {
                    "text": chunk_text,
                    "chunk_type": "learning",
                    "tokens": count_tokens(chunk_text),
                    "section": title,
                    **base_meta,
                }
                points.append(
                    PointStruct(
                        id=int(datetime.now().timestamp() * 1_000_000) + idx,
                        vector=vec,
                        payload=payload,
                    )
                )

            if points:
                self.client.upsert(collection_name=collection_name, points=points)

            return f"✅ Uploaded {len(points)} chunks to collection '{collection_name}' from '{p.name}'"
        except Exception as e:
            return f"❌ Markdown upload failed: {e}"
    
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


# Public API functions with enhanced features
def upload_openapi_spec_to_rag(file_path: str, collection_name: str, metadata: Optional[Dict] = None) -> str:
    """Upload OpenAPI spec with optimized chunking."""
    try:
        rag = get_rag_system()
        return rag.upload_spec(file_path, collection_name)
    except Exception as e:
        return f"❌ Upload error: {str(e)}"


def retrieve_from_rag(query: str, collection_name: str, limit: int = 5, score_threshold: float = 0.5, current_path: Optional[str] = None) -> str:
    """Enhanced RAG query with semantic re-ranking."""
    try:
        rag = get_rag_system()
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


def analyze_fields_with_rag_and_llm(fields: List[str], collection_name: str, context_topic: Optional[str] = None, current_path: Optional[str] = None) -> str:
    """Enhanced field analysis with multi-query strategy."""
    try:
        rag = get_rag_system()
        
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


def delete_rag_collection(collection_name: str) -> str:
    """Delete RAG collection."""
    try:
        rag = get_rag_system()
        return rag.delete_collection(collection_name)
    except Exception as e:
        return f"❌ Delete error: {str(e)}"


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