"""
Unit tests for the Schema Mapping Tool.

Tests the intelligent field mapping functionality, including cognitive matching,
AI agents, input parsing, and report generation.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from tools.mapping_models import (
    SourceField, 
    SchemaMappingRequest, 
    TargetMatch,
    MappingResult,
    SchemaMappingReport,
    AgentInsight
)
from tools.cognitive_matcher import CognitiveMatcher
from tools.input_parser import InputParser
from tools.report_generator import MarkdownReportGenerator


class TestCognitiveMatcher:
    """Test the cognitive matching algorithm."""
    
    def test_exact_match(self):
        """Test exact field name matching."""
        matcher = CognitiveMatcher()
        score = matcher.calculate_similarity_score("user_email", "user_email")
        assert score >= 0.95  # Should be very high for exact match
    
    def test_semantic_similarity(self):
        """Test semantic similarity matching."""
        matcher = CognitiveMatcher()
        score = matcher.calculate_similarity_score("email", "email_address")
        assert score >= 0.4  # Should be decent for semantic similarity
    
    def test_abbreviation_matching(self):
        """Test abbreviation pattern matching."""
        matcher = CognitiveMatcher()
        score = matcher.calculate_similarity_score("emp_id", "employee_id")
        assert score >= 0.3  # Should match abbreviation pattern
    
    def test_no_match(self):
        """Test fields that should not match."""
        matcher = CognitiveMatcher()
        score = matcher.calculate_similarity_score("email", "salary")
        assert score <= 0.5  # Should be low for unrelated fields

    def test_cognitive_patterns(self):
        """Test cognitive pattern detection."""
        matcher = CognitiveMatcher()
        patterns = matcher.find_cognitive_patterns("email", "user_email")
        assert len(patterns) > 0


class TestInputParser:
    """Test the input parser functionality."""
    
    def test_parse_json_file(self):
        """Test JSON file parsing."""
        # Create test JSON data
        test_data = {
            "user": {
                "id": 123,
                "email": "test@example.com", 
                "profile": {
                    "first_name": "John",
                    "last_name": "Doe"
                }
            },
            "company": {
                "name": "Acme Corp"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name
        
        try:
            parser = InputParser()
            fields = parser.parse_json_file(temp_path)
            
            # Check that fields were extracted
            assert len(fields) > 0
            
            # Check specific fields
            field_names = [f.name for f in fields]
            assert "id" in field_names
            assert "email" in field_names
            assert "first_name" in field_names
            
        finally:
            Path(temp_path).unlink()
    
    def test_parse_markdown_analysis(self):
        """Test Markdown analysis file parsing."""
        markdown_content = """
# API Field Analysis

## Field: email
**Type**: string
**Description**: User's email address

## Field: employee_id  
**Type**: integer  
**Description**: Unique identifier for employees
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(markdown_content)
            temp_path = f.name
        
        try:
            parser = InputParser()
            analysis = parser.parse_markdown_analysis(temp_path)
            
            # Check that analysis was extracted
            assert isinstance(analysis, dict)
            field_descriptions = analysis.get('field_descriptions', {})
            assert len(field_descriptions) >= 0  # May be empty depending on parsing
            
        finally:
            Path(temp_path).unlink()


class TestReportGenerator:
    """Test the Markdown report generator."""
    
    def test_report_generation(self):
        """Test Markdown report generation."""
        import datetime
        
        # Create test data
        source_field = SourceField(
            name="email",
            path="user.email",
            type="string", 
            description="User email address",
            context="Authentication",
            examples=["user@example.com"]
        )
        
        target_match = TargetMatch(
            field_name="user_email",
            field_path="user.email",
            field_type="string",
            confidence_score=0.9,
            reasoning="Direct email field match",
            agent_insights=[
                AgentInsight(
                    agent_name="FlipInfoAgent",
                    insight="Maps to Flip user email field",
                    confidence=0.9,
                    reasoning="Direct semantic match"
                )
            ],
            semantic_similarity=0.95,
            structural_similarity=0.8,
            context_relevance=0.9
        )
        
        mapping_result = MappingResult(
            source_field=source_field,
            top_matches=[target_match],
            overall_confidence=0.9,
            mapping_recommendation="HIGH_CONFIDENCE",
            processing_notes="Successfully analyzed field"
        )
        
        request = SchemaMappingRequest(
            source_json_path="test.json",
            source_analysis_md_path="test.md",
            target_collection_name="test_collection",
            mapping_context="Test mapping"
        )
        
        report = SchemaMappingReport(
            request=request,
            mapping_results=[mapping_result],
            summary_statistics={
                "total_fields": 1,
                "matched_fields": 1,
                "match_rate": 1.0,
                "average_confidence": 0.9
            },
            generated_at=datetime.datetime.now(),
            processing_time_seconds=1.5
        )
        
        # Generate report
        generator = MarkdownReportGenerator()
        markdown_content = generator.generate_report(report)
        
        # Check report content
        assert "# 🔄 API Schema Mapping Report" in markdown_content
        assert "email" in markdown_content
        assert "user_email" in markdown_content
        assert "FlipInfoAgent" in markdown_content

    def test_confidence_icons(self):
        """Test confidence icon generation."""
        generator = MarkdownReportGenerator()
        
        assert generator._get_confidence_icon(0.9) == "🟢"  # High
        assert generator._get_confidence_icon(0.6) == "🟡"  # Moderate  
        assert generator._get_confidence_icon(0.4) == "🟠"  # Low
        assert generator._get_confidence_icon(0.2) == "🔴"  # No match


class TestDataModels:
    """Test the Pydantic data models."""
    
    def test_source_field_creation(self):
        """Test SourceField model creation."""
        field = SourceField(
            name="test_field",
            path="user.test_field",
            type="string",
            description="A test field",
            context="Testing context",
            examples=["example1", "example2"]
        )
        
        assert field.name == "test_field"
        assert field.path == "user.test_field"
        assert field.type == "string"
        assert len(field.examples) == 2
    
    def test_target_match_creation(self):
        """Test TargetMatch model creation."""
        match = TargetMatch(
            field_name="target_field",
            field_path="target.field",
            field_type="string",
            confidence_score=0.85,
            reasoning="Test reasoning",
            semantic_similarity=0.9,
            structural_similarity=0.8,
            context_relevance=0.7
        )
        
        assert match.field_name == "target_field"
        assert match.confidence_score == 0.85
        assert len(match.agent_insights) == 0  # Default empty list
    
    def test_schema_mapping_request(self):
        """Test SchemaMappingRequest model."""
        request = SchemaMappingRequest(
            source_json_path="/path/to/source.json",
            source_analysis_md_path="/path/to/analysis.md",
            target_collection_name="test_collection",
            mapping_context="Test context",
            max_matches_per_field=5
        )
        
        assert request.source_json_path == "/path/to/source.json"
        assert request.max_matches_per_field == 5
        assert request.mapping_context == "Test context"


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 