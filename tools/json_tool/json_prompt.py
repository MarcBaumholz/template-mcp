"""
Prompt templates for different agents.
"""

FIELD_EXTRACTION_PROMPT = """
Du bist ein Experte für die Extraktion wichtiger Felder aus HRIS (Human Resource Information System) JSON-Daten.

Analysiere die folgende JSON-Struktur und extrahiere die wichtigsten Felder für eine LangGraph-basierte Verarbeitung:

JSON Data:
{json_data}

AUFGABE:
1. Identifiziere die Kernfelder des JSON-Payloads 
2. Extrahiere API-Path und Event-Typ/body falls vorhanden
3. Bewerte die Vollständigkeit und Validität der Daten
4. Gib eine Konfidenz-Bewertung (0.0-1.0) für die Extraktion ab
5. Füge relevanten Kontext für weitere Verarbeitung hinzu

WICHTIG:
- Antworte NUR mit validem JSON, keine zusätzlichen Erklärungen
- Alle Felder müssen vorhanden sein (nutze null für fehlende Werte)
- confidence_score muss zwischen 0.0 und 1.0 liegen
- validation_status muss einer der drei Werte sein: valid, incomplete, invalid
- gib einen context über das ganze json an

Du MUSST mit einem gültigen JSON-Objekt antworten. Antworte NUR mit JSON, keine zusätzlichen Erklärungen.

FORMAT der Antwort als valides JSON (wird vom LangGraph Agent geparst):
{{
    "extracted_fields": {{
        "path": "API-Path oder null",
        "event_type": "Event-Typ oder null",
        "body": "Body oder null",
        ...
    }},
    "validation_status": "valid|incomplete|invalid",
    "processing_notes": "Detaillierte Beobachtungen zur Datenqualität und gefundenen Feldern",
    "confidence_score": 0.95,
    "context": "Zusätzlicher Kontext für nachgelagerte Agent-Verarbeitung"
}}

"""