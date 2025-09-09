"""
API Specification Verifier MCP Tool
Semantic verification of API specifications using grep-like patterns and RAG analysis
"""

import json
import os
import re
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime

import yaml

# Lazy imports for heavy dependencies
try:
    from qdrant_client import QdrantClient
    from sentence_transformers import SentenceTransformer
    import tiktoken
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    """Result of API specification verification."""
    field_name: str
    found: bool
    confidence: float
    matches: List[Dict[str, Any]]
    suggestions: List[str]
    verification_type: str
    api_path: Optional[str] = None
    schema_path: Optional[str] = None
    data_type: Optional[str] = None
    description: Optional[str] = None


@dataclass
class APIVerificationReport:
    """Complete verification report."""
    timestamp: str
    api_spec_path: str
    total_fields: int
    verified_fields: int
    unverified_fields: int
    confidence_score: float
    results: List[VerificationResult]
    recommendations: List[str]
    verification_summary: Dict[str, Any]


class APISpecVerifier:
    """Semantic API specification verifier with grep-like patterns."""
    
    def __init__(self):
        self.rag_system = None
        self.encoder = None
        self.tokenizer = None
        self._initialize_rag()
    
    def _initialize_rag(self):
        """Initialize RAG system if available."""
        if not RAG_AVAILABLE:
            logger.warning("RAG dependencies not available. Semantic matching disabled.")
            return
        
        try:
            # Check for cloud configuration
            qdrant_url = os.getenv('QDRANT_URL')
            qdrant_api_key = os.getenv('QDRANT_API_KEY')
            
            if qdrant_url and qdrant_api_key:
                self.client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
                logger.info("Connected to Qdrant Cloud for semantic verification")
            else:
                storage_path = os.path.join(os.getcwd(), "qdrant_storage")
                os.makedirs(storage_path, exist_ok=True)
                self.client = QdrantClient(path=storage_path)
                logger.info("Using local Qdrant storage for semantic verification")
            
            self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
            self.rag_system = True
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG system: {e}")
            self.rag_system = None
    
    def load_api_spec(self, api_spec_path: str) -> Dict[str, Any]:
        """Load OpenAPI specification from file."""
        try:
            spec_path = Path(api_spec_path)
            if not spec_path.exists():
                raise FileNotFoundError(f"API spec not found: {api_spec_path}")
            
            with open(spec_path, 'r', encoding='utf-8') as f:
                if spec_path.suffix.lower() in ['.yaml', '.yml']:
                    return yaml.safe_load(f)
                else:
                    return json.load(f)
                    
        except Exception as e:
            logger.error(f"Failed to load API spec: {e}")
            raise
    
    def grep_field_in_spec(self, field_name: str, api_spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fast grep-like search for fields in API spec using pattern matching."""
        matches = []
        
        # Normalize field name for better matching
        normalized_field = self._normalize_field_name(field_name)
        
        # Search patterns
        patterns = [
            rf'"{re.escape(field_name)}"',
            rf'"{re.escape(normalized_field)}"',
            rf'\b{re.escape(field_name)}\b',
            rf'\b{re.escape(normalized_field)}\b'
        ]
        
        # Search in paths
        for path, methods in api_spec.get('paths', {}).items():
            for method, operation in methods.items():
                if isinstance(operation, dict):
                    # Check parameters
                    for param in operation.get('parameters', []):
                        if self._matches_patterns(param.get('name', ''), patterns):
                            matches.append({
                                'type': 'parameter',
                                'path': path,
                                'method': method.upper(),
                                'name': param.get('name'),
                                'in': param.get('in'),
                                'required': param.get('required', False),
                                'schema': param.get('schema', {}),
                                'description': param.get('description', ''),
                                'confidence': 0.9
                            })
                    
                    # Check request body
                    request_body = operation.get('requestBody', {})
                    if request_body:
                        content = request_body.get('content', {})
                        for media_type, media_obj in content.items():
                            schema = media_obj.get('schema', {})
                            self._search_schema_recursive(schema, patterns, matches, path, method)
        
        # Search in components/schemas
        schemas = api_spec.get('components', {}).get('schemas', {})
        for schema_name, schema_def in schemas.items():
            self._search_schema_recursive(schema_def, patterns, matches, schema_name=schema_name)
        
        return matches
    
    def _search_schema_recursive(self, schema: Dict[str, Any], patterns: List[str], 
                               matches: List[Dict[str, Any]], path: str = '', 
                               method: str = '', schema_name: str = ''):
        """Recursively search schema for field matches."""
        if not isinstance(schema, dict):
            return
        
        # Check properties
        properties = schema.get('properties', {})
        for prop_name, prop_def in properties.items():
            if self._matches_patterns(prop_name, patterns):
                matches.append({
                    'type': 'property',
                    'path': path,
                    'method': method,
                    'schema_name': schema_name,
                    'name': prop_name,
                    'data_type': prop_def.get('type'),
                    'format': prop_def.get('format'),
                    'description': prop_def.get('description', ''),
                    'required': prop_name in schema.get('required', []),
                    'confidence': 0.9
                })
        
        # Check allOf, anyOf, oneOf
        for key in ['allOf', 'anyOf', 'oneOf']:
            if key in schema:
                for sub_schema in schema[key]:
                    self._search_schema_recursive(sub_schema, patterns, matches, path, method, schema_name)
        
        # Check items for arrays
        if 'items' in schema:
            self._search_schema_recursive(schema['items'], patterns, matches, path, method, schema_name)
    
    def _matches_patterns(self, text: str, patterns: List[str]) -> bool:
        """Check if text matches any of the patterns."""
        if not text:
            return False
        
        text_lower = text.lower()
        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        return False
    
    def _normalize_field_name(self, field_name: str) -> str:
        """Normalize field name for better matching."""
        # Convert common variations
        variations = {
            'id': ['identifier', 'uuid', 'key'],
            'name': ['title', 'label'],
            'date': ['timestamp', 'time'],
            'email': ['mail', 'e-mail'],
            'phone': ['telephone', 'mobile', 'cell'],
            'address': ['location', 'addr'],
            'status': ['state', 'condition'],
            'type': ['category', 'kind'],
            'description': ['desc', 'details', 'summary'],
            'created': ['created_at', 'created_date', 'created_time'],
            'updated': ['updated_at', 'updated_date', 'modified', 'modified_at'],
            'start': ['begin', 'start_date', 'start_time'],
            'end': ['finish', 'end_date', 'end_time', 'stop'],
            'duration': ['length', 'period', 'time_span'],
            'amount': ['quantity', 'value', 'number'],
            'currency': ['money', 'currency_code'],
            'employee': ['worker', 'staff', 'person', 'user'],
            'manager': ['supervisor', 'boss', 'lead'],
            'department': ['team', 'unit', 'division'],
            'position': ['job', 'role', 'title'],
            'salary': ['wage', 'pay', 'compensation'],
            'absence': ['time_off', 'leave', 'vacation', 'sick_leave'],
            'approval': ['approve', 'approved', 'approver'],
            'request': ['req', 'application'],
            'reason': ['cause', 'explanation', 'justification']
        }
        
        field_lower = field_name.lower()
        for key, values in variations.items():
            if field_lower in values or field_lower == key:
                return key
            if any(val in field_lower for val in values):
                return key
        
        return field_name
    
    def semantic_field_match(self, field_description: str, api_spec: Dict[str, Any], 
                           collection_name: str = "flip_api_v2") -> List[Dict[str, Any]]:
        """Use RAG to find semantically similar fields."""
        if not self.rag_system:
            return []
        
        try:
            # Query RAG system for semantic matches
            from tools.phase1_data_extraction.upload_api_specification import retrieve_from_rag
            
            query = f"Find fields related to: {field_description}"
            results = retrieve_from_rag(
                query=query,
                collection_name=collection_name,
                limit=5,
                score_threshold=0.6
            )
            
            semantic_matches = []
            for result in results:
                semantic_matches.append({
                    'type': 'semantic_match',
                    'field_name': result.get('field_name', ''),
                    'description': result.get('description', ''),
                    'confidence': result.get('score', 0.0),
                    'source': 'rag_semantic_search'
                })
            
            return semantic_matches
            
        except Exception as e:
            logger.error(f"Semantic matching failed: {e}")
            return []
    
    def verify_field_mapping(self, field_name: str, api_spec: Dict[str, Any], 
                           verification_type: str = "comprehensive") -> VerificationResult:
        """Verify a single field mapping against API spec."""
        
        # Pattern-based verification
        pattern_matches = self.grep_field_in_spec(field_name, api_spec)
        
        # Semantic verification (if enabled and RAG available)
        semantic_matches = []
        if verification_type in ["semantic", "comprehensive"] and self.rag_system:
            semantic_matches = self.semantic_field_match(field_name, api_spec)
        
        # Combine and rank matches
        all_matches = pattern_matches + semantic_matches
        all_matches.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        # Determine result
        found = len(all_matches) > 0
        confidence = max([m.get('confidence', 0) for m in all_matches]) if all_matches else 0.0
        
        # Generate suggestions
        suggestions = []
        if not found:
            suggestions.append(f"Field '{field_name}' not found in API spec")
            suggestions.append("Consider checking for similar field names or synonyms")
            if self.rag_system:
                suggestions.append("Try semantic search for related fields")
        else:
            for match in all_matches[:3]:  # Top 3 suggestions
                if match['type'] == 'property':
                    suggestions.append(f"Found property: {match['name']} in schema {match.get('schema_name', 'unknown')}")
                elif match['type'] == 'parameter':
                    suggestions.append(f"Found parameter: {match['name']} in {match['method']} {match['path']}")
                elif match['type'] == 'semantic_match':
                    suggestions.append(f"Semantic match: {match['field_name']} (confidence: {match['confidence']:.2f})")
        
        # Extract best match details
        best_match = all_matches[0] if all_matches else {}
        
        return VerificationResult(
            field_name=field_name,
            found=found,
            confidence=confidence,
            matches=all_matches,
            suggestions=suggestions,
            verification_type=verification_type,
            api_path=best_match.get('path'),
            schema_path=best_match.get('schema_name'),
            data_type=best_match.get('data_type'),
            description=best_match.get('description')
        )
    
    def verify_mappings_batch(self, field_mappings: Dict[str, str], api_spec: Dict[str, Any],
                            verification_type: str = "comprehensive") -> APIVerificationReport:
        """Verify multiple field mappings against API spec."""
        
        results = []
        total_fields = len(field_mappings)
        verified_fields = 0
        total_confidence = 0.0
        
        for source_field, target_field in field_mappings.items():
            # Use target field if provided, otherwise use source field
            field_to_verify = target_field if target_field != "?" else source_field
            
            result = self.verify_field_mapping(field_to_verify, api_spec, verification_type)
            results.append(result)
            
            if result.found:
                verified_fields += 1
            total_confidence += result.confidence
        
        # Calculate overall confidence
        overall_confidence = total_confidence / total_fields if total_fields > 0 else 0.0
        
        # Generate recommendations
        recommendations = self._generate_recommendations(results, api_spec)
        
        # Create verification summary
        verification_summary = {
            'verification_type': verification_type,
            'pattern_matches': len([r for r in results if any(m['type'] == 'property' or m['type'] == 'parameter' for m in r.matches)]),
            'semantic_matches': len([r for r in results if any(m['type'] == 'semantic_match' for m in r.matches)]),
            'high_confidence_matches': len([r for r in results if r.confidence >= 0.8]),
            'medium_confidence_matches': len([r for r in results if 0.5 <= r.confidence < 0.8]),
            'low_confidence_matches': len([r for r in results if r.confidence < 0.5])
        }
        
        return APIVerificationReport(
            timestamp=datetime.now().isoformat(),
            api_spec_path="",  # Will be set by caller
            total_fields=total_fields,
            verified_fields=verified_fields,
            unverified_fields=total_fields - verified_fields,
            confidence_score=overall_confidence,
            results=results,
            recommendations=recommendations,
            verification_summary=verification_summary
        )
    
    def _generate_recommendations(self, results: List[VerificationResult], 
                                api_spec: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on verification results."""
        recommendations = []
        
        # Count verification types
        unverified = [r for r in results if not r.found]
        low_confidence = [r for r in results if r.confidence < 0.5]
        
        if unverified:
            recommendations.append(f"⚠️  {len(unverified)} fields not found in API spec")
            recommendations.append("Consider using semantic search for similar field names")
        
        if low_confidence:
            recommendations.append(f"⚠️  {len(low_confidence)} fields have low confidence matches")
            recommendations.append("Review these mappings manually for accuracy")
        
        # Check for common patterns
        verified_fields = [r for r in results if r.found]
        if verified_fields:
            recommendations.append(f"✅ {len(verified_fields)} fields successfully verified")
        
        # Suggest endpoints based on field patterns
        endpoint_suggestions = self._suggest_endpoints(results, api_spec)
        if endpoint_suggestions:
            recommendations.extend(endpoint_suggestions)
        
        return recommendations
    
    def _suggest_endpoints(self, results: List[VerificationResult], 
                          api_spec: Dict[str, Any]) -> List[str]:
        """Suggest relevant endpoints based on field patterns."""
        suggestions = []
        
        # Analyze field patterns to suggest endpoints
        field_names = [r.field_name.lower() for r in results if r.found]
        
        # Common endpoint patterns
        endpoint_patterns = {
            'employee': ['/employees', '/users', '/staff', '/workers'],
            'absence': ['/absences', '/time-off', '/leave', '/vacations'],
            'time': ['/time', '/attendance', '/hours'],
            'approval': ['/approvals', '/requests', '/workflows'],
            'department': ['/departments', '/teams', '/units'],
            'position': ['/positions', '/jobs', '/roles']
        }
        
        for pattern, endpoints in endpoint_patterns.items():
            if any(pattern in field for field in field_names):
                # Check if these endpoints exist in the spec
                for endpoint in endpoints:
                    if endpoint in api_spec.get('paths', {}):
                        suggestions.append(f"🎯 Suggested endpoint: {endpoint}")
        
        return suggestions
    
    def generate_markdown_report(self, report: APIVerificationReport, 
                               api_spec_path: str) -> str:
        """Generate markdown verification report."""
        
        report.api_spec_path = api_spec_path
        
        markdown = f"""# API Specification Verification Report

## 📊 Summary
- **API Specification**: `{api_spec_path}`
- **Verification Type**: {report.verification_summary['verification_type']}
- **Timestamp**: {report.timestamp}
- **Total Fields**: {report.total_fields}
- **Verified Fields**: {report.verified_fields} ({(report.verified_fields/report.total_fields*100):.1f}%)
- **Unverified Fields**: {report.unverified_fields}
- **Overall Confidence**: {report.confidence_score:.2f}

## 📈 Verification Statistics
- **Pattern Matches**: {report.verification_summary['pattern_matches']}
- **Semantic Matches**: {report.verification_summary['semantic_matches']}
- **High Confidence** (≥0.8): {report.verification_summary['high_confidence_matches']}
- **Medium Confidence** (0.5-0.8): {report.verification_summary['medium_confidence_matches']}
- **Low Confidence** (<0.5): {report.verification_summary['low_confidence_matches']}

## 🔍 Detailed Results

"""
        
        # Group results by verification status
        verified = [r for r in report.results if r.found]
        unverified = [r for r in report.results if not r.found]
        
        if verified:
            markdown += "### ✅ Verified Fields\n\n"
            markdown += "| Field | Confidence | Type | Path | Description |\n"
            markdown += "|-------|------------|------|------|-------------|\n"
            
            for result in verified:
                markdown += f"| {result.field_name} | {result.confidence:.2f} | {result.data_type or 'N/A'} | {result.api_path or result.schema_path or 'N/A'} | {result.description or 'N/A'} |\n"
            
            markdown += "\n"
        
        if unverified:
            markdown += "### ❌ Unverified Fields\n\n"
            markdown += "| Field | Suggestions |\n"
            markdown += "|-------|-------------|\n"
            
            for result in unverified:
                suggestions = "; ".join(result.suggestions[:2])  # Limit to 2 suggestions
                markdown += f"| {result.field_name} | {suggestions} |\n"
            
            markdown += "\n"
        
        # Recommendations
        if report.recommendations:
            markdown += "## 💡 Recommendations\n\n"
            for rec in report.recommendations:
                markdown += f"- {rec}\n"
            markdown += "\n"
        
        # Top matches for each field
        markdown += "## 🎯 Top Matches by Field\n\n"
        for result in report.results:
            markdown += f"### {result.field_name}\n"
            markdown += f"- **Status**: {'✅ Found' if result.found else '❌ Not Found'}\n"
            markdown += f"- **Confidence**: {result.confidence:.2f}\n"
            
            if result.matches:
                markdown += "- **Top Matches**:\n"
                for i, match in enumerate(result.matches[:3], 1):
                    if match['type'] == 'property':
                        markdown += f"  {i}. Property: `{match['name']}` in schema `{match.get('schema_name', 'unknown')}` (confidence: {match['confidence']:.2f})\n"
                    elif match['type'] == 'parameter':
                        markdown += f"  {i}. Parameter: `{match['name']}` in {match['method']} {match['path']} (confidence: {match['confidence']:.2f})\n"
                    elif match['type'] == 'semantic_match':
                        markdown += f"  {i}. Semantic: `{match['field_name']}` (confidence: {match['confidence']:.2f})\n"
            
            if result.suggestions:
                markdown += "- **Suggestions**:\n"
                for suggestion in result.suggestions:
                    markdown += f"  - {suggestion}\n"
            
            markdown += "\n"
        
        return markdown


# Global instance for lazy loading
_verifier_instance = None


def get_verifier_instance() -> APISpecVerifier:
    """Get or create verifier instance with lazy loading."""
    global _verifier_instance
    if _verifier_instance is None:
        _verifier_instance = APISpecVerifier()
    return _verifier_instance


def verify_api_specification(
    api_spec_path: str,
    field_mappings: str,
    verification_type: str = "comprehensive",
    output_format: str = "markdown"
) -> str:
    """
    Verify field mappings against API specification using semantic analysis and grep-like patterns.
    
    Args:
        api_spec_path: Path to OpenAPI specification file
        field_mappings: JSON string containing field mappings to verify
        verification_type: "fast" (pattern only), "semantic" (RAG enhanced), "comprehensive" (both)
        output_format: Output format for results ("markdown", "json", "table")
        
    Returns:
        Verification report in specified format
    """
    try:
        # Parse field mappings
        if isinstance(field_mappings, str):
            mappings = json.loads(field_mappings)
        else:
            mappings = field_mappings
        
        # Get verifier instance
        verifier = get_verifier_instance()
        
        # Load API spec
        api_spec = verifier.load_api_spec(api_spec_path)
        
        # Perform verification
        report = verifier.verify_mappings_batch(mappings, api_spec, verification_type)
        
        # Generate output
        if output_format == "markdown":
            return verifier.generate_markdown_report(report, api_spec_path)
        elif output_format == "json":
            return json.dumps({
                'timestamp': report.timestamp,
                'api_spec_path': api_spec_path,
                'total_fields': report.total_fields,
                'verified_fields': report.verified_fields,
                'unverified_fields': report.unverified_fields,
                'confidence_score': report.confidence_score,
                'verification_summary': report.verification_summary,
                'recommendations': report.recommendations,
                'results': [
                    {
                        'field_name': r.field_name,
                        'found': r.found,
                        'confidence': r.confidence,
                        'api_path': r.api_path,
                        'schema_path': r.schema_path,
                        'data_type': r.data_type,
                        'suggestions': r.suggestions
                    }
                    for r in report.results
                ]
            }, indent=2)
        else:
            return f"Unsupported output format: {output_format}"
            
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        return f"❌ Verification failed: {str(e)}"
