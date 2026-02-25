# PEARL Project: Complete Reference

Every file, every function, every capability, every data flow, and every known issue.

---

## Part 1: Project Identity

**Name:** PEARL (Performance-Efficient Agentic RAG through Learned Orchestration)

**What it is:** A multi-agent legal RAG system where a tiny Flan-T5-small model (80M params) orchestrates 5 specialized agents. The SLM was trained via knowledge distillation from GPT-4 traces. The project proves that a small local model can replace expensive GPT-4 API calls for agent orchestration.

**Location on disk:** `C:\Users\Lenovo\Downloads\Collage_Materials\Major project\`

**GitHub:** Pushed to `clean-main` branch of `Demo_repo`.

**Virtual environment:** `C:\Users\Lenovo\Downloads\Collage_Materials\Major project\legal_rag_env`

---

## Part 2: Full Directory Map

### Root Level (Major project/)

| File | Important? | What it does |
|------|-----------|-------------|
| README.md | **Yes** | Main README with setup, usage, architecture, troubleshooting |
| requirements.txt | **Yes** | Python dependencies for the whole project |
| .gitignore | **Yes** | Excludes config.py, model weights, DBs, logs |
| PROJECT_STRUCTURE_FINAL.md | Moderate | Map of where all files were organized |
| PEARL_FRAMEWORK_PROJECT_REPORT.md | Moderate | 24KB research report on the PEARL framework |

---

### Core Project: projects/slm_orchestration_legal_rag/ (MOST IMPORTANT)

#### Main Application Files

| File | Important? | What it does |
|------|-----------|-------------|
| **slm_orchestration_app.py** | **Critical** | Main entry point. Contains SLMOrchestrationApp class |
| **config.py** | **Critical** | Real API keys (GROQ, OpenAI). Gitignored, never committed. |
| config.example.py | **Yes** | Template with placeholder keys. Committed to GitHub. |
| agent_adapters.py | **Yes** | Bridges your agents to the orchestration interface |
| run_pearl_pipeline.py | Moderate | Simplified pipeline runner |

---

#### SLMOrchestrationApp - Class and Functions

| Method | What it does |
|--------|-------------|
| `__init__(orchestrator_type)` | Accepts flan_t5, gpt4, rule, or none. Stores config. |
| `_load_config()` | Returns dict with model name, API keys, device (cuda/cpu) |
| `initialize()` | Creates the chosen orchestrator, creates all 5 agents via adapters, initializes them |
| `process_query(query)` | **Main method.** analyze_query -> route_to_agents -> _execute_agent_workflow. Computes weighted confidence (30% SLM + 45% answer + 25% doc support). |
| `_execute_agent_workflow(query, agent_sequence)` | Loops through agents in order: booster->retriever->answering->verifier->multilingual |
| `run_demo()` | Runs 5 hardcoded demo queries |
| `get_orchestration_metrics()` | Returns metrics from the orchestrator |

**main() function** - CLI entry point: --orchestrator, --query, --demo, --interactive

---

#### Orchestrators: orchestrators/

All 4 extend BaseOrchestrator (core/base_orchestrator.py): analyze_query(), route_to_agents(), execute_workflow(), cost_per_decision, requires_api, get_metrics(), _record_decision()

| File | Class | What it does |
|------|-------|-------------|
| **flan_t5_orchestrator.py** | FlanT5Orchestrator | **Main contribution.** 80M param local SLM. $0.00/decision, ~15ms. |
| gpt4_orchestrator.py | GPT4Orchestrator | Baseline. Uses OpenAI API. ~$0.02/decision, ~500ms. |
| rule_orchestrator.py | RuleBasedOrchestrator | Lower-bound baseline. 7 if-then rules. $0.00, ~0ms. |
| no_orchestrator.py | NoOrchestrator | Always retriever->answering. Shows value of orchestration. |
| workflow_optimizer.py | WorkflowOptimizer | Removes duplicates, enforces dependencies, prunes by complexity. |

##### FlanT5Orchestrator Key Functions

| Method | What it does |
|--------|-------------|
| __init__(config) | Checks for trained model at models/flan_t5_orchestrator/model.safetensors. If found loads trained, else loads google/flan-t5-small. |
| initialize() | Loads T5Tokenizer + T5ForConditionalGeneration to GPU/CPU |
| analyze_query(query) | Sends prompt to Flan-T5 for JSON: complexity, reasoning_type, confidence. Falls back to _fallback_query_analysis. |
| route_to_agents(query, analysis) | Trained: training-format prompt. Base: pattern-selection prompt. Picks pattern from 6 predefined. Calls WorkflowOptimizer. |
| _select_pattern_from_analysis(query, analysis) | Maps analysis to pattern: simple_factual, complex_analytical, comparative, procedural, citation_heavy, vague_query |
| _fallback_query_analysis(query) | Keyword-based analysis when model fails. |

**6 Orchestration Patterns:**

| Pattern | Agents | When Used |
|---------|--------|-----------|
| simple_factual | retriever, answering | Well-formed simple questions |
| complex_analytical | booster, retriever, answering, verifier | Complex analysis queries |
| comparative | booster, retriever, answering, verifier | Comparison queries |
| procedural | booster, retriever, answering | How-to queries |
| citation_heavy | retriever, answering, verifier | Needs verification only |
| vague_query | booster, retriever, answering | Vague/short queries |

##### GPT4Orchestrator Key Functions

| Method | What it does |
|--------|-------------|
| __init__(config) | Creates OpenAI client. cost_per_1k_tokens = 0.03 |
| analyze_query(query) | Sends to GPT-4 API, parses JSON |
| route_to_agents(query, analysis) | Sends to GPT-4 with agent list, parses JSON array |

##### RuleBasedOrchestrator - 7 Rules

| Rule | Condition | Agents |
|------|-----------|--------|
| simple_factual | <10 words + ? | retriever, answering |
| comparison | compare/difference/vs | booster, retriever, answering, verifier |
| complex_analytical | analyze/implications/impact | booster, retriever, answering, verifier |
| definition | what is/define | retriever, answering |
| procedural | how to/steps/process | booster, retriever, answering |
| multilingual | Hindi characters | multilingual, booster, retriever, answering |
| default | catch-all | retriever, answering |

##### WorkflowOptimizer - 4 Steps

1. _remove_duplicates(sequence)
2. _enforce_dependencies(sequence) - retriever before answering, answering before verifier
3. _complexity_aware_pruning(sequence, query, analysis) - minimal for simple factual
4. _remove_redundant_calls(sequence, analysis) - remove booster/verifier if not needed

---

#### Agents (5 specialized workers)

##### booster_agent.py - PromptBooster
- enhance_query(query) -> {boosted_query, confidence, reasoning, retrieval_mode, top_k}
- Uses Flan-T5-small or rule-based mode for Indian legal context
- Dataclass: BoosterDecision (need_boost, boosted_query, retrieval_mode, top_k, confidence)

##### retriever_agent.py - RetrieverAgent
- retrieve(query, k=5) -> RetrievalResult with statutes, judgments, cross_links
- Connects to ChromaDB at chroma_db_consolidated/ using OpenAI embeddings (21,444+ docs)
- Inner class: CitationExtractor (Section X IPC, Article Y patterns)
- Dataclasses: RetrievedDocument (doc_id, content, title, similarity_score, court, date), CrossLink, RetrievalResult

##### answering_agent.py - AnsweringAgent
- generate_answer(query, documents) -> AnswerResult with answer_text, claims, sources, confidence
- Uses Groq LLM (llama-3.1-8b-instant) via LangChain
- Dataclasses: LegalClaim (text, cited_doc_ids, claim_type, verification_status), AnswerResult

##### citation_verifier.py - CitationVerifier
- verify(claims, docs) -> list of VerificationResult
- Semantic similarity using OpenAI embeddings (or SentenceTransformer fallback)
- Threshold: 0.7, Methods: semantic/keyword/hybrid
- Dataclass: VerificationResult (claim_text, supported, confidence, supporting_docs)

##### multilingual_agent.py - MultilingualAgent
- detect_language(text) -> language code (en, hi)
- translate(text, target_lang) -> translated text
- Uses Helsinki-NLP model or keyword-based fallback

##### agent_adapters.py - 5 Adapter Classes

| Adapter | Wraps | process() does |
|---------|-------|----------------|
| BoosterAdapter | PromptBooster | enhance_query(query) |
| RetrieverAdapter | RetrieverAgent | retrieve(query, k=5), converts to dicts |
| AnsweringAdapter | AnsweringAgent | generate_answer(query, docs) |
| VerifierAdapter | CitationVerifier | verify(claims, docs), computes score |
| MultilingualAdapter | MultilingualAgent | detect_language(query) |

---

#### Training: training/

##### knowledge_distillation.py
- OrchestrationDataset: PyTorch Dataset, loads JSONL (input: query+analysis, target: agent sequence)
- SequenceCoherenceLoss: Penalizes invalid orderings (answering before retriever)
- train(): HuggingFace Trainer, saves checkpoints. Supports --resume_from_checkpoint
- CLI args: --data_path, --output_dir, --epochs, --batch_size, --learning_rate, --resume_from_checkpoint

##### collect_expert_traces.py
- ExpertTraceCollector class
- collect_traces(queries): Sends to GPT-4, captures analysis + routing
- save_trace(trace): Appends to expert_traces.jsonl
- format_for_training(traces): Converts to input/target pairs -> training_data.jsonl

##### run_step2_simple.py (root level)
- collect_trace(query): One query to GPT-4 API
- collect_batch(queries, batch_size=500): Concurrent batches of 20 using asyncio.gather()
- main(): Loads from data/legal_queries_1200_training.jsonl, saves to data/expert_traces/

---

#### Evaluation: evaluation/

| File | What it does |
|------|-------------|
| orchestration_metrics.py | OrchestrationEvaluator + OrchestrationMetrics. Computes RAS, WAI, routing accuracy, latency, cost. |
| batch_evaluation.py | Evaluates on 300-query dataset in batches of 50. Produces report. |
| run_orchestration_evaluation.py | Runs all 4 orchestrators on 16-query test set. |
| orchestration_test_dataset.py | Generates 16-query test dataset with ground truth |
| collect_gpt4_ground_truth_300.py | Collects GPT-4 routing for 300 eval queries |
| collect_gpt4_ground_truth_300_safe.py | Same with better error handling |

##### RAS (Routing Accuracy Score)
- Formula: |predicted_set INTERSECTION expected_set| / |predicted_set UNION expected_set|
- Set-based comparison: measures if the right agents were selected (ignoring order)

##### WAI (Workflow Appropriateness Index)
- Formula: 0.4 * agent_selection + 0.3 * order + 0.2 * dependency + 0.1 * (1 - efficiency_penalty)
- Composite metric for workflow quality

##### OrchestrationMetrics dataclass fields:
- routing_accuracy, sequence_accuracy, complexity_classification_accuracy
- ras, wai
- avg_decision_latency_ms, p50/p95/p99_latency_ms
- total_cost_usd, avg_cost_per_decision, cost_per_1000_decisions
- unnecessary_agent_calls, missed_necessary_agents, optimal_routing_rate
- error_rate, fallback_rate, total_decisions, orchestrator_name, requires_api

---

#### Data: data/

| File | What it does |
|------|-------------|
| extract_questions_from_indiclegalqa.py | Extracts 1,500 questions from IndicLegalQA. 1,200 training + 300 eval. |
| expert_traces/expert_traces.jsonl | Raw GPT-4 orchestration traces |
| expert_traces/training_data.jsonl | Formatted for Flan-T5 training {input, target} |
| legal_queries_1200_training.jsonl | 1,200 training queries |
| legal_queries_300_evaluation.json | 300 evaluation queries |
| legal_queries_300_evaluation_gpt4_ground_truth.json | 300 queries with GPT-4 routing |

#### Models: models/flan_t5_orchestrator/
- model.safetensors (~308MB, trained weights)
- config.json, tokenizer_config.json, spiece.model, special_tokens_map.json, generation_config.json, tokenizer.json

#### Tests: tests/
- test_booster.py, test_citation_verifier.py, test_indexing.py, test_retrieval.py

#### PowerShell Scripts:
- TRAIN_MODEL.ps1, RESUME_TRAINING.ps1, INSTALL_TRAINING_DEPS.ps1, COMMIT_AND_PUSH.ps1, PUSH_TO_GITHUB.ps1, COPY_MODEL.ps1

---

### Other Projects

#### projects/api_interfaces/ui/legal_ui.py - Streamlit UI (288 lines)
- initialize_system(): Creates SLMOrchestrationApp, calls initialize()
- main(): Sidebar (status, 8 sample queries), main area (query input, orchestration visualization, answer, citations, confidence)
- Run: streamlit run projects/api_interfaces/ui/legal_ui.py from repo root

#### projects/api_interfaces/api/main.py - FastAPI REST API
- Endpoints: /query (POST), /health (GET), /metrics (GET)

#### projects/indian_law_voicebot/ - Separate project (not PEARL)
- workingone.py: 35KB voice-based legal assistant

#### projects/database_builders/ - Database building
- scripts/build_indian_legal_database.py, consolidate_chromadb.py, indian_kanoon_api.py, indian_legal_database.py, add_docs_to_chromadb.py
- data_processing/document_processor.py, text_chunker.py, legal_parser.py, dataset_loader.py

#### projects/testing_evaluation/ - Testing
- evaluation/evaluation.py, tests/test_orchestration_queries.py, tests/run_tests.py, tests/test_agents.py, tests/test_orchestrator.py

### docs/ - Documentation

#### docs/guides/ (most useful)
- **SYSTEM_DESIGN_PEARL.md** (59KB) - Full 6-layer system design
- **RAS_WAI_METRICS_EXPLANATION.md** (12KB) - RAS/WAI formulas and interpretation
- **HOW_GPT_MAKES_ORCHESTRATION_DECISIONS.md** (18KB) - GPT-4 decision process
- **GPT_TRACE_COLLECTION_EXPLANATION.md** (8KB) - Trace collection
- **COLLECT_MORE_TRACES_AND_TRAIN.md** (11KB) - Trace collection + training guide
- **PROJECT_LOCATION_AND_FILES.md** (10KB) - File locations
- **PROJECT_OBJECTIVES.md** (6KB) - 3 objectives with targets
- SETUP.md, DEMO_QUERIES.md, HOD_PRESENTATION_GUIDE.md, PANEL_DEMONSTRATION_GUIDE.md, TRAINING_STOP_RESUME.md

#### docs/architecture/
- SLM_BASED_ARCHITECTURE.md, SLM_ORCHESTRATOR_REDESIGN.md, FULLY_SLM_BASED_DESIGN.md, ROUTING_FIXES.md

#### docs/reports/
- COMPREHENSIVE_PROJECT_REPORT.md (23KB), FINAL_SUMMARY.md, CLEAN_PROJECT_STRUCTURE.md

### utilities/
- data_loading/: data_loader.py, ingest.py, embed.py, preprocess.py, scraper.py
- database/: check_database.py, load_chroma.py, load_kaggle_data.py
- demos/: demo_bootstrap.py, demo_system.py, hod_demo.py

### config/
- config.py (root-level config), setup_scripts/setup.py, setup_api_keys.ps1

---

## Part 3: Capabilities Summary

| Capability | Command |
|-----------|---------|
| Ask via UI | streamlit run projects/api_interfaces/ui/legal_ui.py (from repo root) |
| Ask via CLI | python slm_orchestration_app.py --query 'What is Article 21?' |
| Run 5 demos | python slm_orchestration_app.py --demo |
| Interactive mode | python slm_orchestration_app.py --interactive |
| Switch orchestrator | python slm_orchestration_app.py --orchestrator gpt4 (or rule, none) |
| Collect GPT-4 traces | python run_step2_simple.py (needs OPENAI_API_KEY) |
| Train Flan-T5 | python training/knowledge_distillation.py --output_dir models/flan_t5_orchestrator |
| Resume training | add --resume_from_checkpoint models/flan_t5_orchestrator/checkpoint-200 |
| Evaluate (16 queries) | python evaluation/run_orchestration_evaluation.py |
| Batch evaluate (300) | python evaluation/batch_evaluation.py |
| REST API | uvicorn projects.api_interfaces.api.main:app |
| Run tests | python -m pytest projects/slm_orchestration_legal_rag/tests/ |

---

## Part 4: Files That Are NOT Important

- STEP2_COMPLETE.md, STEP3_COMPLETE.md, STEP4_COMPLETE.md - status tracking
- ORGANIZATION_COMPLETE.md, IMPORT_PATHS_FIXED.md - one-time records
- .ps1 scripts - convenience wrappers
- artifacts/ - old audit reports
- utilities/demos/ - one-time presentation demos
- projects/indian_law_voicebot/ - separate project, not PEARL

---

## Part 5: Current State and Known Issues

### Working:
- python slm_orchestration_app.py with base Flan-T5 (all 5 agents, 21,444 docs)
- All demo queries produce answers with citations
- Evaluation framework works (16-query and 300-query)
- Project pushed to GitHub clean-main branch

### Known Issues:
1. Streamlit UI path bug: legal_ui.py needs ('..','..','..') (3 levels up) not ('..','..') and needs the import re-added
2. Trained model overfitting: ~84% bias to 'retriever,answering,verifier'. Using base model. Fix: re-train with balanced data.

### On GitHub:
- Pushed: All source code, docs, config.example.py, requirements.txt, README
- NOT pushed: config.py (API keys), ChromaDB dirs, model weights, logs

---

## Part 6: End-to-End Data Flow

User Query -> SLMOrchestrationApp.process_query()
  Step 1: FlanT5Orchestrator.analyze_query() -> {complexity, reasoning_type, confidence}
  Step 2: FlanT5Orchestrator.route_to_agents() -> pattern selection -> WorkflowOptimizer -> agent sequence
  Step 3: _execute_agent_workflow():
    - BoosterAdapter -> enhanced query
    - RetrieverAdapter -> 5 docs from ChromaDB (21K docs)
    - AnsweringAdapter -> answer via Groq (llama-3.1-8b)
    - VerifierAdapter -> verification score
    - MultilingualAdapter -> language detection
  Step 4: Weighted confidence: 30% SLM + 45% answer quality + 25% doc support
  Returns: {answer, citations, confidence, orchestration metadata}

---

## Part 7: Training Pipeline Flow

Step 1: extract_questions_from_indiclegalqa.py -> 1,200 training + 300 eval queries
Step 2: run_step2_simple.py -> GPT-4 traces -> expert_traces.jsonl + training_data.jsonl
Step 3: knowledge_distillation.py -> Train Flan-T5 -> checkpoints at models/flan_t5_orchestrator/
Step 4: batch_evaluation.py / run_orchestration_evaluation.py -> RAS, WAI, comparison report

---

## Part 8: Performance Numbers

| Orchestrator | Params | Cost/Decision | Latency | Routing Accuracy | API |
|-------------|--------|--------------|---------|-----------------|-----|
| Flan-T5 (SLM) | 80M | free | ~15ms | 35.7% (base) / 85%+ (target) | No |
| GPT-4 | 1.7T | ~0.02 | ~500ms | 92.9% | Yes |
| Rule-Based | N/A | free | ~0ms | 28.6% | No |
| No Orchestration | N/A | free | N/A | 14.3% | No |

---

## Part 9: API Keys Required

| Key | Required For | How to Get |
|-----|-------------|-----------|
| GROQ_API_KEY | Answering agent | https://console.groq.com/ (free: 14,400 req/day) |
| OPENAI_API_KEY | Embeddings, GPT-4 traces, GPT-4 orchestrator | https://platform.openai.com/ |
| INDIAN_KANOON_API_KEY | Optional: legal doc updates | Contact Indian Kanoon |

Set in: projects/slm_orchestration_legal_rag/config.py (copy from config.example.py)

---

*Last updated: February 2026*
*GitHub: clean-main branch of Demo_repo*
