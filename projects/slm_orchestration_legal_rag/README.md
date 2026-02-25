# 🏛️ SLM Orchestration Legal RAG System

## Overview

This is the main research project demonstrating how Small Language Models (SLM) can effectively orchestrate multi-agent legal RAG systems.

## Key Features

- **SLM Orchestrator**: Flan-T5-small (80M parameters) for intelligent agent coordination
- **Multi-Agent Architecture**: 5 specialized agents working in coordination
- **Legal Document Retrieval**: 21,000+ legal documents from Indian legal databases
- **Citation Verification**: Ensures all answers are backed by retrieved sources
- **Streamlit UI**: Modern web interface showcasing SLM orchestration decisions

## Project Structure

```
slm_orchestration_legal_rag/
├── slm_orchestration_app.py    # Main application entry point
├── orchestrators/              # Orchestrator implementations
│   ├── flan_t5_orchestrator.py
│   ├── gpt4_orchestrator.py
│   ├── rule_orchestrator.py
│   └── no_orchestrator.py
├── agents/                     # Agent implementations
│   ├── booster_agent.py
│   ├── retriever_agent.py
│   ├── answering_agent.py
│   ├── citation_verifier.py
│   └── multilingual_agent.py
├── evaluation/                 # Evaluation framework
├── data/                      # Training data
├── models/                    # Trained models
├── tests/                     # Test files
└── chroma_db_consolidated/    # Vector database
```

## Quick Start

```bash
# Navigate to project
cd projects/slm_orchestration_legal_rag

# Install dependencies
pip install -r requirements.txt

# Run the application
python slm_orchestration_app.py

# Or run the Streamlit UI (from root)
streamlit run projects/api_interfaces/ui/legal_ui.py
```

## Documentation

- **Research Paper**: `research/papers/PEARL_doc.pdf` - PEARL: Performance-Efficient Agentic RAG through Learned Orchestration
- **Project Alignment**: See `PEARL_PROJECT_ALIGNMENT.md` for research alignment details
- **Architecture**: See `docs/architecture/` for architecture documentation
- **Guides**: See `docs/guides/` for setup guides
- **Reports**: See `docs/reports/` for project reports

## Related Files

- **UI**: `projects/api_interfaces/ui/legal_ui.py`
- **Database Builders**: `projects/database_builders/`
- **Utilities**: `utilities/`
