"""
Proof Tool Module - Generates comprehensive prompts for Cursor to double-check field mappings
and provide creative solutions for unmapped fields.
"""

from .proof_tool import ProofTool, generate_proof_prompt

__all__ = ['ProofTool', 'generate_proof_prompt'] 