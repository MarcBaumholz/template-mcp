"""
RAG Tools for OpenAPI Specification Analysis

This module provides tools for uploading, querying, and analyzing OpenAPI specifications
using a RAG (Retrieval-Augmented Generation) system with Qdrant vector database.
"""

import os
import json
import logging
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    from sentence_transformers import SentenceTransformer
    import yaml
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

from .llm_client import get_llm_response


class RAGSystem:
    """RAG system for OpenAPI specification analysis."""
    
    def __init__(self):
        """Initialize RAG system with Qdrant client and sentence transformer."""
        if not QDRANT_AVAILABLE:
            raise ImportError("Required packages not available. Install with: pip install sentence-transformers qdrant-client pyyaml pandas")
        
        # Check for cloud Qdrant configuration
        qdrant_url = os.getenv('QDRANT_URL')
        qdrant_api_key = os.getenv('QDRANT_API_KEY')
        
        if qdrant_url and qdrant_api_key:
            # Use cloud Qdrant
            self.client = QdrantClient(
                url=qdrant_url,
                api_key=qdrant_api_key,
            )
            self.storage_path = "cloud"
            self.logger = logging.getLogger("rag_system")
            self.logger.info(f"RAG system initialized with cloud Qdrant: {qdrant_url}")
        else:
            # Use local Qdrant storage
            storage_path = os.path.join(os.getcwd(), "qdrant_storage")
            
            # Ensure the directory exists and is writable
            try:
                os.makedirs(storage_path, exist_ok=True)
                # Test write permissions
                test_file = os.path.join(storage_path, ".write_test")
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
            except Exception as e:
                # Fallback to temporary directory if main storage is not writable
                storage_path = tempfile.mkdtemp(prefix="qdrant_")
                logging.warning(f"Using temporary storage at {storage_path} due to: {e}")
            
            self.client = QdrantClient(path=storage_path)
            self.storage_path = storage_path
            self.logger = logging.getLogger("rag_system")
            self.logger.info(f"RAG system initialized with local storage at: {storage_path}")
        
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
    
    def create_collection(self, collection_name: str) -> None:
        """Create a new collection in Qdrant."""
        try:
            # Check if collection already exists
            existing_collections = self.list_collections()
            if collection_name in existing_collections:
                self.logger.info(f"Collection '{collection_name}' already exists")
                return
                
            # Create collection with vector configuration
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
            self.logger.info(f"Created collection: {collection_name}")
        except Exception as e:
            self.logger.error(f"Failed to create collection {collection_name}: {e}")
            raise
    
    def upload_openapi_spec(self, file_path: str, collection_name: str, metadata: Optional[Dict] = None) -> str:
        """Upload and process an OpenAPI specification file."""
        try:
            # Read the file
            file_path = Path(file_path)
            if not file_path.exists():
                return f"Error: File {file_path} does not exist"
            
            # Parse the file - check format and validate
            file_suffix = file_path.suffix.lower()
            if file_suffix not in ['.json', '.yaml', '.yml']:
                raise ValueError(f"Unsupported file format: {file_suffix}. Only JSON, YAML, and YML files are supported.")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_suffix in ['.yaml', '.yml']:
                    spec = yaml.safe_load(f)
                else:
                    spec = json.load(f)
            
            # Create collection
            self.create_collection(collection_name)
            
            # Process and embed the specification
            points = self._process_openapi_spec(spec, metadata or {})
            
            # Upload to Qdrant
            self.client.upsert(
                collection_name=collection_name,
                points=points
            )
            
            return f"Successfully uploaded {len(points)} chunks from {file_path.name} to collection '{collection_name}'"
        
        except Exception as e:
            return f"Error uploading specification: {str(e)}"
    
    def _process_openapi_spec(self, spec: Dict, metadata: Dict) -> List[PointStruct]:
        """Process OpenAPI spec into chunks for embedding."""
        points = []
        point_id = 0
        
        # Process paths
        if 'paths' in spec:
            for path, path_data in spec['paths'].items():
                for method, operation in path_data.items():
                    if isinstance(operation, dict):
                        # Create text representation
                        text_parts = [
                            f"Path: {path}",
                            f"Method: {method.upper()}",
                        ]
                        
                        if 'summary' in operation:
                            text_parts.append(f"Summary: {operation['summary']}")
                        if 'description' in operation:
                            text_parts.append(f"Description: {operation['description']}")
                        if 'parameters' in operation:
                            params = [p.get('name', '') for p in operation['parameters']]
                            text_parts.append(f"Parameters: {', '.join(params)}")
                        
                        text = '\n'.join(text_parts)
                        embedding = self.encoder.encode(text).tolist()
                        
                        points.append(PointStruct(
                            id=point_id,
                            vector=embedding,
                            payload={
                                'text': text,
                                'path': path,
                                'method': method,
                                'type': 'endpoint',
                                **metadata
                            }
                        ))
                        point_id += 1
        
        # Process schemas/components
        if 'components' in spec and 'schemas' in spec['components']:
            for schema_name, schema_data in spec['components']['schemas'].items():
                text_parts = [f"Schema: {schema_name}"]
                
                if 'description' in schema_data:
                    text_parts.append(f"Description: {schema_data['description']}")
                if 'properties' in schema_data:
                    props = list(schema_data['properties'].keys())
                    text_parts.append(f"Properties: {', '.join(props)}")
                
                text = '\n'.join(text_parts)
                embedding = self.encoder.encode(text).tolist()
                
                points.append(PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        'text': text,
                        'schema_name': schema_name,
                        'type': 'schema',
                        **metadata
                    }
                ))
                point_id += 1
        
        return points
    
    def query(self, query: str, collection_name: str, limit: int = 5, score_threshold: float = 0.5) -> List[Dict]:
        """Query the RAG system."""
        try:
            query_embedding = self.encoder.encode(query).tolist()
            
            results = self.client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=score_threshold
            )
            
            return [
                {
                    'text': result.payload['text'],
                    'score': result.score,
                    'metadata': {k: v for k, v in result.payload.items() if k != 'text'}
                }
                for result in results
            ]
        
        except Exception as e:
            return [{'error': f"Query failed: {str(e)}"}]
    
    def list_collections(self) -> List[str]:
        """List all available collections."""
        try:
            collections_response = self.client.get_collections()
            collection_names = []
            
            if hasattr(collections_response, 'collections'):
                # Handle CollectionsResponse object
                for collection in collections_response.collections:
                    if hasattr(collection, 'name'):
                        collection_names.append(collection.name)
                    else:
                        # Fallback: try to get name from dict-like object
                        collection_names.append(str(collection))
            elif isinstance(collections_response, list):
                # Handle direct list response
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
            return []  # Return empty list instead of error message in list
    
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
def upload_openapi_spec_to_rag(file_path: str, collection_name: str, metadata: Optional[Dict] = None) -> str:
    """Upload an OpenAPI specification to the RAG system."""
    try:
        rag = get_rag_system()
        return rag.upload_openapi_spec(file_path, collection_name, metadata)
    except Exception as e:
        return f"Error: {str(e)}"


def retrieve_from_rag(query: str, collection_name: str, limit: int = 5, score_threshold: float = 0.5) -> List[Dict]:
    """Retrieve relevant information from the RAG system."""
    try:
        rag = get_rag_system()
        return rag.query(query, collection_name, limit, score_threshold)
    except Exception as e:
        return [{'error': f"Retrieval failed: {str(e)}"}]


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
    """Analyze fields using RAG retrieval and LLM synthesis."""
    try:
        # Create search queries for the fields
        field_context = {}
        rag = get_rag_system()
        
        for field in fields:
            # Search for field-related information
            queries = [
                f"field {field}",
                f"parameter {field}",
                f"property {field}",
                f"{field} definition"
            ]
            
            all_results = []
            for query in queries:
                results = rag.query(query, collection_name, limit=3, score_threshold=0.3)
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
Please provide a comprehensive analysis of these fields including:
1. Purpose and meaning of each field
2. Data types and expected values
3. Relationships between fields
4. Business context and usage
5. Any validation rules or constraints

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