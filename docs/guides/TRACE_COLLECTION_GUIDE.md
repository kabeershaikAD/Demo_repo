# GPT-4 Trace Collection Guide - 1,200 Queries

## ✅ Script Updated!

The trace collection script has been updated to use the new **1,200 realistic legal queries** dataset.

---

## 📋 Prerequisites

1. **OpenAI API Key**: Set your API key
   ```bash
   # Option 1: Environment variable
   export OPENAI_API_KEY="your-api-key-here"
   
   # Option 2: Windows PowerShell
   $env:OPENAI_API_KEY="your-api-key-here"
   
   # Option 3: Add to config.py
   # OPENAI_API_KEY = "your-api-key-here"
   ```

2. **Dataset File**: Verify the training dataset exists
   ```bash
   # Should exist at:
   projects/slm_orchestration_legal_rag/data/legal_queries_1200_training.jsonl
   ```

3. **Dependencies**: Install required packages
   ```bash
   pip install openai asyncio
   ```

---

## 🚀 Running Trace Collection

### Step 1: Navigate to Project Directory

```bash
cd "C:\Users\Lenovo\Downloads\Collage_Materials\Major project\projects\slm_orchestration_legal_rag"
```

### Step 2: Run Trace Collection

```bash
python run_step2_simple.py
```

### What Happens:

1. **Loads 1,200 queries** from `data/legal_queries_1200_training.jsonl`
2. **Collects GPT-4 traces** for each query:
   - Query analysis (complexity, reasoning type)
   - Agent routing decisions
   - Workflow sequences
3. **Saves intermediate results** every 100 traces (safety feature)
4. **Saves final results** to:
   - `data/expert_traces/expert_traces.jsonl` (raw traces)
   - `data/expert_traces/training_data.jsonl` (formatted for training)
   - `data/expert_traces/collection_stats.json` (statistics)

---

## ⏱️ Expected Timeline

| Stage | Time | Details |
|-------|------|---------|
| **Setup** | 1-2 min | Loading queries, initializing API |
| **Collection** | 4-5 hours | 1,200 queries × ~12-15 seconds each |
| **Saving** | 1-2 min | Writing traces to files |
| **Total** | **4-5 hours** | Complete trace collection |

### Rate Limiting

- **Batch Size**: 2 queries at a time (to avoid API rate limits)
- **Delay**: 1 second between batches
- **Intermediate Saves**: Every 100 traces (safety checkpoint)

---

## 💰 Expected Costs

| Item | Cost | Details |
|------|------|---------|
| **Per Trace** | ~$0.007 | GPT-4 API call (analysis + routing) |
| **Total (1,200)** | **~$8.40** | Complete collection |
| **With Buffer** | **~$9.00** | Including retries/errors |

**Note**: Actual cost may vary based on:
- Query complexity (longer queries = more tokens)
- API rate limits (may need retries)
- Network latency

---

## 📊 Progress Monitoring

The script will display:
- ✅ Query count loaded
- ✅ API key status
- 📊 Progress updates (every batch)
- 💾 Intermediate saves (every 100 traces)
- 📈 Final statistics

### Sample Output:

```
============================================================
Expert Trace Collection - PEARL Framework
============================================================

✅ Loaded 1200 queries from data/legal_queries_1200_training.jsonl
📊 Collecting traces for 1200 queries
   Expected time: 4-5 hours
   Expected cost: ~$8.40 (at ~$0.007 per trace)

✅ API key found: sk-proj-abc...

[INFO] Collecting batch 1/600 (queries 0-2)...
[INFO] Collected 2 traces (2 successful, 0 failed)
[INFO] Progress: 2/1200 (0.2%)
...

[INFO] Saved intermediate traces: 100 traces collected
[INFO] Progress: 100/1200 (8.3%)
...

============================================================
✅ Expert Trace Collection Complete!
============================================================
Total Queries: 1200
Successful Traces: 1198
Failed Traces: 2
Success Rate: 99.8%
Total Cost: $8.3860
Average Latency: 12,450.5ms
Traces Saved: 1198
============================================================
```

---

## 🛡️ Safety Features

### 1. Intermediate Saves
- Saves progress every 100 traces
- Prevents data loss if script crashes
- Files: `intermediate_100.jsonl`, `intermediate_200.jsonl`, etc.

### 2. Error Handling
- Continues on individual query failures
- Logs errors for debugging
- Reports success rate at end

### 3. Rate Limiting
- Batch size: 2 (safe for API limits)
- Delay: 1 second between batches
- Prevents API throttling

---

## 🔧 Troubleshooting

### Issue: "OpenAI API key not found"
**Solution**: Set `OPENAI_API_KEY` environment variable or add to `config.py`

### Issue: "Rate limit exceeded"
**Solution**: 
- Wait 1 minute and retry
- Reduce batch_size in script (line 331): `batch_size=1`
- Add longer delay: `await asyncio.sleep(2)`

### Issue: "Connection timeout"
**Solution**:
- Check internet connection
- Retry the script (it will skip already collected traces)
- Script continues from where it left off

### Issue: "Out of memory"
**Solution**:
- Script saves intermediate results automatically
- Restart script - it will continue from last checkpoint
- Or process in smaller chunks (modify script to process 500 at a time)

---

## 📁 Output Files

After completion, you'll have:

### 1. `data/expert_traces/expert_traces.jsonl`
**Raw traces** from GPT-4 (full metadata)
```json
{
  "query": "What were the charges against P Ramesh in this case?",
  "analysis": {"complexity": "simple", "reasoning_type": "factual"},
  "agent_sequence": ["retriever", "answering"],
  "metadata": {"latency_ms": 12345, "timestamp": "2024-..."}
}
```

### 2. `data/expert_traces/training_data.jsonl`
**Formatted for training** (query-to-workflow pairs)
```json
{
  "input": "Query: What were the charges...\nAnalysis: {...}",
  "target": "retriever,answering"
}
```

### 3. `data/expert_traces/collection_stats.json`
**Statistics** about collection
```json
{
  "total_queries": 1200,
  "successful_traces": 1198,
  "failed_traces": 2,
  "success_rate": 0.998,
  "total_cost": 8.3860,
  "avg_latency_ms": 12450.5
}
```

---

## ✅ Next Steps After Collection

Once trace collection completes:

### Step 1: Verify Results
```bash
# Check trace count
python -c "import json; f=open('data/expert_traces/expert_traces.jsonl','r'); print(f'Traces: {sum(1 for _ in f)}')"

# Check statistics
cat data/expert_traces/collection_stats.json
```

### Step 2: Train Flan-T5 Model
```bash
python training/knowledge_distillation.py \
    --data data/expert_traces/training_data.jsonl \
    --output models/flan_t5_orchestrator \
    --epochs 3 \
    --batch_size 8 \
    --lr 5e-5
```

**Expected Results**:
- **RAS**: 70-85% (vs. 35.7% with 10 traces)
- **WAI**: 90-93% (vs. 88.6% with 10 traces)
- **Training Time**: 30-45 minutes

### Step 3: Evaluate Model
```bash
python evaluation/run_orchestration_evaluation.py
```

---

## 🎯 Success Criteria

✅ **Collection Complete** when:
- Success rate > 95%
- Total traces ≥ 1,150 (allowing for ~50 failures)
- All output files created
- Statistics file shows reasonable cost/latency

✅ **Ready for Training** when:
- `training_data.jsonl` has ≥ 1,150 entries
- File size > 500 KB (indicates substantial data)
- No major errors in logs

---

## 📝 Notes

- **Long Running**: This will take 4-5 hours. Run in background or use `screen`/`tmux`
- **Cost**: ~$8-9 for 1,200 traces (one-time cost)
- **Resumable**: Script can be stopped and restarted (saves progress)
- **Quality**: Realistic queries from actual legal cases = better training data

---

**Ready to start? Run: `python run_step2_simple.py`** 🚀



