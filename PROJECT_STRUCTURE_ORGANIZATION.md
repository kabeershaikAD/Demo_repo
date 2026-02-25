# 📁 PROJECT STRUCTURE ORGANIZATION

## 🎯 Overview

This document provides a comprehensive mapping of all files to their respective projects and the new organized structure.

---

## 📦 **PROJECT 1: SLM Orchestration Legal RAG System**
**Location:** `projects/slm_orchestration_legal_rag/`

### **Core Application Files**
- `Buddy/agentic_legal_rag/slm_orchestration_app.py` → Main application
- `Buddy/agentic_legal_rag/agent_adapters.py` → Agent compatibility
- `Buddy/agentic_legal_rag/config.py` → Configuration
- `legal_ui.py` → Streamlit UI (root level, uses SLM system)

### **Orchestrators**
- `Buddy/agentic_legal_rag/orchestrators/` → All orchestrator implementations

### **Agents**
- `Buddy/agentic_legal_rag/booster_agent.py`
- `Buddy/agentic_legal_rag/retriever_agent.py`
- `Buddy/agentic_legal_rag/answering_agent.py`
- `Buddy/agentic_legal_rag/citation_verifier.py`
- `Buddy/agentic_legal_rag/multilingual_agent.py`
- `agents/` (root level) → Move to project if used

### **Evaluation Framework**
- `Buddy/agentic_legal_rag/evaluation/` → All evaluation files

### **Data & Database**
- `Buddy/agentic_legal_rag/data/` → Training data
- `Buddy/agentic_legal_rag/chroma_db_/` → Vector database
- `chroma_db_consolidated/` → Consolidated vector DB

### **Documentation**
- `SLM_BASED_ARCHITECTURE.md`
- `SLM_ORCHESTRATOR_REDESIGN.md`
- `FULLY_SLM_BASED_DESIGN.md`
- `Buddy/agentic_legal_rag/README_SLM_ORCHESTRATION.md`
- `Buddy/agentic_legal_rag/README.md`
- `Buddy/agentic_legal_rag/README_COMPLETE.md`
- `Buddy/agentic_legal_rag/QUICK_START_GUIDE.md`

### **Training & Model Files**
- `Buddy/agentic_legal_rag/models/` → Trained models
- `Buddy/agentic_legal_rag/train_*.py` → Training scripts
- `Buddy/agentic_legal_rag/generate_*.py` → Data generation scripts

---

## 📦 **PROJECT 2: Indian Law Voicebot**
**Location:** `projects/indian_law_voicebot/`

### **Core Files**
- `Buddy/Indian-Law-Voicebot/workingone.py` → Main application
- `Buddy/Indian-Law-Voicebot/README.md`
- `Buddy/Indian-Law-Voicebot/requirements.txt`
- `Buddy/Indian-Law-Voicebot/law_buddy.db` → Database
- `Buddy/Indian-Law-Voicebot/chroma_db_/` → Vector database
- `Buddy/Indian-Law-Voicebot/evaluation/` → Evaluation files
- `Buddy/Indian-Law-Voicebot/ground_truths.csv` → Test data

---

## 📦 **PROJECT 3: Database Builders & Data Processing**
**Location:** `projects/database_builders/`

### **Database Building Scripts**
- `build_indian_legal_database.py` → Main database builder
- `indian_legal_database.py` → Database manager
- `indian_kanoon_api.py` → API client
- `dynamic_updater.py` → Real-time updates
- `consolidate_chromadb.py` → ChromaDB consolidation
- `fix_consolidated_db.py` → Database fixes
- `add_docs_to_chromadb.py` → Add documents
- `add_poc_data.py` → Add POC data
- `check_sqlite_db.py` → Database checker

### **Data Processing**
- `data_processing/` → All data processing utilities
- `dataset_loader.py` → Dataset loader
- `updater.py` → Update utilities

### **Database Files**
- `indian_legal_db.sqlite` → SQLite database
- `vector_db/` → FAISS vector database

---

## 📦 **PROJECT 4: Testing & Evaluation**
**Location:** `projects/testing_evaluation/`

### **Test Scripts**
- `test_orchestration_queries.py` → Orchestration tests
- `test_retriever_debug.py` → Retriever debugging
- `test_llm_init.py` → LLM initialization tests
- `diagnose_retriever_issue.py` → Retriever diagnostics
- `diagnose_retriever.py` → Retriever diagnostics
- `run_tests.py` → Test runner
- `tests/` → Test suite (root level)
- `Buddy/agentic_legal_rag/tests/` → SLM project tests
- `Buddy/agentic_legal_rag/test_*.py` → All test files

### **Evaluation Scripts**
- `evaluation.py` → Main evaluation script
- `Buddy/agentic_legal_rag/evaluation/` → Evaluation framework

---

## 📦 **PROJECT 5: API & Interfaces**
**Location:** `projects/api_interfaces/`

### **API Files**
- `api/main.py` → FastAPI main
- `api/models.py` → API models

### **UI Files**
- `legal_ui.py` → Streamlit UI (uses SLM system)

---

## 📦 **PROJECT 6: Documentation**
**Location:** `docs/`

### **Architecture & Design**
- `SLM_BASED_ARCHITECTURE.md`
- `SLM_ORCHESTRATOR_REDESIGN.md`
- `FULLY_SLM_BASED_DESIGN.md`
- `ROUTING_FIXES.md`
- `ANALYSIS_COMPARISON.md`
- `BEFORE_AFTER_SUMMARY.md`
- `COMPREHENSIVE_ANALYSIS.md`

### **Project Reports**
- `COMPREHENSIVE_PROJECT_REPORT.md`
- `FINAL_SUMMARY.md`
- `CLEAN_PROJECT_STRUCTURE.md`

### **Setup & Guides**
- `SETUP.md`
- `ENHANCED_README.md`
- `README.md` (root)
- `HOD_PRESENTATION_GUIDE.md`
- `PANEL_DEMONSTRATION_GUIDE.md`
- `DEMO_QUERIES.md`

### **Fixes & Issues**
- `FIXES_APPLIED.md`
- `FIX_PUSH_ISSUE.md`
- `FIX_RETRIEVER_ISSUE.md`
- `RETRIEVER_FIXES.md`

### **Database Documentation**
- `CHROMADB_CONSOLIDATION_GUIDE.md`
- `CONSOLIDATION_COMPLETE.md`
- `DATABASE_CONTENTS_SUMMARY.md`

### **GitHub & Deployment**
- `GITHUB_SETUP.md`
- `GITHUB_AUTH_INSTRUCTIONS.md`
- `SIMPLE_PUSH_GUIDE.md`
- `FILES_TO_PUSH.md`

### **Explanations**
- `CONFIDENCE_EXPLANATION.md`
- `EXPLAIN_DIRECT_ANSWER.md`

### **Existing Docs Folder**
- `docs/` → Keep as is, contains API reference, architecture, etc.

---

## 📦 **PROJECT 7: Configuration & Setup**
**Location:** `config/`

### **Configuration Files**
- `config.py` → Main config
- `config.env` → Environment variables
- `env_example.txt` → Environment template

### **Setup Scripts**
- `setup.py` → Package setup
- `setup_api_keys.ps1` → API key setup (PowerShell)
- `Buddy/agentic_legal_rag/setup_slm_orchestration.py` → SLM setup
- `Buddy/agentic_legal_rag/setup_nltk.py` → NLTK setup

### **GitHub Scripts**
- `push_to_github.ps1` → GitHub push script
- `quick_push.ps1` → Quick push script

---

## 📦 **PROJECT 8: Research Materials**
**Location:** `research/`

### **Research Papers**
- `Research_papers/` → All research papers

### **Academic Documents**
- `Comprehensive Literature Review.docx`
- `3001_1__abstract_major.docx`

---

## 📦 **PROJECT 9: Utilities & Scripts**
**Location:** `utilities/`

### **Utility Scripts**
- `Buddy/agentic_legal_rag/check_database.py`
- `Buddy/agentic_legal_rag/load_chroma.py`
- `Buddy/agentic_legal_rag/load_kaggle_data.py`
- `Buddy/agentic_legal_rag/load_supreme_court_fixed.py`
- `Buddy/agentic_legal_rag/data_loader.py`
- `Buddy/agentic_legal_rag/ingest.py`
- `Buddy/agentic_legal_rag/embed.py`
- `Buddy/agentic_legal_rag/preprocess.py`
- `Buddy/agentic_legal_rag/scraper.py`
- `Buddy/agentic_legal_rag/document_to_vectordb.py`
- `Buddy/agentic_legal_rag/analyze_document_structure.py`

### **Demo Scripts**
- `Buddy/agentic_legal_rag/hod_demo.py`
- `Buddy/agentic_legal_rag/demo_system.py`
- `Buddy/agentic_legal_rag/demo_ingestion.py`
- `Buddy/agentic_legal_rag/demo_bootstrap.py`

---

## 📁 **NEW ORGANIZED STRUCTURE**

```
Major project/
├── projects/
│   ├── slm_orchestration_legal_rag/     # Project 1
│   │   ├── core/                        # Core application files
│   │   ├── orchestrators/               # Orchestrator implementations
│   │   ├── agents/                      # Agent implementations
│   │   ├── evaluation/                  # Evaluation framework
│   │   ├── data/                        # Training data
│   │   ├── models/                      # Trained models
│   │   ├── tests/                       # Test files
│   │   ├── docs/                        # Project-specific docs
│   │   └── chroma_db_/                  # Vector database
│   │
│   ├── indian_law_voicebot/             # Project 2
│   │   ├── core/                        # Core files
│   │   ├── evaluation/                 # Evaluation
│   │   └── chroma_db_/                  # Vector database
│   │
│   ├── database_builders/               # Project 3
│   │   ├── scripts/                     # Building scripts
│   │   ├── data_processing/             # Data processing
│   │   └── databases/                   # Database files
│   │
│   ├── testing_evaluation/              # Project 4
│   │   ├── tests/                       # Test scripts
│   │   └── evaluation/                  # Evaluation scripts
│   │
│   └── api_interfaces/                  # Project 5
│       ├── api/                         # API files
│       └── ui/                          # UI files
│
├── docs/                                 # Project 6 - All documentation
│   ├── architecture/                    # Architecture docs
│   ├── guides/                          # Setup guides
│   ├── reports/                         # Project reports
│   └── fixes/                           # Fix documentation
│
├── config/                               # Project 7 - Configuration
│   ├── config.py
│   ├── config.env
│   └── setup_scripts/                   # Setup scripts
│
├── research/                             # Project 8 - Research materials
│   ├── papers/                          # Research papers
│   └── academic/                        # Academic documents
│
├── utilities/                            # Project 9 - Utilities
│   ├── database/                        # Database utilities
│   ├── data_loading/                    # Data loading scripts
│   └── demos/                           # Demo scripts
│
├── logs/                                 # System logs (keep as is)
├── chroma_db_consolidated/              # Consolidated vector DB
├── requirements.txt                      # Root requirements
└── README.md                             # Root README
```

---

## 🔄 **MIGRATION PLAN**

### **Phase 1: Create New Structure**
1. Create all new directories
2. Create project README files

### **Phase 2: Move Files**
1. Move SLM Orchestration files
2. Move Database Builder files
3. Move Testing files
4. Move Documentation files
5. Move Configuration files
6. Move Research materials
7. Move Utility scripts

### **Phase 3: Update Imports**
1. Update all import paths
2. Update configuration paths
3. Test all applications

### **Phase 4: Cleanup**
1. Remove empty directories
2. Update documentation
3. Create final structure document

---

## ✅ **FILE MAPPING SUMMARY**

| Category | Count | Location |
|----------|-------|----------|
| SLM Orchestration | ~80 files | `projects/slm_orchestration_legal_rag/` |
| Voicebot | ~10 files | `projects/indian_law_voicebot/` |
| Database Builders | ~15 files | `projects/database_builders/` |
| Testing | ~20 files | `projects/testing_evaluation/` |
| API/UI | ~5 files | `projects/api_interfaces/` |
| Documentation | ~30 files | `docs/` |
| Configuration | ~10 files | `config/` |
| Research | ~5 files | `research/` |
| Utilities | ~15 files | `utilities/` |

**Total:** ~190 files organized into 9 project categories









