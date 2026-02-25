# Your PEARL Project Location and Required Files

## 🎯 Main Project Location

**Your main project is located at:**
```
C:\Users\Lenovo\Downloads\Collage_Materials\Major project\projects\slm_orchestration_legal_rag\
```

**Full Path:**
```
C:\Users\Lenovo\Downloads\Collage_Materials\Major project\projects\slm_orchestration_legal_rag
```

---

## 📁 Project Structure Overview

```
projects/slm_orchestration_legal_rag/
│
├── 🚀 MAIN APPLICATION FILES
│   ├── slm_orchestration_app.py          # Main entry point - Run this!
│   ├── orchestrator.py                   # Main orchestrator
│   ├── config.py                         # Configuration file
│   └── app.py                            # Alternative app entry
│
├── 🤖 ORCHESTRATORS (Core Intelligence)
│   └── orchestrators/
│       ├── flan_t5_orchestrator.py      # ⭐ Your SLM orchestrator (main contribution)
│       ├── gpt4_orchestrator.py         # GPT-4 baseline
│       ├── rule_orchestrator.py         # Rule-based baseline
│       ├── no_orchestrator.py           # No orchestration baseline
│       └── workflow_optimizer.py        # Workflow optimization
│
├── 🎯 AGENTS (Specialized Workers)
│   ├── booster_agent.py                 # Query enhancement agent
│   ├── retriever_agent.py               # Document retrieval agent
│   ├── answering_agent.py               # Answer generation agent
│   ├── citation_verifier.py             # Citation verification agent
│   └── multilingual_agent.py            # Multilingual support agent
│
├── 📚 TRAINING & DATA COLLECTION
│   └── training/
│       ├── collect_expert_traces.py     # ⭐ Collect GPT-4 traces
│       ├── knowledge_distillation.py   # ⭐ Train Flan-T5 model
│       └── (other training files)
│
├── 📊 EVALUATION
│   └── evaluation/
│       ├── orchestration_metrics.py     # ⭐ RAS/WAI metrics
│       ├── run_orchestration_evaluation.py
│       ├── orchestration_test_dataset.json
│       └── orchestration_evaluation_report.md
│
├── 💾 DATA FILES
│   └── data/
│       ├── expert_traces/               # ⭐ GPT-4 traces
│       │   ├── expert_traces.jsonl
│       │   └── training_data.jsonl
│       ├── query_booster_500.jsonl      # 500 legal queries
│       ├── ai_teacher_dataset.jsonl    # Training dataset
│       └── (other data files)
│
├── 🗄️ DATABASE
│   ├── chroma_db_/                      # Vector database
│   └── chroma_db_consolidated/         # Consolidated database
│
├── 📖 DOCUMENTATION
│   ├── README.md                        # Main README
│   ├── PEARL_IMPLEMENTATION_GUIDE.md
│   ├── PEARL_PROJECT_ALIGNMENT.md
│   └── (other docs)
│
└── ⚙️ CONFIGURATION
    ├── requirements.txt                 # ⭐ Python dependencies
    ├── config.py                        # ⭐ Configuration
    └── slm_config.py                    # SLM-specific config
```

---

## 🔑 Essential Files You Need

### 1. **Main Application Files**

| File | Purpose | Location |
|------|---------|----------|
| `slm_orchestration_app.py` | **Main entry point** - Run this to start the system | `projects/slm_orchestration_legal_rag/` |
| `config.py` | Configuration (API keys, model paths) | `projects/slm_orchestration_legal_rag/` |
| `requirements.txt` | Python dependencies | `projects/slm_orchestration_legal_rag/` |

### 2. **Core Orchestration Files**

| File | Purpose | Location |
|------|---------|----------|
| `orchestrators/flan_t5_orchestrator.py` | **Your SLM orchestrator** (main contribution) | `orchestrators/` |
| `orchestrators/gpt4_orchestrator.py` | GPT-4 baseline for comparison | `orchestrators/` |
| `orchestrators/workflow_optimizer.py` | Workflow optimization | `orchestrators/` |

### 3. **Agent Files**

| File | Purpose | Location |
|------|---------|----------|
| `booster_agent.py` | Query enhancement | Root |
| `retriever_agent.py` | Document retrieval | Root |
| `answering_agent.py` | Answer generation | Root |
| `citation_verifier.py` | Citation verification | Root |
| `multilingual_agent.py` | Multilingual support | Root |

### 4. **Training Files**

| File | Purpose | Location |
|------|---------|----------|
| `training/collect_expert_traces.py` | **Collect GPT-4 traces** | `training/` |
| `training/knowledge_distillation.py` | **Train Flan-T5 model** | `training/` |
| `run_step2_simple.py` | Simplified trace collection | Root |

### 5. **Evaluation Files**

| File | Purpose | Location |
|------|---------|----------|
| `evaluation/orchestration_metrics.py` | **RAS/WAI metrics** | `evaluation/` |
| `evaluation/run_orchestration_evaluation.py` | Run evaluation | `evaluation/` |
| `evaluation/orchestration_test_dataset.json` | Test dataset | `evaluation/` |

### 6. **Data Files**

| File | Purpose | Location |
|------|---------|----------|
| `data/expert_traces/expert_traces.jsonl` | **GPT-4 traces** | `data/expert_traces/` |
| `data/expert_traces/training_data.jsonl` | **Training data** | `data/expert_traces/` |
| `data/query_booster_500.jsonl` | 500 legal queries | `data/` |

---

## 🚀 How to Navigate to Your Project

### Option 1: Using Command Line

```bash
# Navigate to your project
cd "C:\Users\Lenovo\Downloads\Collage_Materials\Major project\projects\slm_orchestration_legal_rag"

# Or from workspace root
cd projects/slm_orchestration_legal_rag
```

### Option 2: Using File Explorer

1. Open File Explorer
2. Navigate to: `C:\Users\Lenovo\Downloads\Collage_Materials\Major project\projects\slm_orchestration_legal_rag`

### Option 3: In VS Code/Cursor

1. Open the folder: `projects/slm_orchestration_legal_rag`
2. Or open the entire workspace: `Major project`

---

## 📋 Quick Reference: What Each Directory Contains

### `/orchestrators/` - Orchestration Logic
- **flan_t5_orchestrator.py**: Your main SLM orchestrator
- **gpt4_orchestrator.py**: GPT-4 baseline
- **workflow_optimizer.py**: Workflow optimization

### `/training/` - Training Scripts
- **collect_expert_traces.py**: Collect GPT-4 traces
- **knowledge_distillation.py**: Train Flan-T5

### `/evaluation/` - Evaluation Framework
- **orchestration_metrics.py**: RAS/WAI metrics
- **run_orchestration_evaluation.py**: Run evaluations

### `/data/` - Data Files
- **expert_traces/**: GPT-4 traces and training data
- **query_booster_500.jsonl**: Legal queries
- **ai_teacher_dataset.jsonl**: Training dataset

### `/chroma_db_consolidated/` - Vector Database
- Contains 21,000+ legal document embeddings
- Used by retriever agent

---

## 🎯 Most Important Files for Your Project

### For Running the System:
1. ✅ `slm_orchestration_app.py` - Main application
2. ✅ `config.py` - Configuration
3. ✅ `requirements.txt` - Dependencies

### For Training:
1. ✅ `training/collect_expert_traces.py` - Collect traces
2. ✅ `training/knowledge_distillation.py` - Train model
3. ✅ `data/query_booster_500.jsonl` - Training queries

### For Evaluation:
1. ✅ `evaluation/orchestration_metrics.py` - Metrics
2. ✅ `evaluation/run_orchestration_evaluation.py` - Run eval
3. ✅ `evaluation/orchestration_test_dataset.json` - Test data

### For Research/Report:
1. ✅ `orchestrators/flan_t5_orchestrator.py` - Main contribution
2. ✅ `PEARL_PROJECT_ALIGNMENT.md` - Project alignment
3. ✅ `GPT4_COMPARISON_RESULTS.md` - Results

---

## 📝 Configuration File Location

**Main Config**: `projects/slm_orchestration_legal_rag/config.py`

**What to configure**:
- OpenAI API key (for GPT-4 traces)
- Groq API key (for answering agent)
- Model paths
- Database paths

---

## 🗄️ Database Locations

**Vector Database (ChromaDB)**:
- `projects/slm_orchestration_legal_rag/chroma_db_consolidated/`
- Contains 21,000+ legal document embeddings

**SQLite Database**:
- `projects/slm_orchestration_legal_rag/chroma_db_consolidated/chroma.sqlite3`

---

## 📊 Documentation Locations

**Project Documentation**:
- `projects/slm_orchestration_legal_rag/README.md`
- `projects/slm_orchestration_legal_rag/PEARL_IMPLEMENTATION_GUIDE.md`

**System Design Documentation**:
- `docs/guides/SYSTEM_DESIGN_PEARL.md`
- `docs/guides/RAS_WAI_METRICS_EXPLANATION.md`
- `docs/guides/GPT_TRACE_COLLECTION_EXPLANATION.md`

**Research Papers**:
- `Research_papers/PEARL_doc draft1.docx`
- `research/papers/` (if exists)

---

## 🔍 Finding Specific Files

### To Find Orchestrator Files:
```
projects/slm_orchestration_legal_rag/orchestrators/
```

### To Find Agent Files:
```
projects/slm_orchestration_legal_rag/
(Look for: booster_agent.py, retriever_agent.py, etc.)
```

### To Find Training Data:
```
projects/slm_orchestration_legal_rag/data/expert_traces/
```

### To Find Evaluation Results:
```
projects/slm_orchestration_legal_rag/evaluation/
```

---

## ✅ Quick Checklist

- [ ] Main project: `projects/slm_orchestration_legal_rag/`
- [ ] Main app: `slm_orchestration_app.py`
- [ ] Config: `config.py`
- [ ] Dependencies: `requirements.txt`
- [ ] SLM Orchestrator: `orchestrators/flan_t5_orchestrator.py`
- [ ] Training scripts: `training/`
- [ ] Evaluation: `evaluation/`
- [ ] Data: `data/expert_traces/`
- [ ] Database: `chroma_db_consolidated/`

---

## 🚀 Next Steps

1. **Navigate to project**: `cd projects/slm_orchestration_legal_rag`
2. **Check config**: Open `config.py` and set API keys
3. **Install dependencies**: `pip install -r requirements.txt`
4. **Run system**: `python slm_orchestration_app.py`

---

**Your project is ready! All files are in:**
```
C:\Users\Lenovo\Downloads\Collage_Materials\Major project\projects\slm_orchestration_legal_rag\
```



