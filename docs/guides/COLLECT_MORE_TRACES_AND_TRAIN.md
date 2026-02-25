# How to Collect More Traces and Train Your SLM

## Overview

This guide shows you how to:
1. **Collect more GPT-4 traces** (from 10 to 500+ traces)
2. **Train your Flan-T5 model** with the collected traces
3. **Improve your SLM orchestrator** performance

---

## Part 1: Collect More GPT-4 Traces

### Step 1: Modify the Collection Script

**File to edit**: `projects/slm_orchestration_legal_rag/run_step2_simple.py`

**Current setting** (line 304):
```python
# Limit to 10 for testing (remove limit for full collection)
test_queries = queries[:10] if len(queries) > 10 else queries
```

**Change to** (to collect all 500 queries):
```python
# Use all queries for full collection
test_queries = queries  # Remove the [:10] limit
```

**Or collect a specific number** (e.g., 100 traces):
```python
# Collect 100 traces
test_queries = queries[:100] if len(queries) > 100 else queries
```

### Step 2: Check Your OpenAI API Key

**Make sure your API key is configured:**

**Option A: In config.py**
```python
# In projects/slm_orchestration_legal_rag/config.py
OPENAI_API_KEY = "sk-your-actual-api-key-here"
```

**Option B: Environment Variable**
```bash
# Windows PowerShell
$env:OPENAI_API_KEY="sk-your-actual-api-key-here"

# Windows CMD
set OPENAI_API_KEY=sk-your-actual-api-key-here

# Linux/Mac
export OPENAI_API_KEY="sk-your-actual-api-key-here"
```

### Step 3: Run Trace Collection

**Navigate to project directory:**
```bash
cd "C:\Users\Lenovo\Downloads\Collage_Materials\Major project\projects\slm_orchestration_legal_rag"
```

**Run the collection script:**
```bash
python run_step2_simple.py
```

**What happens:**
- Script loads queries from `data/query_booster_500.jsonl`
- For each query, sends it to GPT-4 API
- GPT-4 analyzes and returns orchestration decision
- Saves trace to `data/expert_traces/expert_traces.jsonl`
- Formats for training and saves to `data/expert_traces/training_data.jsonl`

**Expected output:**
```
============================================================
STEP 2: Expert Trace Collection
============================================================

✅ Loaded 500 queries from data/query_booster_500.jsonl
📊 Collecting traces for 500 queries
✅ API key found: sk-proj-abc...
Processing query 1/500: What is Article 21?...
Processing query 2/500: What is Section 302 of IPC?...
...
============================================================
✅ Expert Trace Collection Complete!
============================================================
Total Queries: 500
Successful Traces: 498
Failed Traces: 2
Success Rate: 99.6%
Total Cost: $3.62
Average Latency: 3245.8ms
Traces Saved: 498
============================================================
```

### Step 4: Verify Collection

**Check the output files:**

1. **Raw traces**: `data/expert_traces/expert_traces.jsonl`
   - Should have one trace per line
   - Count lines: `wc -l data/expert_traces/expert_traces.jsonl` (Linux/Mac)
   - Or open in text editor and count

2. **Training data**: `data/expert_traces/training_data.jsonl`
   - Formatted for Flan-T5 training
   - Should have same number of lines as expert_traces.jsonl

3. **Statistics**: `data/expert_traces/collection_stats.json`
   - Contains collection metrics

### Cost and Time Estimates

| Number of Traces | Estimated Cost | Estimated Time |
|------------------|----------------|----------------|
| 10 traces | ~$0.07 | 2-3 minutes |
| 100 traces | ~$0.72 | 20-30 minutes |
| 500 traces | ~$3.60 | 2-3 hours |
| 1,000 traces | ~$7.20 | 4-5 hours |

**Note**: Cost is approximate based on GPT-4 pricing (~$0.007 per trace)

---

## Part 2: Train Your Flan-T5 Model

### Step 1: Verify Training Data Exists

**Check that training data file exists:**
```bash
# Navigate to project
cd projects/slm_orchestration_legal_rag

# Check if file exists
dir data\expert_traces\training_data.jsonl  # Windows
ls data/expert_traces/training_data.jsonl   # Linux/Mac
```

**Verify it has data:**
```bash
# Count lines (should match number of traces collected)
# Windows PowerShell
(Get-Content data\expert_traces\training_data.jsonl).Count

# Linux/Mac
wc -l data/expert_traces/training_data.jsonl
```

### Step 2: Install Training Dependencies

**Make sure you have PyTorch and Transformers:**
```bash
pip install torch transformers accelerate
```

**Or install all requirements:**
```bash
pip install -r requirements.txt
```

### Step 3: Run Training

**Basic training (recommended for first time):**
```bash
cd projects/slm_orchestration_legal_rag

python training/knowledge_distillation.py \
    --data data/expert_traces/training_data.jsonl \
    --output models/flan_t5_orchestrator \
    --epochs 3 \
    --batch_size 8 \
    --lr 5e-5
```

**Quick test training (1 epoch, faster):**
```bash
python training/knowledge_distillation.py \
    --data data/expert_traces/training_data.jsonl \
    --output models/flan_t5_orchestrator \
    --epochs 1 \
    --batch_size 4
```

**Full training (more epochs for better results):**
```bash
python training/knowledge_distillation.py \
    --data data/expert_traces/training_data.jsonl \
    --output models/flan_t5_orchestrator \
    --epochs 5 \
    --batch_size 8 \
    --lr 5e-5
```

### Step 4: Monitor Training

**What you'll see during training:**
```
Loading training data...
Loaded 498 training examples

Initializing Flan-T5-small model...
Model initialized on cuda (or cpu)

Starting training...
Epoch 1/3
  Training: 100%|████████████| 62/62 [05:23<00:00, loss=2.345]
  Validation: 100%|████████████| 16/16 [00:45<00:00, loss=1.892]

Epoch 2/3
  Training: 100%|████████████| 62/62 [05:18<00:00, loss=1.234]
  Validation: 100%|████████████| 16/16 [00:43<00:00, loss=0.987]

Epoch 3/3
  Training: 100%|████████████| 62/62 [05:21<00:00, loss=0.876]
  Validation: 100%|████████████| 16/16 [00:44<00:00, loss=0.654]

Saving model to models/flan_t5_orchestrator...
✅ Training complete!
```

### Step 5: Verify Trained Model

**Check that model files exist:**
```bash
# Windows
dir models\flan_t5_orchestrator

# Linux/Mac
ls models/flan_t5_orchestrator
```

**Should see:**
- `config.json` - Model configuration
- `pytorch_model.bin` or `model.safetensors` - Model weights
- `tokenizer_config.json` - Tokenizer configuration
- `vocab.json` - Vocabulary
- Other tokenizer files

---

## Part 3: Use Your Trained Model

### Update Orchestrator to Use Trained Model

**File**: `projects/slm_orchestration_legal_rag/orchestrators/flan_t5_orchestrator.py`

**Check the model path** (should point to your trained model):
```python
# Should be:
model_path = "models/flan_t5_orchestrator"
```

### Test Your Trained Model

**Run the orchestrator:**
```bash
python slm_orchestration_app.py
```

**Or test with a query:**
```python
from orchestrators.flan_t5_orchestrator import FlanT5Orchestrator

orchestrator = FlanT5Orchestrator(config)
await orchestrator.initialize()

query = "What is Article 21?"
analysis = await orchestrator.analyze_query(query)
sequence = await orchestrator.route_to_agents(query, analysis)

print(f"Agent sequence: {sequence}")
```

---

## Training Parameters Explained

### Epochs
- **1 epoch**: Quick test, may underfit
- **3 epochs**: Recommended starting point
- **5-10 epochs**: Better results, but may overfit with small datasets

### Batch Size
- **4**: Small batches, slower but more stable
- **8**: Recommended (good balance)
- **16**: Larger batches, faster but needs more memory

### Learning Rate
- **5e-5**: Recommended (standard for fine-tuning)
- **1e-4**: Higher learning rate, faster but less stable
- **1e-5**: Lower learning rate, slower but more stable

### Recommended Settings by Dataset Size

| Traces | Epochs | Batch Size | Learning Rate |
|--------|--------|------------|---------------|
| 10-50 | 5-10 | 4 | 5e-5 |
| 50-200 | 3-5 | 8 | 5e-5 |
| 200-500 | 3 | 8 | 5e-5 |
| 500+ | 3 | 8-16 | 5e-5 |

---

## Troubleshooting

### Issue: "OpenAI API key not found"
**Solution**: 
- Check `config.py` has your API key
- Or set environment variable: `export OPENAI_API_KEY="sk-..."`

### Issue: "Training data file not found"
**Solution**: 
- Make sure you ran trace collection first
- Check file exists: `data/expert_traces/training_data.jsonl`

### Issue: "Out of memory during training"
**Solution**:
- Reduce batch size: `--batch_size 4` or `--batch_size 2`
- Use CPU instead of GPU (slower but less memory)

### Issue: "Model not improving"
**Solution**:
- Collect more traces (500+ recommended)
- Increase epochs: `--epochs 5`
- Adjust learning rate: `--lr 1e-5` (lower) or `--lr 1e-4` (higher)

### Issue: "Collection is too slow"
**Solution**:
- This is normal - GPT-4 API has rate limits
- Each trace takes ~3-5 seconds
- For 500 traces, expect 2-3 hours
- Script has rate limiting to avoid API errors

---

## Expected Results

### With 10 Traces
- **RAS**: ~60-70%
- **WAI**: ~65-75%
- **Status**: Basic functionality, needs more data

### With 100 Traces
- **RAS**: ~75-85%
- **WAI**: ~80-88%
- **Status**: Good performance, can be improved

### With 500 Traces
- **RAS**: ~85-90%
- **WAI**: ~88-92%
- **Status**: Excellent performance, comparable to GPT-4

### With 1,000+ Traces
- **RAS**: ~87-93%
- **WAI**: ~90-93%
- **Status**: Near-GPT-4 performance

---

## Quick Command Reference

### Collect Traces
```bash
cd projects/slm_orchestration_legal_rag
python run_step2_simple.py
```

### Train Model
```bash
python training/knowledge_distillation.py \
    --data data/expert_traces/training_data.jsonl \
    --output models/flan_t5_orchestrator \
    --epochs 3 \
    --batch_size 8
```

### Check Progress
```bash
# Count traces collected
wc -l data/expert_traces/expert_traces.jsonl

# Check training data
wc -l data/expert_traces/training_data.jsonl

# Check model exists
ls models/flan_t5_orchestrator/
```

---

## Summary

1. **Edit** `run_step2_simple.py` line 304 to remove `[:10]` limit
2. **Run** `python run_step2_simple.py` to collect traces
3. **Wait** for collection to complete (2-3 hours for 500 traces)
4. **Train** with `python training/knowledge_distillation.py --data data/expert_traces/training_data.jsonl --output models/flan_t5_orchestrator --epochs 3`
5. **Test** your trained model with `python slm_orchestration_app.py`

**Good luck with your training!** 🚀



