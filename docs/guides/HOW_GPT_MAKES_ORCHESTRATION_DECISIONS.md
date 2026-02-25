# How GPT-4 Makes Orchestration Decisions: Detailed Explanation

## Overview

This document explains the **exact mechanism** of how GPT-4 analyzes queries and makes orchestration decisions, and how those decisions are captured as traces for training.

---

## The Two-Step Decision Process

GPT-4 makes orchestration decisions in **two steps**:

1. **Step 1: Query Analysis** - GPT-4 analyzes the query to understand its complexity and requirements
2. **Step 2: Agent Routing** - GPT-4 decides which agents to call and in what order

---

## Step 1: Query Analysis (`analyze_query`)

### What Happens

When you call `analyze_query(query)`, the code sends a **prompt** to GPT-4 asking it to analyze the query.

### The Actual Prompt Sent to GPT-4

```python
prompt = f"""
Analyze this legal query and classify its complexity for multi-agent processing.

Query: "{query}"

Determine:
1. Complexity level (simple/moderate/complex)
2. Required reasoning type (factual/analytical/comparative/procedural)
3. Estimated processing steps needed
4. Whether query enhancement is needed
5. Whether verification is needed

Respond in JSON format:
{{
    "complexity": "simple|moderate|complex",
    "reasoning_type": "factual|analytical|comparative|procedural",
    "estimated_steps": 1-5,
    "requires_enhancement": true|false,
    "requires_verification": true|false,
    "confidence": 0.0-1.0
}}
"""
```

### Example: Real Query

**Input Query**: `"What is Article 21?"`

**GPT-4 receives**:
```
Analyze this legal query and classify its complexity for multi-agent processing.

Query: "What is Article 21?"

Determine:
1. Complexity level (simple/moderate/complex)
2. Required reasoning type (factual/analytical/comparative/procedural)
3. Estimated processing steps needed
4. Whether query enhancement is needed
5. Whether verification is needed

Respond in JSON format:
{
    "complexity": "simple|moderate|complex",
    "reasoning_type": "factual|analytical|comparative|procedural",
    "estimated_steps": 1-5,
    "requires_enhancement": true|false,
    "requires_verification": true|false,
    "confidence": 0.0-1.0
}
```

### GPT-4's Response

GPT-4 analyzes the query and returns JSON like this:

```json
{
    "complexity": "simple",
    "reasoning_type": "factual",
    "estimated_steps": 2,
    "requires_enhancement": false,
    "requires_verification": false,
    "confidence": 0.9
}
```

**GPT-4's Reasoning** (what it thinks):
- "This is a simple factual query asking about a specific article"
- "No enhancement needed - query is clear"
- "No verification needed - straightforward retrieval"
- "High confidence (0.9) - straightforward question"

### Code That Captures This

```python
# In gpt4_orchestrator.py, analyze_query method:

response = self.client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are an expert query analyzer for multi-agent legal systems."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.1,  # Low temperature for consistent results
    max_tokens=200
)

# Parse GPT-4's JSON response
analysis = json.loads(response.choices[0].message.content)

# Returns:
# {
#     "complexity": "simple",
#     "reasoning_type": "factual",
#     "requires_enhancement": false,
#     "requires_verification": false,
#     "confidence": 0.9
# }
```

---

## Step 2: Agent Routing (`route_to_agents`)

### What Happens

After getting the analysis, the code asks GPT-4 to decide **which agents to call** and **in what order**.

### The Actual Prompt Sent to GPT-4

```python
prompt = f"""
Based on this query analysis, determine the optimal sequence of agents.

Query: "{query}"
Analysis: {json.dumps(analysis)}

Available agents:
- booster: Improves vague queries with legal terminology
- retriever: Searches document database
- answering: Creates comprehensive answers
- verifier: Validates citations and facts
- multilingual: Handles language detection and translation
- updater: Checks for recent updates

Routing rules:
- Simple factual queries: retriever → answering
- Complex analytical queries: booster → retriever → answering → verifier
- Comparative queries: booster → retriever → answering → verifier
- Multilingual queries: multilingual → booster → retriever → answering
- Procedural queries: booster → retriever → answering

Respond with JSON array of agent names in execution order:
["agent1", "agent2", "agent3"]
"""
```

### Example: With Previous Analysis

**Input**:
- Query: `"What is Article 21?"`
- Analysis: `{"complexity": "simple", "reasoning_type": "factual", ...}`

**GPT-4 receives**:
```
Based on this query analysis, determine the optimal sequence of agents.

Query: "What is Article 21?"
Analysis: {"complexity": "simple", "reasoning_type": "factual", "requires_enhancement": false, "requires_verification": false, "confidence": 0.9}

Available agents:
- booster: Improves vague queries with legal terminology
- retriever: Searches document database
- answering: Creates comprehensive answers
- verifier: Validates citations and facts
- multilingual: Handles language detection and translation
- updater: Checks for recent updates

Routing rules:
- Simple factual queries: retriever → answering
- Complex analytical queries: booster → retriever → answering → verifier
- Comparative queries: booster → retriever → answering → verifier
- Multilingual queries: multilingual → booster → retriever → answering
- Procedural queries: booster → retriever → answering

Respond with JSON array of agent names in execution order:
["agent1", "agent2", "agent3"]
```

### GPT-4's Response

GPT-4 decides on the agent sequence:

```json
["retriever", "answering"]
```

**GPT-4's Reasoning** (what it thinks):
- "This is a simple factual query"
- "Query is clear, no enhancement needed (skip booster)"
- "Just need to retrieve documents and answer (retriever → answering)"
- "No verification needed for simple factual query (skip verifier)"

### Code That Captures This

```python
# In gpt4_orchestrator.py, route_to_agents method:

response = self.client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are an expert agent router for legal AI systems."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.1,
    max_tokens=100
)

# Parse GPT-4's JSON response
agent_sequence = json.loads(response.choices[0].message.content)

# Returns: ["retriever", "answering"]
```

---

## How the Trace is Created

### Complete Flow

```python
# In collect_expert_traces.py, collect_trace method:

# Step 1: Get analysis from GPT-4
analysis = await self.teacher_orchestrator.analyze_query(query)
# Returns: {"complexity": "simple", "reasoning_type": "factual", ...}

# Step 2: Get agent sequence from GPT-4
agent_sequence = await self.teacher_orchestrator.route_to_agents(query, analysis)
# Returns: ["retriever", "answering"]

# Step 3: Create trace object
trace = {
    "query": query,  # "What is Article 21?"
    "analysis": {
        "complexity": analysis.get("complexity"),  # "simple"
        "reasoning_type": analysis.get("reasoning_type"),  # "factual"
        "requires_enhancement": analysis.get("requires_enhancement"),  # false
        "requires_verification": analysis.get("requires_verification"),  # false
        "confidence": analysis.get("confidence", 0.0)  # 0.9
    },
    "agent_sequence": agent_sequence,  # ["retriever", "answering"]
    "workflow": {
        "agents": agent_sequence,
        "estimated_steps": len(agent_sequence),  # 2
        "complexity": analysis.get("complexity"),
        "reasoning_type": analysis.get("reasoning_type")
    },
    "metadata": {
        "latency_ms": latency_ms,  # ~3000ms
        "cost_usd": cost,  # ~$0.007
        "timestamp": time.time(),
        "teacher_model": "gpt-4",
        "trace_id": "trace_0_1764572025"
    }
}
```

### Final Trace Saved

```json
{
  "query": "What is Article 21?",
  "analysis": {
    "complexity": "simple",
    "reasoning_type": "factual",
    "requires_enhancement": false,
    "requires_verification": false,
    "confidence": 0.9
  },
  "agent_sequence": ["retriever", "answering"],
  "workflow": {
    "agents": ["retriever", "answering"],
    "estimated_steps": 2,
    "complexity": "simple",
    "reasoning_type": "factual"
  },
  "metadata": {
    "latency_ms": 3078.74,
    "cost_usd": 0.00714,
    "timestamp": 1764572039.7617636,
    "teacher_model": "gpt-4",
    "trace_id": "trace_3_1764572039"
  }
}
```

---

## Visual Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    TRACE COLLECTION FLOW                        │
└─────────────────────────────────────────────────────────────────┘

User Query: "What is Article 21?"
        │
        ▼
┌───────────────────────────────────────────────────────────────┐
│  Step 1: Query Analysis                                       │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Send to GPT-4:                                         │  │
│  │  "Analyze this legal query..."                          │  │
│  │  + Query: "What is Article 21?"                         │  │
│  └───────────────────────┬─────────────────────────────────┘  │
│                          │                                      │
│                          ▼                                      │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  GPT-4 Response (JSON):                                 │  │
│  │  {                                                       │  │
│  │    "complexity": "simple",                              │  │
│  │    "reasoning_type": "factual",                         │  │
│  │    "requires_enhancement": false,                        │  │
│  │    "requires_verification": false,                      │  │
│  │    "confidence": 0.9                                    │  │
│  │  }                                                       │  │
│  └───────────────────────┬─────────────────────────────────┘  │
└──────────────────────────┼────────────────────────────────────┘
                           │
                           ▼
┌───────────────────────────────────────────────────────────────┐
│  Step 2: Agent Routing                                        │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Send to GPT-4:                                         │  │
│  │  "Based on this query analysis..."                      │  │
│  │  + Query: "What is Article 21?"                         │  │
│  │  + Analysis: {complexity: "simple", ...}                │  │
│  │  + Available agents list                                │  │
│  │  + Routing rules                                        │  │
│  └───────────────────────┬─────────────────────────────────┘  │
│                          │                                      │
│                          ▼                                      │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  GPT-4 Response (JSON):                                 │  │
│  │  ["retriever", "answering"]                             │  │
│  └───────────────────────┬─────────────────────────────────┘  │
└──────────────────────────┼────────────────────────────────────┘
                           │
                           ▼
┌───────────────────────────────────────────────────────────────┐
│  Step 3: Create Trace                                         │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Combine:                                                │  │
│  │  • Query                                                 │  │
│  │  • Analysis (from Step 1)                               │  │
│  │  • Agent Sequence (from Step 2)                          │  │
│  │  • Metadata (cost, latency, timestamp)                   │  │
│  └───────────────────────┬─────────────────────────────────┘  │
│                          │                                      │
│                          ▼                                      │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Save to: expert_traces.jsonl                          │  │
│  │  (One trace per line in JSON format)                    │  │
│  └─────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

---

## Real Example: Complex Query

### Query: `"Compare Article 19 and Article 21"`

**Step 1 - Analysis Prompt**:
```
Analyze this legal query and classify its complexity for multi-agent processing.

Query: "Compare Article 19 and Article 21"
...
```

**Step 1 - GPT-4 Response**:
```json
{
    "complexity": "moderate",
    "reasoning_type": "comparative",
    "estimated_steps": 4,
    "requires_enhancement": true,
    "requires_verification": true,
    "confidence": 0.85
}
```

**Step 2 - Routing Prompt**:
```
Based on this query analysis, determine the optimal sequence of agents.

Query: "Compare Article 19 and Article 21"
Analysis: {"complexity": "moderate", "reasoning_type": "comparative", ...}
...
```

**Step 2 - GPT-4 Response**:
```json
["booster", "retriever", "answering", "verifier"]
```

**Final Trace**:
```json
{
  "query": "Compare Article 19 and Article 21",
  "analysis": {
    "complexity": "moderate",
    "reasoning_type": "comparative",
    "requires_enhancement": true,
    "requires_verification": true,
    "confidence": 0.85
  },
  "agent_sequence": ["booster", "retriever", "answering", "verifier"],
  "workflow": {
    "agents": ["booster", "retriever", "answering", "verifier"],
    "estimated_steps": 4,
    "complexity": "moderate",
    "reasoning_type": "comparative"
  },
  "metadata": {...}
}
```

---

## Key Points

1. **GPT-4 makes decisions through prompts**: We send structured prompts asking GPT-4 to analyze and route
2. **Two API calls per trace**: One for analysis, one for routing
3. **JSON responses**: GPT-4 returns structured JSON that we parse
4. **Traces capture decisions**: We save what GPT-4 decided (analysis + agent sequence)
5. **Training data**: These traces become training examples for Flan-T5

---

## Why This Works for Knowledge Distillation

- **GPT-4 is the teacher**: It makes expert orchestration decisions
- **Traces are lessons**: Each trace shows GPT-4's decision-making process
- **Flan-T5 learns**: By training on these traces, Flan-T5 learns to make similar decisions
- **Result**: Flan-T5 can orchestrate like GPT-4, but locally and cheaply

---

## Summary

**How GPT-4 makes decisions**:
1. We send a prompt asking GPT-4 to analyze the query
2. GPT-4 returns JSON with complexity, reasoning type, etc.
3. We send another prompt asking GPT-4 to choose agents
4. GPT-4 returns JSON with agent sequence
5. We combine both into a trace and save it

**Where traces are stored**:
- `data/expert_traces/expert_traces.jsonl` - Raw traces
- `data/expert_traces/training_data.jsonl` - Formatted for training

**What each trace contains**:
- The original query
- GPT-4's analysis (complexity, reasoning type, etc.)
- GPT-4's agent sequence decision
- Metadata (cost, latency, timestamp)

This is how we capture GPT-4's "expert knowledge" to train Flan-T5!





