"""
RAG Chunking Methods
Contains all chunking and content extraction methods for API specifications
"""

import json
import yaml
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime

from qdrant_client.models import PointStruct
from .rag_core import OptimizedRAGSystem, DocumentChunk


class RAGChunkingMixin:
    """Mixin class providing chunking functionality for OptimizedRAGSystem."""
    
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
