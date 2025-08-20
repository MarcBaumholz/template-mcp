# 🧹 MCP Template Server - Tool Cleanup & Übersicht

## ✅ **AKTIVE TOOLS (Single Source of Truth)**

### 🎯 **Haupt-Orchestrator**
- **`reasoning_agent.py`** - **MASTER TOOL**
  - **Funktion**: End-to-End Schema Mapping Orchestrator mit integrierter Proof Tool Funktionalität
  - **Verantwortlich für**: Vollständige Mapping-Pipeline von Source-Analyse bis Creative Solutions
  - **Integriert**: Proof Tool Funktionalität (unmapped fields detection + creative solutions)
  - **MCP Tool**: `reasoning_agent()`

### 📊 **JSON Analyse Tools**
- **`json_tool/combined_analysis_agent.py`** - **AKTIV**
  - **Funktion**: Vereinfachte JSON-Feldextraktion mit semantischer Erweiterung
  - **Verantwortlich für**: Identifizierung relevanter Felder + semantische Beschreibungen
  - **MCP Tool**: `analyze_json_fields_with_rag()`

- **`json_tool/json_agent.py`** - **AKTIV** (wird von combined_analysis_agent verwendet)
  - **Funktion**: Basis JSON-Feldextraktion
  - **Verantwortlich für**: Grundlegende JSON-Struktur-Analyse

### 🔍 **RAG & API Tools**
- **`rag_tools.py`** - **AKTIV**
  - **Funktion**: RAG-System für API-Spezifikation Analyse
  - **Verantwortlich für**: Vector DB Operations, API Spec Upload/Query
  - **MCP Tools**: `upload_api_specification()`, `query_api_specification()`, `delete_api_specification()`

- **`api_spec_getter.py`** - **AKTIV**
  - **Funktion**: Direkte API-Spec Analyse für kleine Specs
  - **Verantwortlich für**: Context Window basierte Analyse ohne RAG
  - **MCP Tool**: `get_direct_api_mapping_prompt()`

### 💻 **Code Generation**
- **`codingtool/biggerprompt.py`** - **AKTIV**
  - **Funktion**: Kotlin Mapping Code Generation
  - **Verantwortlich für**: Prompt-Generierung für Cursor/LLM Code-Erstellung
  - **MCP Tool**: `generate_kotlin_mapping_code()`

### 🔧 **Utility Tools**
- **`llm_client.py`** - **AKTIV**
  - **Funktion**: LLM Communication Utilities
  - **Verantwortlich für**: OpenRouter API Calls, Response Handling

- **`rag_helper.py`** - **AKTIV**
  - **Funktion**: RAG System Helper Functions
  - **Verantwortlich für**: Qdrant Integration, Vector Operations

---

## 📦 **ARCHIVIERTE TOOLS (_archive/)**

### 🗂️ **Duplikate & Legacy Mapping Tools**
- `mapping.py` - Alte Multi-Agent Mapping Implementation
- `ai_agents.py` - Multi-Agent System (ersetzt durch reasoning_agent)
- `cognitive_matcher.py` - Cognitive Pattern Matching (integriert in reasoning_agent)
- `input_parser.py` - JSON Input Parser (ersetzt durch json_tool)
- `report_generator.py` - Markdown Report Generator (integriert in reasoning_agent)
- `mapping_models.py` - Pydantic Models für altes Mapping System
- `field_enhancer.py` - Field Enhancement (ersetzt durch combined_analysis_agent)
- `json_tools.py` - Alte JSON Tools (ersetzt durch json_tool/)
- `proof_tool/` - **INTEGRIERT IN reasoning_agent**
- `rag_tools.py.backup` - Backup der RAG Tools

---

## 🚫 **NICHT VERWENDETE TOOLS (_unused/)**

### 🔧 **Referenziert aber Inaktiv**
- `mapping_fixed.py` - Enhanced Mapping Tool (im Code referenziert aber deaktiviert)
- `enhancer/` - Field Enhancement System (im Code referenziert aber deaktiviert)

---

## 🎯 **WORKFLOW ÜBERSICHT**

### **Standard HR API Mapping Workflow:**

1. **JSON Analyse** → `analyze_json_fields_with_rag()`
   - Extrahiert relevante Felder aus HR JSON
   - Generiert semantische Beschreibungen

2. **Schema Mapping** → `reasoning_agent()`
   - Analysiert Source Fields vs API Spec
   - Identifiziert unmapped fields automatisch
   - Generiert creative solutions für unmapped fields
   - Erstellt comprehensive implementation guide

3. **Code Generation** → `generate_kotlin_mapping_code()`
   - Generiert Kotlin Mapping Code Prompts
   - Verwendet Mapping Report für Code-Generierung

### **RAG System Support:**
- `upload_api_specification()` - API Specs in Vector DB laden
- `query_api_specification()` - Direkte RAG Queries
- `get_direct_api_mapping_prompt()` - Alternative für kleine Specs

---

## 📈 **CLEANUP ERGEBNISSE**

### ✅ **Was erreicht wurde:**
- **9 Tools archiviert** (Duplikate & Legacy Code)
- **2 Tools als unused markiert** (referenziert aber inaktiv)
- **7 aktive Tools** bleiben (Single Source of Truth)
- **Proof Tool integriert** in reasoning_agent
- **JSON Tools konsolidiert** in json_tool/
- **Saubere Tool-Hierarchie** etabliert

### 🎯 **Aktive MCP Tools (nur diese sind verfügbar):**
1. `reasoning_agent()` - **MASTER ORCHESTRATOR**
2. `analyze_json_fields_with_rag()` - JSON Analyse
3. `upload_api_specification()` - RAG Upload
4. `query_api_specification()` - RAG Query
5. `delete_api_specification()` - RAG Delete
6. `get_direct_api_mapping_prompt()` - Direkte API Analyse
7. `generate_kotlin_mapping_code()` - Code Generation

---

## 🚀 **EMPFOHLENE NUTZUNG**

**Für vollständiges HR API Mapping:**
```
1. analyze_json_fields_with_rag() - Analysiere HR JSON
2. reasoning_agent() - Vollständige Mapping-Analyse mit Proof Tool
3. generate_kotlin_mapping_code() - Generiere Implementation Code
```

**Der reasoning_agent ist jetzt der zentrale Orchestrator mit integrierter Proof Tool Funktionalität - verwende diesen für komplette End-to-End Mappings!**