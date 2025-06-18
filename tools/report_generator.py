"""
Report generator for schema mapping results.
Creates professional Markdown reports with detailed findings.
"""

from typing import List, Dict, Any
from datetime import datetime
from .mapping_models import SchemaMappingReport, MappingResult, TargetMatch, AgentInsight


class MarkdownReportGenerator:
    """Generate comprehensive Markdown reports for schema mapping results."""
    
    def __init__(self):
        """Initialize the report generator."""
        pass
    
    def generate_report(self, report: SchemaMappingReport, output_path: str = None) -> str:
        """
        Generate a comprehensive Markdown report.
        
        Args:
            report: Schema mapping report data
            output_path: Optional file path to save the report
            
        Returns:
            str: Generated Markdown content
        """
        markdown_content = self._build_markdown_report(report)
        
        if output_path:
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
            except Exception as e:
                print(f"Failed to save report to {output_path}: {e}")
        
        return markdown_content
    
    def _build_markdown_report(self, report: SchemaMappingReport) -> str:
        """Build the complete Markdown report."""
        sections = [
            self._build_header(report),
            self._build_summary(report),
            self._build_statistics(report),
            self._build_detailed_results(report),
            self._build_recommendations(report),
            self._build_footer(report)
        ]
        
        return "\n\n".join(sections)
    
    def _build_header(self, report: SchemaMappingReport) -> str:
        """Build the report header section."""
        return f"""# 🔄 API Schema Mapping Report

**Generated:** {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}  
**Processing Time:** {report.processing_time_seconds:.2f} seconds  
**Source:** `{report.request.source_json_path}`  
**Target Collection:** `{report.request.target_collection_name}`

---"""
    
    def _build_summary(self, report: SchemaMappingReport) -> str:
        """Build the executive summary section."""
        stats = report.summary_statistics
        
        if "error" in stats:
            return f"""## ❌ Processing Error

**Error:** {stats['error']}

The schema mapping process encountered an error and could not complete successfully."""
        
        total_fields = stats.get('total_fields', 0)
        matched_fields = stats.get('matched_fields', 0)
        match_rate = stats.get('match_rate', 0.0)
        avg_confidence = stats.get('average_confidence', 0.0)
        
        return f"""## 📊 Executive Summary

This report analyzes **{total_fields}** source fields against the target API schema and provides intelligent mapping recommendations using multi-agent AI analysis.

### Key Findings
- **Fields Analyzed:** {total_fields}
- **Successful Matches:** {matched_fields} ({match_rate:.1%})
- **Average Confidence:** {avg_confidence:.1%}
- **Processing Context:** {report.request.mapping_context or 'General schema mapping'}"""
    
    def _build_statistics(self, report: SchemaMappingReport) -> str:
        """Build the detailed statistics section."""
        stats = report.summary_statistics
        
        if "error" in stats:
            return ""
        
        high_conf = stats.get('high_confidence_matches', 0)
        mod_conf = stats.get('moderate_confidence_matches', 0)
        low_conf = stats.get('low_confidence_matches', 0)
        
        return f"""## 📈 Confidence Distribution

| Confidence Level | Count | Percentage |
|------------------|-------|------------|
| 🟢 High (>70%)   | {high_conf} | {(high_conf/stats['total_fields']*100):.1f}% |
| 🟡 Moderate (50-70%) | {mod_conf} | {(mod_conf/stats['total_fields']*100):.1f}% |
| 🟠 Low (30-50%)   | {low_conf} | {(low_conf/stats['total_fields']*100):.1f}% |
| 🔴 No Match (<30%) | {stats['total_fields'] - high_conf - mod_conf - low_conf} | {((stats['total_fields'] - high_conf - mod_conf - low_conf)/stats['total_fields']*100):.1f}% |"""
    
    def _build_detailed_results(self, report: SchemaMappingReport) -> str:
        """Build the detailed field mapping results."""
        if not report.mapping_results:
            return "## 📋 Detailed Results\n\nNo mapping results available."
        
        sections = ["## 📋 Detailed Field Mappings"]
        
        for i, result in enumerate(report.mapping_results, 1):
            sections.append(self._build_field_result(result, i))
        
        return "\n\n".join(sections)
    
    def _build_field_result(self, result: MappingResult, index: int) -> str:
        """Build the result section for a single field."""
        confidence_icon = self._get_confidence_icon(result.overall_confidence)
        
        # Header
        field_section = f"""### {index}. {confidence_icon} `{result.source_field.name}`

**Type:** `{result.source_field.type}`  
**Path:** `{result.source_field.path}`  
**Overall Confidence:** {result.overall_confidence:.1%}  
**Recommendation:** {result.mapping_recommendation}"""
        
        # Field description if available
        if result.source_field.description:
            field_section += f"\n**Description:** {result.source_field.description}"
        
        # Top matches
        if result.top_matches:
            field_section += "\n\n#### 🎯 Top Matches\n"
            for i, match in enumerate(result.top_matches[:3], 1):
                field_section += f"\n{self._build_match_summary(match, i)}"
        else:
            field_section += "\n\n#### ❌ No Matches Found\nNo suitable matches were discovered in the target API."
        
        # AI Agent Insights
        if result.top_matches and result.top_matches[0].agent_insights:
            field_section += "\n\n#### 🤖 AI Agent Analysis\n"
            field_section += self._build_agent_insights(result.top_matches[0].agent_insights)
        
        # Processing notes
        if result.processing_notes:
            field_section += f"\n\n**Notes:** {result.processing_notes}"
        
        return field_section
    
    def _build_match_summary(self, match: TargetMatch, rank: int) -> str:
        """Build summary for a single match."""
        confidence_badge = self._get_confidence_badge(match.confidence_score)
        
        return f"""**{rank}. `{match.field_name}` {confidence_badge}**
- **Path:** `{match.field_path}`
- **Type:** `{match.field_type}`
- **Confidence:** {match.confidence_score:.1%}
- **Reasoning:** {match.reasoning}"""
    
    def _build_agent_insights(self, insights: List[AgentInsight]) -> str:
        """Build the AI agent insights section."""
        if not insights:
            return "No agent insights available."
        
        insights_text = []
        
        for insight in insights:
            confidence_badge = self._get_confidence_badge(insight.confidence)
            insights_text.append(f"""
**{insight.agent_name}** {confidence_badge}
- **Insight:** {insight.insight}
- **Reasoning:** {insight.reasoning[:200]}{'...' if len(insight.reasoning) > 200 else ''}""")
        
        return "\n".join(insights_text)
    
    def _build_recommendations(self, report: SchemaMappingReport) -> str:
        """Build the recommendations section."""
        if not report.mapping_results:
            return ""
        
        # Analyze results for recommendations
        high_confidence = [r for r in report.mapping_results if r.overall_confidence > 0.7]
        no_matches = [r for r in report.mapping_results if not r.top_matches]
        
        recommendations = ["## 💡 Recommendations"]
        
        if high_confidence:
            recommendations.append(f"""### ✅ Ready for Implementation
The following **{len(high_confidence)}** fields have high-confidence matches and are ready for API integration:

{self._build_high_confidence_list(high_confidence)}""")
        
        if no_matches:
            recommendations.append(f"""### ⚠️ Requires Manual Review
The following **{len(no_matches)}** fields could not be automatically matched and require manual investigation:

{self._build_no_match_list(no_matches)}""")
        
        # General recommendations
        recommendations.append("""### 🎯 General Recommendations

1. **High Confidence Matches:** Implement these mappings first as they have strong semantic and contextual alignment.
2. **Moderate Confidence:** Review the AI agent insights and validate matches before implementation.
3. **Low Confidence:** Consider alternative field names or check if target API supports these concepts.
4. **No Matches:** Investigate if these fields exist under different names or if new fields need to be created.""")
        
        return "\n\n".join(recommendations)
    
    def _build_high_confidence_list(self, results: List[MappingResult]) -> str:
        """Build list of high confidence matches."""
        items = []
        for result in results:
            if result.top_matches:
                top_match = result.top_matches[0]
                items.append(f"- `{result.source_field.name}` → `{top_match.field_name}` ({result.overall_confidence:.1%})")
        return "\n".join(items)
    
    def _build_no_match_list(self, results: List[MappingResult]) -> str:
        """Build list of fields with no matches."""
        items = []
        for result in results:
            items.append(f"- `{result.source_field.name}` ({result.source_field.type})")
        return "\n".join(items)
    
    def _build_footer(self, report: SchemaMappingReport) -> str:
        """Build the report footer."""
        return f"""---

## 📝 Report Details

**Request Parameters:**
- **Source JSON:** `{report.request.source_json_path}`
- **Analysis MD:** `{report.request.source_analysis_md_path or 'Not provided'}`
- **Target Collection:** `{report.request.target_collection_name}`
- **Max Matches per Field:** {report.request.max_matches_per_field}

**Processing Information:**
- **Generated At:** {report.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
- **Processing Time:** {report.processing_time_seconds:.2f} seconds
- **Tool Version:** Schema Mapping Tool v1.0

*This report was generated by the AI-powered Schema Mapping Tool using multi-agent analysis and cognitive pattern recognition.*"""
    
    def _get_confidence_icon(self, confidence: float) -> str:
        """Get emoji icon based on confidence level."""
        if confidence > 0.7:
            return "🟢"
        elif confidence > 0.5:
            return "🟡"
        elif confidence > 0.3:
            return "🟠"
        else:
            return "🔴"
    
    def _get_confidence_badge(self, confidence: float) -> str:
        """Get confidence badge text."""
        if confidence > 0.7:
            return "`HIGH`"
        elif confidence > 0.5:
            return "`MODERATE`"
        elif confidence > 0.3:
            return "`LOW`"
        else:
            return "`NO MATCH`" 