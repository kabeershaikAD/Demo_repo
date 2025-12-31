# Batch Evaluation Guide - 300 Query Dataset

## Overview

The batch evaluation script processes 300 queries efficiently using:
- **Batch Processing**: 50 queries per batch (6 batches total)
- **Concurrent Execution**: Multiple queries processed in parallel within each batch
- **Cost Optimization**: Reduces API call overhead and improves efficiency
- **Comprehensive Reporting**: Generates detailed evaluation report

---

## Features

### ✅ Batch Processing
- Processes queries in batches of 50
- Reduces API rate limit issues
- Better error handling and recovery
- Progress tracking per batch

### ✅ Concurrent Execution
- Uses `asyncio.gather()` for parallel processing
- Both GPT-4 and trained model benefit from concurrent calls
- Significantly faster than sequential processing

### ✅ Cost Optimization
- Batched API calls reduce overhead
- Better rate limit management
- Progress updates to monitor costs

### ✅ Comprehensive Metrics
- **RAS** (Routing Accuracy Score)
- **WAI** (Workflow Appropriateness Index)
- Latency metrics (avg, P50, P95, P99)
- Cost tracking
- Error rates

---

## Usage

### Run Batch Evaluation

```powershell
cd "C:\Users\Lenovo\Downloads\Collage_Materials\Major project\projects\slm_orchestration_legal_rag"
.\legal_rag_env\Scripts\Activate.ps1
python evaluation/batch_evaluation.py
```

---

## What It Does

1. **Loads 300-query dataset** from `data/legal_queries_300_evaluation.json`

2. **Initializes orchestrators**:
   - FlanT5 (your trained model)
   - RuleBased (baseline)
   - NoOrchestration (baseline)
   - GPT4 (if API key available)

3. **Processes in batches**:
   - 50 queries per batch
   - 6 batches total (300 queries)
   - Concurrent processing within each batch

4. **Calculates metrics**:
   - Routing accuracy
   - RAS and WAI (PEARL metrics)
   - Latency statistics
   - Cost analysis

5. **Generates report**:
   - `evaluation/batch_evaluation_report.md`
   - Comprehensive comparison tables
   - Detailed analysis for each orchestrator

---

## Expected Output

### Console Output
```
============================================================
Batch Evaluation - 300 Query Dataset
============================================================

[INFO] Loading dataset: data/legal_queries_300_evaluation.json
[OK] Loaded 300 test cases

[INFO] Initializing orchestrators...
  [OK] Flan-T5 initialized
  [OK] Orchestrators ready

============================================================
Evaluating FlanT5
============================================================
Total queries: 300
Batch size: 50
Total batches: 6
  Processing batch 1/6 (50 queries)...
  Completed: 50/300 queries
  Processing batch 2/6 (50 queries)...
  ...
```

### Report File
- **Location**: `evaluation/batch_evaluation_report.md`
- **Contents**:
  - Executive summary
  - Comparison table
  - Detailed metrics for each orchestrator
  - Dataset information
  - Methodology

---

## Performance

### Expected Time
- **FlanT5**: ~10-15 minutes (300 queries, local model)
- **RuleBased**: ~1-2 minutes (rule-based, very fast)
- **NoOrchestration**: ~1-2 minutes (no processing)
- **GPT4**: ~30-45 minutes (300 queries × 2 API calls each, with rate limits)

### Expected Costs (GPT-4)
- **Per query**: ~$0.008 (2 API calls: analysis + routing)
- **Total**: ~$2.40 for 300 queries
- **With batching**: Slightly lower due to reduced overhead

---

## Batch Processing Details

### How Batching Works

1. **Split queries into batches**:
   ```python
   batch_size = 50
   batches = [queries[i:i+batch_size] for i in range(0, len(queries), batch_size)]
   ```

2. **Process each batch concurrently**:
   ```python
   tasks = [process_query(query) for query in batch]
   results = await asyncio.gather(*tasks)
   ```

3. **Collect results**:
   - All batch results combined
   - Metrics calculated from complete dataset

### Benefits

- **Reduced API overhead**: Fewer connection setups
- **Better error handling**: Errors isolated to batches
- **Progress tracking**: See progress every 50 queries
- **Rate limit management**: Can add delays between batches

---

## Output Files

### 1. Evaluation Report
- **File**: `evaluation/batch_evaluation_report.md`
- **Format**: Markdown
- **Contents**: Full evaluation results and analysis

### 2. Console Output
- Real-time progress updates
- Batch completion status
- Summary metrics

---

## Troubleshooting

### Issue: Rate Limit Errors
**Solution**: The script includes 1-second delays between batches. If you still hit rate limits, increase the delay in the script.

### Issue: Out of Memory
**Solution**: Reduce batch size from 50 to 25 or 10 in the script.

### Issue: GPT-4 API Errors
**Solution**: Check your API key and quota. The script will skip GPT-4 if unavailable.

### Issue: Slow Processing
**Solution**: This is normal for 300 queries. GPT-4 evaluation takes 30-45 minutes. FlanT5 is much faster (10-15 minutes).

---

## Comparison with Sequential Evaluation

| Method | Time (300 queries) | API Efficiency | Error Recovery |
|--------|-------------------|----------------|----------------|
| **Sequential** | ~60-90 min | Low | Poor |
| **Batch (50)** | ~30-45 min | High | Good |
| **Concurrent** | ~20-30 min | Very High | Excellent |

---

## Next Steps

After evaluation completes:

1. **Review Report**: Check `evaluation/batch_evaluation_report.md`
2. **Analyze Metrics**: Compare RAS/WAI across orchestrators
3. **Cost Analysis**: Review total costs vs. accuracy trade-offs
4. **Document Findings**: Add results to project documentation

---

## Summary

The batch evaluation script provides:
- ✅ Efficient processing of 300 queries
- ✅ Cost-optimized API usage
- ✅ Comprehensive metrics (RAS, WAI)
- ✅ Detailed evaluation report
- ✅ Progress tracking and error handling

**Ready to run!** The script is currently executing in the background.

