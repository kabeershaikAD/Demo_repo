# GPT-4 Expert Trace Collection: How and Where

## Overview

GPT-4 expert traces were collected to create training data for knowledge distillation. These traces capture how GPT-4 (the teacher model) makes orchestration decisions, which are then used to train Flan-T5-small (the student model).

---

## How Traces Were Collected

### Method 1: Using `run_step2_simple.py` (Simplified Approach)

**Location**: `projects/slm_orchestration_legal_rag/run_step2_simple.py`

**How it works**:
1. **Loads queries** from `data/query_booster_500.jsonl` (500 legal queries)
2. **Calls OpenAI GPT-4 API** directly with a prompt asking for orchestration decisions
3. **For each query**, GPT-4 analyzes and returns:
   - Complexity level (simple/moderate/complex)
   - Reasoning type (factual/analytical/comparative/procedural)
   - Whether query needs enhancement
   - Whether query needs verification
   - Optimal agent sequence (e.g., `["booster", "retriever", "answering"]`)
   - Confidence score
4. **Saves traces** to JSONL format

**Code Flow**:
```python
# For each query:
1. Send query to GPT-4 with orchestration prompt
2. GPT-4 analyzes query and returns JSON response
3. Parse response to extract:
   - Analysis (complexity, reasoning type, etc.)
   - Agent sequence
   - Confidence
4. Create trace object with metadata (cost, latency, timestamp)
5. Save to expert_traces.jsonl
```

**To run**:
```bash
cd projects/slm_orchestration_legal_rag
python run_step2_simple.py
```

### Method 2: Using `training/collect_expert_traces.py` (Full Orchestrator)

**Location**: `projects/slm_orchestration_legal_rag/training/collect_expert_traces.py`

**How it works**:
1. **Initializes GPT4Orchestrator** (full orchestrator class)
2. **Uses orchestrator methods**:
   - `analyze_query(query)` - Gets GPT-4's analysis
   - `route_to_agents(query, analysis)` - Gets agent sequence
3. **Collects traces** in batches with rate limiting
4. **Saves traces** in both raw and training formats

**To run**:
```bash
cd projects/slm_orchestration_legal_rag
python training/collect_expert_traces.py
```

---

## Where Traces Are Stored

### Primary Storage Locations

1. **Raw Expert Traces**: 
   - **Path**: `projects/slm_orchestration_legal_rag/data/expert_traces/expert_traces.jsonl`
   - **Format**: JSONL (one trace per line)
   - **Content**: Complete trace with query, analysis, agent sequence, workflow, and metadata

2. **Training Format Traces**:
   - **Path**: `projects/slm_orchestration_legal_rag/data/expert_traces/training_data.jsonl`
   - **Format**: JSONL formatted for Flan-T5 training
   - **Content**: Query-to-workflow pairs in sequence-to-sequence format

3. **Collection Statistics**:
   - **Path**: `projects/slm_orchestration_legal_rag/data/expert_traces/collection_stats.json`
   - **Content**: Collection metrics (total queries, success rate, cost, latency)

### Current Trace Data

**File**: `data/expert_traces/expert_traces.jsonl`
- **Total Traces**: 10 (test collection)
- **Status**: Sample traces collected for testing

**Sample Trace Structure**:
```json
{
  "query": "merger acquisition",
  "analysis": {
    "complexity": "simple",
    "reasoning_type": "factual",
    "requires_enhancement": true,
    "requires_verification": false,
    "confidence": 0.7
  },
  "agent_sequence": ["booster", "retriever", "answering"],
  "workflow": {
    "agents": ["booster", "retriever", "answering"],
    "estimated_steps": 3,
    "complexity": "simple",
    "reasoning_type": "factual"
  },
  "metadata": {
    "latency_ms": 4179.73,
    "cost_usd": 0.00729,
    "timestamp": 1764572025.95913,
    "teacher_model": "gpt-4",
    "trace_id": "trace_0_1764572025"
  }
}
```

---

## Query Sources

### Primary Source: `data/query_booster_500.jsonl`

**Location**: `projects/slm_orchestration_legal_rag/data/query_booster_500.jsonl`

**Content**: 500 legal queries covering:
- Constitutional law queries
- Criminal law queries
- Civil law queries
- Procedural queries
- Comparative queries

**Format**:
```json
{"query": "What is Article 21?", ...}
{"query": "What is Section 302 of IPC?", ...}
```

### Alternative Sources

If `query_booster_500.jsonl` is not available, the script uses **sample queries**:
- "What is Article 21?"
- "What is Section 302 of IPC?"
- "Compare Article 19 and Article 21"
- "How to file an FIR?"
- "Analyze the implications of Section 377"
- And 5 more sample queries

---

## Collection Process Details

### Step-by-Step Process

1. **Initialization**:
   - Load OpenAI API key from `config.py` or environment variable
   - Initialize GPT-4 client
   - Create output directory `data/expert_traces/`

2. **Query Loading**:
   - Read queries from `data/query_booster_500.jsonl`
   - Or use sample queries if file not found
   - Limit to 10 queries for testing (can be changed)

3. **Trace Collection** (for each query):
   - Send query to GPT-4 with orchestration prompt
   - Wait for response (average latency: ~3-5 seconds)
   - Parse JSON response
   - Extract analysis and agent sequence
   - Calculate cost (~$0.007 per query)
   - Create trace object
   - Add rate limiting (1 second delay between queries)

4. **Saving**:
   - Save raw traces to `expert_traces.jsonl`
   - Format for training and save to `training_data.jsonl`
   - Save statistics to `collection_stats.json`

### Cost and Performance

**Current Collection (10 traces)**:
- **Total Cost**: ~$0.07
- **Average Latency**: ~3,500ms per trace
- **Success Rate**: 100%

**Estimated for 1,000 traces**:
- **Total Cost**: ~$7.24
- **Estimated Time**: ~1 hour (with rate limiting)
- **Batch Size**: 2-5 queries processed in parallel

---

## How to Collect More Traces

### Option 1: Modify `run_step2_simple.py`

Edit line 304:
```python
# Change from:
test_queries = queries[:10]  # Limited to 10

# To:
test_queries = queries  # Use all 500 queries
```

Then run:
```bash
python run_step2_simple.py
```

### Option 2: Use Full Collection Script

```bash
python training/collect_expert_traces.py
```

This will:
- Process all queries from `data/query_booster_500.jsonl`
- Use batch processing (5 queries at a time)
- Save intermediate results every 100 traces
- Handle errors gracefully

---

## Trace Format for Training

### Input Format (for Flan-T5)

Each training example contains:

```json
{
  "input": "Query: What is Article 21?\n\nComplexity: simple\nReasoning Type: factual\nRequires Enhancement: false\nRequires Verification: false\n\nDetermine the optimal agent sequence:",
  "target": "retriever,answering",
  "query": "What is Article 21?",
  "agent_sequence": ["retriever", "answering"],
  "analysis": {
    "complexity": "simple",
    "reasoning_type": "factual",
    "requires_enhancement": false,
    "requires_verification": false,
    "confidence": 0.9
  },
  "metadata": {...}
}
```

**Training Process**:
- **Input**: Query + analysis → Flan-T5 model
- **Target**: Agent sequence (comma-separated)
- **Goal**: Train Flan-T5 to predict agent sequences given query analysis

---

## Summary

**How**: 
- Used OpenAI GPT-4 API to analyze legal queries
- Collected orchestration decisions (agent sequences) from GPT-4
- Saved as query-to-workflow pairs

**Where**:
- **Raw traces**: `data/expert_traces/expert_traces.jsonl`
- **Training data**: `data/expert_traces/training_data.jsonl`
- **Statistics**: `data/expert_traces/collection_stats.json`

**Current Status**:
- ✅ 10 traces collected (test run)
- ✅ Ready for training Flan-T5
- ⏳ Can collect 1,000+ traces for full dataset

**Next Steps**:
- Collect more traces (remove 10-query limit)
- Use traces to train Flan-T5 orchestrator
- Evaluate trained model with RAS/WAI metrics





