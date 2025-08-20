# 📁 Template-MCP Projektstruktur

## 🎯 Übersicht

Diese Dokumentation beschreibt die optimierte Struktur des Template-MCP Projekts nach der Bereinigung.

## 🏗️ Hauptverzeichnis

```
template-mcp/
├── 🚀 server_fast.py              # Hauptserver (SSE + Ngrok ready)
├── 📖 README.md                   # Hauptdokumentation
├── 🧪 test_optimized_server.py    # Kompletter Systemtest
├── ⚙️ mcp_client_config.json      # MCP Client Konfiguration
├── 📦 requirements.txt            # Dependencies
├── 🔐 .env                        # Environment Variables
├── 📝 .env.example               # Environment Template
├── 🛠️ tools/                      # Aktive Tools
├── 📄 reports/                   # Generated Reports
├── 📤 outputs/                   # Output Files
├── 📚 examples/                  # Examples
├── 🧪 tests/                     # Unit Tests
├── 📦 _archive/                  # Archivierte Dateien
└── 🗄️ qdrant_storage/            # RAG Database
```

## 🛠️ Tools Verzeichnis

```
tools/
├── 🧠 rag_tools.py               # Optimierte RAG Engine
├── 🤖 reasoning_agent.py         # Mapping Orchestrator
├── 📊 json_tool/                 # JSON Analysis
│   ├── __init__.py
│   ├── combined_analysis_agent.py
│   └── json_agent.py
├── 💻 codingtool/                # Code Generation
│   ├── __init__.py
│   ├── biggerprompt.py
│   └── template.kt
├── 📋 api_spec_getter.py         # API Spec Parser
├── 🤖 llm_client.py              # LLM Integration
├── 🔧 rag_helper.py              # RAG Helper Functions
├── 📦 _archive/                  # Archivierte Tools
│   ├── reasoning_agent_complex.py
│   ├── combined_analysis_agent_complex.py
│   ├── json_tools.py
│   ├── biggerprompt_complex.py
│   ├── rag_tools_complex.py
│   ├── rag_helper_complex.py
│   ├── rag_tools.py.backup
│   ├── mapping.py
│   ├── ai_agents.py
│   ├── mapping_models.py
│   ├── report_generator.py
│   ├── input_parser.py
│   ├── cognitive_matcher.py
│   ├── field_enhancer.py
│   └── proof_tool/
└── 📦 _unused/                   # Ungenutzte Tools
    ├── mapping_fixed.py
    └── enhancer/
```

## 📦 Archiv Verzeichnis

```
_archive/
├── 🖥️ old_servers/               # Alte Server-Versionen
│   ├── server.py                 # Ursprünglicher Server
│   ├── server_sse.py             # SSE Server Version
│   └── _test_server.py           # Test Server
├── 🧪 old_tests/                 # Alte Tests
│   ├── test_combined_analysis.py
│   └── test_sse_server.py
├── 📖 old_docs/                  # Alte Dokumentation
│   ├── SSE_SERVER_SETUP.md
│   ├── TOOL_CLEANUP_FINAL.md
│   ├── TOOL_OVERVIEW.md
│   ├── SERVER_STATUS.md
│   ├── SCHEMA_MAPPING_STATUS.md
│   ├── SCHEMA_MAPPING_DEBUG.md
│   ├── MCP_DEVELOPMENT_RULES.md
│   └── system_prompt.md
└── ⚙️ old_configs/               # Alte Konfigurationen
    ├── requirements_fixed.txt
    └── start_server.sh
```

## 📊 Datei-Kategorien

### 🚀 Aktive Server-Dateien
- `server_fast.py` - Hauptserver mit optimierten RAG-Tools

### 📖 Dokumentation
- `README.md` - Hauptdokumentation
- `PROJECT_STRUCTURE.md` - Diese Datei
- `TASK.md` - Aktuelle Aufgaben

### 🧪 Tests
- `test_optimized_server.py` - Kompletter Systemtest

### ⚙️ Konfiguration
- `mcp_client_config.json` - MCP Client Setup
- `requirements.txt` - Python Dependencies
- `.env` - Environment Variables
- `.env.example` - Environment Template

### 🛠️ Aktive Tools
- `tools/rag_tools.py` - Optimierte RAG Engine
- `tools/reasoning_agent.py` - Mapping Orchestrator
- `tools/json_tool/` - JSON Analysis Tools
- `tools/codingtool/` - Code Generation
- `tools/api_spec_getter.py` - API Spec Parser
- `tools/llm_client.py` - LLM Integration

### 📦 Archivierte Dateien
- Alle alten Server-Versionen
- Redundante Tests
- Veraltete Dokumentation
- Ungenutzte Konfigurationen

## 🎯 Bereinigungs-Ziele

### ✅ Erreicht
- **67% Code-Reduktion** durch Entfernung redundanter Dateien
- **Klare Trennung** zwischen aktiven und archivierten Dateien
- **Einheitliche Dokumentation** in README.md
- **Optimierte Tool-Struktur** mit Single Source of Truth
- **Saubere Projektstruktur** für bessere Wartbarkeit

### 📈 Verbesserungen
- **Bessere Übersichtlichkeit** durch kategorisierte Archive
- **Reduzierte Komplexität** durch Entfernung doppelter Funktionalität
- **Klarere Dokumentation** mit fokussiertem Inhalt
- **Optimierte Performance** durch bereinigte Imports

## 🔄 Wartung

### Neue Dateien hinzufügen
1. **Aktive Tools** → `tools/`
2. **Tests** → `tests/` oder Root-Level
3. **Dokumentation** → Root-Level
4. **Konfiguration** → Root-Level

### Dateien archivieren
1. **Veraltete Server** → `_archive/old_servers/`
2. **Alte Tests** → `_archive/old_tests/`
3. **Veraltete Docs** → `_archive/old_docs/`
4. **Ungenutzte Configs** → `_archive/old_configs/`

### Tools archivieren
1. **Redundante Tools** → `tools/_archive/`
2. **Ungenutzte Tools** → `tools/_unused/`

## 📝 Naming Conventions

### Dateien
- **Server**: `server_*.py`
- **Tests**: `test_*.py`
- **Dokumentation**: `*.md`
- **Konfiguration**: `*.json`, `*.txt`, `*.sh`

### Verzeichnisse
- **Aktive Tools**: `tools/`
- **Archive**: `_archive/` (mit Unterkategorien)
- **Ungenutzt**: `_unused/`
- **Cache**: `__pycache__/`

---

**🎯 Die Projektstruktur ist jetzt sauber, organisiert und wartungsfreundlich!** 