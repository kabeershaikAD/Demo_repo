# Comprehensive Cleanup Analysis

## Redundant Files Identified

### 1. README Files (Keep only README.md)
- README_COMPLETE.md (duplicate/outdated)
- README_SLM_ORCHESTRATION.md (duplicate/outdated)

### 2. Training Scripts (Old versions - keep only training/knowledge_distillation.py)
- final_train_booster.py
- fixed_train_booster.py
- simple_train_booster.py
- train_booster_slm.py
- train_500_queries_slm.py
- generate_500_training_data.py

### 3. Summary Files (Redundant - keep only essential)
- CLEANUP_SUMMARY.md
- FIXED_ERRORS_SUMMARY.md
- TRAINING_ERROR_SUMMARY.md
- TRANSFORMATION_SUMMARY.md
- SYSTEM_SUMMARY.md
- IMPLEMENTATION_SUMMARY.md

### 4. Quick Start Files (Consolidate - keep QUICK_START_GUIDE.md)
- QUICK_START_TRACE_COLLECTION.md (can merge into main guide)
- QUICK_START_TRAINING.md (can merge into main guide)

### 5. Step Complete Files (Keep for reference or consolidate)
- STEP2_COMPLETE.md
- STEP3_COMPLETE.md
- STEP4_COMPLETE.md

### 6. Old Data Files (Intermediate/old versions)
- data/ai_teacher_dataset.jsonl (old version)
- data/ai_teacher_dataset_fixed.jsonl (intermediate)
- data/query_booster.jsonl (old)
- data/query_booster_500.jsonl (old)
- data/training_format.jsonl (old format)
- data/sample_legal_data.json (sample/test)
- data/scraped_legal_data.json (old)
- data/processed_legal_data.json (intermediate)
- data/legal_embeddings.json (old)

### 7. Old Evaluation Scripts
- evaluation/collect_gpt4_ground_truth.py (old - replaced by _300 version)

### 8. Old Test Files (Keep organized tests/, remove root test_*.py)
- test_boosted_prompts.py
- test_booster.py
- test_comprehensive_system.py
- test_database.py
- test_ingestion_pipeline.py
- test_optimizer_integration.py
- test_orchestrator.py
- test_pipeline.py
- test_queries.py
- test_system.py
- test_workflow_optimizer.py

### 9. Old Setup/Utility Scripts
- add_article21_data.py
- add_sample_data.py
- bootstrap_dataset.py
- updater.py
- verify_step_completion.py
- ai_teacher_dataset_generator.py
- setup_nltk.py
- setup_slm_orchestration.py

### 10. Old App Files
- app.py (old - replaced by slm_orchestration_app.py)
- orchestrator.py (old - replaced by orchestrators/)

### 11. Old Documentation
- BOOTSTRAP_README.md
- INGESTION_PIPELINE_README.md
- KAGGLE_INTEGRATION_GUIDE.md
- FREE_DATA_APPROACH.md
- ARCHITECTURE_DOCUMENTATION.md (might keep)
- PROJECT_ABSTRACT.md (might keep)
- PROJECT_ANALYSIS_REPORT.md (might keep)
- SLM_ORCHESTRATOR_ABSTRACT.md (might keep)
- PEARL_PROJECT_ALIGNMENT.md (might keep)
- PEARL_IMPLEMENTATION_GUIDE.md (might keep)

### 12. PowerShell Scripts (Keep only essential)
- STOP_DUPLICATE_EVALUATIONS.ps1 (temporary)
- COPY_MODEL.ps1 (might keep)

### 13. Expert Traces Batch Files (Intermediate - final exists)
- data/expert_traces/expert_traces_batch_1.jsonl
- data/expert_traces/expert_traces_batch_2.jsonl
- data/expert_traces/expert_traces_batch_3.jsonl
- data/expert_traces/training_data_batch_1.jsonl
- data/expert_traces/training_data_batch_2.jsonl
- data/expert_traces/training_data_batch_3.jsonl


