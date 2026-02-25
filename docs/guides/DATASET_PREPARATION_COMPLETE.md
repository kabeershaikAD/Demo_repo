# ✅ Dataset Preparation Complete: 1500 Realistic Legal Queries

## 🎉 Success!

Successfully extracted **1,500 realistic legal questions** from the IndicLegalQA Dataset and split them into training and evaluation sets.

---

## 📊 Dataset Summary

| Dataset | Count | File | Purpose |
|---------|-------|------|---------|
| **Training** | 1,200 queries | `legal_queries_1200_training.jsonl` | For GPT-4 trace collection |
| **Evaluation** | 300 queries | `legal_queries_300_evaluation.json` | For testing and evaluation |
| **Total** | 1,500 queries | - | Complete dataset |

### Statistics

- **Total Unique Questions**: 9,701 (from IndicLegalQA Dataset)
- **Selected**: 1,500 (1,200 training + 300 evaluation)
- **Average Query Length**: ~16 words (realistic human queries)
- **Source**: Real legal case questions from Indian legal judgments

---

## 📁 Generated Files

### 1. Training Dataset
**File**: `projects/slm_orchestration_legal_rag/data/legal_queries_1200_training.jsonl`

**Format**: JSONL (one query per line)
```json
{"query": "What were the charges against P Ramesh in this case?"}
{"query": "What interim order was passed by the High Court that led to the appeal?"}
{"query": "What might happen if new evidence emerges in the future regarding the involvement of the accused?"}
```

**Usage**: For collecting GPT-4 expert traces

### 2. Evaluation Dataset
**File**: `projects/slm_orchestration_legal_rag/data/legal_queries_300_evaluation.json`

**Format**: JSON array with metadata
```json
[
  {
    "id": 1,
    "query": "Did the Supreme Court find merit in the allegations made by Ramesh Sanka?",
    "complexity": "moderate",
    "reasoning_type": "factual",
    "expected_agents": ["booster", "retriever", "answering"],
    "reasoning": "Auto-classified: factual query with moderate complexity",
    "category": "moderate_factual"
  }
]
```

**Usage**: For testing orchestrator performance

### 3. Statistics File
**File**: `projects/slm_orchestration_legal_rag/data/dataset_statistics.json`

Contains dataset statistics and metadata.

---

## 🚀 How to Use These Datasets

### Step 1: Update Trace Collection Script

**File**: `projects/slm_orchestration_legal_rag/run_step2_simple.py`

**Change line 281** from:
```python
queries_file = Path("data/query_booster_500.jsonl")
```

**To**:
```python
queries_file = Path("data/legal_queries_1200_training.jsonl")
```

**Change line 304** from:
```python
test_queries = queries[:10]  # Limited to 10
```

**To**:
```python
test_queries = queries  # Use all 1200 queries
```

### Step 2: Collect GPT-4 Traces

```bash
cd projects/slm_orchestration_legal_rag
python run_step2_simple.py
```

**Expected**:
- **Time**: 4-5 hours (for 1,200 queries)
- **Cost**: ~$8.64 (at ~$0.007 per trace)
- **Output**: `data/expert_traces/expert_traces.jsonl` with 1,200 traces

### Step 3: Train Flan-T5 Model

After trace collection completes:

```bash
python training/knowledge_distillation.py \
    --data data/expert_traces/training_data.jsonl \
    --output models/flan_t5_orchestrator \
    --epochs 3 \
    --batch_size 8 \
    --lr 5e-5
```

**Expected**:
- **Time**: 30-45 minutes
- **Performance**: 70-85% RAS (vs. 35.7% with 10 traces)

### Step 4: Evaluate with Test Dataset

```bash
# Update evaluation script to use new test dataset
# File: evaluation/orchestration_test_dataset.json
# Replace with: legal_queries_300_evaluation.json

python evaluation/run_orchestration_evaluation.py
```

---

## 📋 Sample Queries (Realistic Examples)

### Training Queries (Sample)
- "What were the charges against P Ramesh in this case?"
- "What interim order was passed by the High Court that led to the appeal?"
- "What might happen if new evidence emerges in the future regarding the involvement of the accused?"
- "What defense did Rakesh Tiwari present in response to the contempt charges?"
- "What environmental violations were Sterlite Industries accused of?"

### Evaluation Queries (Sample)
- "Did the Supreme Court find merit in the allegations made by Ramesh Sanka?"
- "What was the primary issue in the case of Hemant Kumar Verma & Ors. vs Employees State Insurance Corporation & Ors.?"
- "How did the Supreme Court interpret Section 3 of the Sports Broadcasting Signals Act?"

---

## ✅ Quality of Queries

### Why These Queries Are Realistic:

1. **Real Legal Cases**: Extracted from actual Indian legal judgments
2. **Natural Language**: Questions people actually ask about legal cases
3. **Diverse Complexity**: Mix of simple, moderate, and complex queries
4. **Various Reasoning Types**: Factual, analytical, comparative, procedural
5. **Contextual**: Questions reference specific cases, parties, and legal issues
6. **Not Generic**: Not just "What is Article 21?" but "What was the main issue in the case..."

### Query Characteristics:

- **Average Length**: ~16 words (natural human queries)
- **Domain Coverage**: 
  - Constitutional law
  - Criminal law
  - Civil law
  - Family law
  - Property law
  - Labor law
  - Consumer law
  - Administrative law

---

## 🔄 Next Steps

1. ✅ **Dataset Created** - 1,500 queries extracted
2. ⏳ **Update Collection Script** - Point to new training file
3. ⏳ **Collect Traces** - Run trace collection (4-5 hours)
4. ⏳ **Train Model** - Train Flan-T5 with 1,200 traces
5. ⏳ **Evaluate** - Test with 300 evaluation queries

---

## 📝 File Locations

All files are in: `projects/slm_orchestration_legal_rag/data/`

- ✅ `legal_queries_1200_training.jsonl` - Training queries
- ✅ `legal_queries_300_evaluation.json` - Evaluation queries
- ✅ `dataset_statistics.json` - Statistics
- ✅ `extract_questions_from_indiclegalqa.py` - Extraction script

---

## 🎯 Expected Results After Training

With 1,200 training traces (vs. current 10):

| Metric | Current (10 traces) | Expected (1,200 traces) |
|--------|---------------------|------------------------|
| **RAS** | 35.7% | 70-85% |
| **WAI** | 88.6% | 90-93% |
| **Routing Accuracy** | 35.7% | 75-85% |
| **Sequence Accuracy** | 35.7% | 70-80% |

---

**Dataset is ready! Now update the trace collection script and start collecting!** 🚀



