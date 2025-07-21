"""
Prompt templates for field enhancement agent.
"""

FIELD_ENHANCEMENT_PROMPT = """
Du bist ein Experte für semantische Datenanalyse und HRIS-Systeme.

Analysiere die folgenden extrahierten Felder und erstelle eine KOMPAKTE semantische Beschreibung.

KONTEXT:
Processing Notes: {processing_notes}
Business Context: {context}

FELDER ZU ANALYSIEREN:
{extracted_fields}

AUFGABE:
Für jedes Feld in extracted_fields, erstelle eine umfassende semantische Analyse:

1. **Semantic Description**: Detaillierte Beschreibung was das Feld bedeutet und repräsentiert, 1 Satz
2. **Synonyms**: Alternative Bezeichnungen in anderen Systemen (z.B. emp_id, worker_id für employee_id)
3. **Possible Datatypes**: Welche Datentypen sind möglich (string, integer, date, boolean, etc.)
4. **Business Context**: Einordnung in den Geschäftskontext, wo wird das Feld verwendet?

WICHTIGE REGELN:
- KURZE, prägnante Beschreibungen (max 50 Wörter pro Feld)
- MAXIMAL 3 Synonyme pro Feld
- MAXIMAL 3 Datentypen pro Feld  
- Antworte NUR mit validem JSON, KEINE Markdown-Blöcke

FORMAT (kompaktes JSON):
{{
    "enhanced_fields": [
        {{
            "field_name": "method",
            "semantic_description": "HTTP-Methode für API-Requests",
            "synonyms": ["http_method", "verb", "action"],
            "possible_datatypes": ["string", "enum"],
            "business_context": "API Integration"
        }},
        {{
            "field_name": "employee_id", 
            "semantic_description": "Eindeutige Mitarbeiter-Identifikation",
            "synonyms": ["emp_id", "worker_id", "staff_id"],
            "possible_datatypes": ["string", "integer"],
            "business_context": "HR Management"
        }}
    ],
    "processing_context": "HRIS field enhancement",
    "enhancement_confidence": 0.95
}}

Antworte NUR mit dem JSON-Objekt, keine zusätzlichen Texte!
"""