"""
Cognitive matching algorithms for semantic field mapping.
Uses cognitive science principles to find semantic similarities between fields.
"""

import re
from typing import List, Dict, Tuple, Set
from difflib import SequenceMatcher
from .mapping_models import CognitivePattern


class CognitiveMatcher:
    """Cognitive matching algorithms for field mapping."""
    
    def __init__(self):
        """Initialize with common patterns and synonyms."""
        self.synonyms = {
            # Employee/User patterns
            'employee': ['emp', 'staff', 'worker', 'person', 'user'],
            'user': ['employee', 'emp', 'person', 'member'],
            'id': ['identifier', 'key', 'uuid', 'guid', 'number'],
            
            # Business patterns
            'department': ['dept', 'division', 'team', 'group', 'unit'],
            'company': ['org', 'organization', 'corp', 'corporation', 'business'],
            'address': ['addr', 'location', 'place'],
            'phone': ['telephone', 'tel', 'mobile', 'cell'],
            'email': ['mail', 'e_mail', 'electronic_mail'],
            
            # HR specific patterns
            'salary': ['wage', 'pay', 'compensation', 'income'],
            'position': ['role', 'title', 'job', 'designation'],
            'manager': ['supervisor', 'boss', 'lead', 'head'],
            'hire': ['start', 'join', 'onboard', 'employment'],
            'termination': ['end', 'leave', 'exit', 'offboard'],
        }
        
        self.abbreviations = {
            'emp': 'employee',
            'dept': 'department', 
            'addr': 'address',
            'tel': 'telephone',
            'org': 'organization',
            'corp': 'corporation',
            'mgr': 'manager',
            'pos': 'position',
            'loc': 'location',
            'val': 'value',
            'num': 'number',
            'str': 'string',
            'dt': 'date',
            'ts': 'timestamp',
        }
        
        self.domain_patterns = {
            # HR domain patterns
            'hr': ['employee', 'staff', 'hire', 'termination', 'salary', 'department'],
            'finance': ['salary', 'wage', 'cost', 'budget', 'expense'],
            'contact': ['email', 'phone', 'address', 'contact'],
            'identity': ['id', 'name', 'identifier', 'key'],
            'temporal': ['date', 'time', 'created', 'updated', 'start', 'end'],
        }
    
    def calculate_similarity_score(self, source_field: str, target_field: str) -> float:
        """
        Calculate overall similarity score between two field names.
        
        Args:
            source_field: Source field name
            target_field: Target field name
            
        Returns:
            float: Similarity score between 0.0 and 1.0
        """
        # Normalize field names
        source_normalized = self._normalize_field_name(source_field)
        target_normalized = self._normalize_field_name(target_field)
        
        # Calculate different similarity metrics
        exact_match = 1.0 if source_normalized == target_normalized else 0.0
        semantic_sim = self._semantic_similarity(source_normalized, target_normalized)
        structural_sim = self._structural_similarity(source_field, target_field)
        abbreviation_sim = self._abbreviation_similarity(source_normalized, target_normalized)
        
        # Weighted combination
        weights = {
            'exact': 0.4,
            'semantic': 0.3,
            'structural': 0.2,
            'abbreviation': 0.1
        }
        
        total_score = (
            exact_match * weights['exact'] +
            semantic_sim * weights['semantic'] +
            structural_sim * weights['structural'] +
            abbreviation_sim * weights['abbreviation']
        )
        
        return min(total_score, 1.0)
    
    def find_cognitive_patterns(self, source_field: str, target_field: str) -> List[CognitivePattern]:
        """
        Find cognitive patterns between source and target fields.
        
        Args:
            source_field: Source field name
            target_field: Target field name
            
        Returns:
            List[CognitivePattern]: List of identified patterns
        """
        patterns = []
        source_norm = self._normalize_field_name(source_field)
        target_norm = self._normalize_field_name(target_field)
        
        # Check for exact match
        if source_norm == target_norm:
            patterns.append(CognitivePattern(
                pattern_type="exact_match",
                source_pattern=source_field,
                target_pattern=target_field,
                confidence=1.0,
                explanation="Exact field name match"
            ))
        
        # Check for synonym patterns
        synonym_score = self._check_synonym_patterns(source_norm, target_norm)
        if synonym_score > 0.5:
            patterns.append(CognitivePattern(
                pattern_type="synonym",
                source_pattern=source_field,
                target_pattern=target_field,
                confidence=synonym_score,
                explanation=f"Synonym relationship detected"
            ))
        
        # Check for abbreviation patterns
        abbrev_score = self._check_abbreviation_patterns(source_norm, target_norm)
        if abbrev_score > 0.5:
            patterns.append(CognitivePattern(
                pattern_type="abbreviation",
                source_pattern=source_field,
                target_pattern=target_field,
                confidence=abbrev_score,
                explanation="Abbreviation pattern detected"
            ))
        
        # Check for hierarchical patterns
        hier_score = self._check_hierarchical_patterns(source_field, target_field)
        if hier_score > 0.5:
            patterns.append(CognitivePattern(
                pattern_type="hierarchical",
                source_pattern=source_field,
                target_pattern=target_field,
                confidence=hier_score,
                explanation="Hierarchical structure similarity"
            ))
        
        # Check for domain patterns
        domain_score = self._check_domain_patterns(source_norm, target_norm)
        if domain_score > 0.3:
            patterns.append(CognitivePattern(
                pattern_type="domain_specific",
                source_pattern=source_field,
                target_pattern=target_field,
                confidence=domain_score,
                explanation="Domain-specific terminology match"
            ))
        
        return patterns
    
    def _normalize_field_name(self, field_name: str) -> str:
        """Normalize field name for comparison."""
        # Remove common prefixes/suffixes
        normalized = field_name.lower()
        normalized = re.sub(r'[_\-\.]', '', normalized)
        normalized = re.sub(r'(field|attr|prop|column|col)$', '', normalized)
        return normalized.strip()
    
    def _semantic_similarity(self, source: str, target: str) -> float:
        """Calculate semantic similarity using synonyms."""
        # Check direct synonyms
        for word, synonyms in self.synonyms.items():
            if word in source and any(syn in target for syn in synonyms):
                return 0.9
            if word in target and any(syn in source for syn in synonyms):
                return 0.9
        
        # Check partial word matches
        source_words = re.findall(r'\w+', source)
        target_words = re.findall(r'\w+', target)
        
        matches = 0
        total_words = max(len(source_words), len(target_words))
        
        for s_word in source_words:
            for t_word in target_words:
                if s_word == t_word:
                    matches += 1
                elif s_word in self.synonyms.get(t_word, []):
                    matches += 0.8
                elif t_word in self.synonyms.get(s_word, []):
                    matches += 0.8
        
        return matches / total_words if total_words > 0 else 0.0
    
    def _structural_similarity(self, source: str, target: str) -> float:
        """Calculate structural similarity using sequence matching."""
        return SequenceMatcher(None, source.lower(), target.lower()).ratio()
    
    def _abbreviation_similarity(self, source: str, target: str) -> float:
        """Check for abbreviation patterns."""
        # Expand abbreviations
        source_expanded = source
        target_expanded = target
        
        for abbrev, full_form in self.abbreviations.items():
            source_expanded = source_expanded.replace(abbrev, full_form)
            target_expanded = target_expanded.replace(abbrev, full_form)
        
        if source_expanded == target_expanded:
            return 0.9
        
        # Check if one is abbreviation of the other
        if self._is_abbreviation(source, target):
            return 0.8
        
        return 0.0
    
    def _check_synonym_patterns(self, source: str, target: str) -> float:
        """Check for synonym patterns between fields."""
        for word, synonyms in self.synonyms.items():
            if word in source and any(syn in target for syn in synonyms):
                return 0.85
            if word in target and any(syn in source for syn in synonyms):
                return 0.85
        return 0.0
    
    def _check_abbreviation_patterns(self, source: str, target: str) -> float:
        """Check for abbreviation patterns."""
        for abbrev, full_form in self.abbreviations.items():
            if abbrev in source and full_form in target:
                return 0.8
            if abbrev in target and full_form in source:
                return 0.8
        return 0.0
    
    def _check_hierarchical_patterns(self, source: str, target: str) -> float:
        """Check for hierarchical structure patterns."""
        source_parts = re.split(r'[._]', source)
        target_parts = re.split(r'[._]', target)
        
        # Check if one is subset of the other
        if len(source_parts) > 1 and len(target_parts) > 1:
            common_parts = set(source_parts) & set(target_parts)
            if len(common_parts) > 0:
                return 0.6 + (len(common_parts) * 0.1)
        
        return 0.0
    
    def _check_domain_patterns(self, source: str, target: str) -> float:
        """Check for domain-specific patterns."""
        source_domains = set()
        target_domains = set()
        
        for domain, patterns in self.domain_patterns.items():
            if any(pattern in source for pattern in patterns):
                source_domains.add(domain)
            if any(pattern in target for pattern in patterns):
                target_domains.add(domain)
        
        common_domains = source_domains & target_domains
        if len(common_domains) > 0:
            return 0.4 + (len(common_domains) * 0.2)
        
        return 0.0
    
    def _is_abbreviation(self, short: str, long: str) -> bool:
        """Check if short is an abbreviation of long."""
        if len(short) >= len(long):
            return False
        
        # Simple heuristic: check if characters of short appear in order in long
        long_index = 0
        for char in short:
            while long_index < len(long) and long[long_index].lower() != char.lower():
                long_index += 1
            if long_index >= len(long):
                return False
            long_index += 1
        
        return True 