# 5 Different Queries for SLM Orchestration Demo

These queries are designed to trigger **different orchestration patterns** from the Flan-T5 orchestrator, demonstrating its ability to adapt to different query types.

---

## Query 1: Simple Factual Query
**Expected Sequence:** `retriever → answering`

**Query:**
```
What is Section 302 of the Indian Penal Code?
```

**Why this triggers simple routing:**
- Well-formed, specific query
- Clear legal provision reference
- No vagueness or complexity
- Direct factual question

**Expected SLM Analysis:**
- Complexity: Simple
- Reasoning Type: Factual
- Confidence: ~70-75% (has legal terms)
- **No booster needed** - query is already clear

---

## Query 2: Vague/Short Query
**Expected Sequence:** `booster → retriever → answering`

**Query:**
```
what is 21
```

**Why this triggers booster:**
- Very short (3 words)
- Vague - "21" could mean anything
- Needs enhancement to understand context
- Likely refers to Article 21 but unclear

**Expected SLM Analysis:**
- Complexity: Simple (but vague)
- Reasoning Type: Factual
- Requires Enhancement: **True**
- Confidence: ~50-55% (short, vague)
- **Booster needed** to clarify: "What is Article 21 of the Indian Constitution?"

---

## Query 3: Complex Analytical Query
**Expected Sequence:** `booster → retriever → answering → verifier`

**Query:**
```
Analyze the legal implications of the recent Supreme Court judgment on privacy rights and how it affects data protection laws in India
```

**Why this triggers full pipeline:**
- Complex analytical query
- Multiple legal concepts (privacy, data protection)
- Requires verification of recent judgments
- Needs comprehensive analysis

**Expected SLM Analysis:**
- Complexity: Complex
- Reasoning Type: Analytical
- Requires Enhancement: True
- Requires Verification: **True**
- Confidence: ~80-85% (long, specific, legal terms)
- **Full pipeline** - booster, retriever, answering, verifier

---

## Query 4: Comparative Query
**Expected Sequence:** `booster → retriever → answering → verifier`

**Query:**
```
What is the difference between murder and culpable homicide under Indian law?
```

**Why this triggers comparative routing:**
- Comparative reasoning type
- Requires comparing two legal concepts
- Needs verification to ensure accuracy
- Complex legal distinction

**Expected SLM Analysis:**
- Complexity: Moderate to Complex
- Reasoning Type: **Comparative**
- Requires Verification: True
- Confidence: ~75-80%
- **Full pipeline with verifier** - needs accurate comparison

---

## Query 5: Procedural Query
**Expected Sequence:** `booster → retriever → answering`

**Query:**
```
How to file a First Information Report (FIR) in India?
```

**Why this triggers procedural routing:**
- "How to" indicates procedural query
- Needs step-by-step guidance
- Requires enhancement for clarity
- Doesn't necessarily need verification (procedural info)

**Expected SLM Analysis:**
- Complexity: Moderate
- Reasoning Type: **Procedural**
- Requires Enhancement: True
- Requires Verification: False (procedural, not analytical)
- Confidence: ~70-75%
- **Booster + Retriever + Answering** (no verifier needed)

---

## Summary Table

| Query | Type | Expected Sequence | Key Trigger |
|-------|------|-------------------|-------------|
| 1. "What is Section 302..." | Simple Factual | `retriever → answering` | Well-formed, specific |
| 2. "what is 21" | Vague/Short | `booster → retriever → answering` | Very short, unclear |
| 3. "Analyze the legal implications..." | Complex Analytical | `booster → retriever → answering → verifier` | Complex, analytical, needs verification |
| 4. "What is the difference between..." | Comparative | `booster → retriever → answering → verifier` | Comparative reasoning |
| 5. "How to file a FIR..." | Procedural | `booster → retriever → answering` | "How to" procedural query |

---

## How to Test

1. **Run Streamlit:**
   ```powershell
   streamlit run legal_ui.py
   ```

2. **Try each query** and observe:
   - **SLM Query Analysis** (Complexity, Reasoning Type, Confidence)
   - **Agent Sequence** (should differ for each query)
   - **SLM Confidence** (should vary based on query quality)

3. **Compare the results:**
   - Query 1: Should skip booster (simple)
   - Query 2: Should use booster first (vague)
   - Query 3: Should use full pipeline with verifier (complex)
   - Query 4: Should use verifier (comparative)
   - Query 5: Should use booster but no verifier (procedural)

---

## Expected Variations

The SLM orchestrator should show:
- ✅ **Different agent sequences** for different query types
- ✅ **Varying SLM confidence** (50-90% based on query quality)
- ✅ **Adaptive routing** based on query characteristics
- ✅ **Intelligent decision-making** without fixed rules

This demonstrates that **Flan-T5-small (80M parameters) can effectively orchestrate** multi-agent systems!



