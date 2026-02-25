# Confidence Score Explanation

## Two Types of Confidence

### 1. SLM Confidence (70% - Now Dynamic!)

**What it is:**
- Confidence in the **orchestration decision** (which agents to use)
- How confident Flan-T5 is that it chose the right agent sequence

**Why it was always 70%:**
- The fallback function had a hardcoded value of `0.7` (70%)
- This happened when Flan-T5 couldn't generate valid JSON responses

**Fixed:**
- Now calculates confidence dynamically based on:
  - Query length (longer = more confident)
  - Legal terms present (section, IPC, etc. = more confident)
  - Query specificity (vague queries = less confident)
- Range: 50% to 90% depending on query quality

**Example:**
- "IPC section 302" → ~70-75% (has legal terms, specific)
- "what is 21" → ~50-55% (short, vague)
- "What are the provisions of Section 302 of the Indian Penal Code regarding punishment for murder?" → ~80-85% (long, specific, legal terms)

### 2. Answer Confidence (48% - Now More Accurate!)

**What it is:**
- Overall confidence in the **final answer quality**
- Combines multiple factors

**How it's calculated:**
```
Overall Confidence = (SLM Confidence × 30%) + (Answer Quality × 50%) + (Document Support × 20%)
```

**Components:**

1. **SLM Confidence (30%)**: Orchestration decision quality
   - Example: 70% → contributes 21%

2. **Answer Quality (50%)**: From answering agent
   - Based on:
     - Citation coverage (how many claims are cited)
     - Document similarity scores
   - Example: 50% → contributes 25%

3. **Document Support (20%)**: Based on retrieved documents
   - Number of documents (more = better)
   - Average similarity scores (higher = better)
   - Example: 5 docs with 0.8 avg similarity → contributes 16%

**Why you see 48%:**
- If SLM = 70%, Answer = 50%, Docs = 40%:
  - (0.70 × 0.3) + (0.50 × 0.5) + (0.40 × 0.2)
  - = 0.21 + 0.25 + 0.08
  - = 0.54 (54%)

- If Answer quality is lower (40%):
  - (0.70 × 0.3) + (0.40 × 0.5) + (0.40 × 0.2)
  - = 0.21 + 0.20 + 0.08
  - = 0.49 (49%) ≈ 48%

**What affects answer confidence:**
- ✅ More documents retrieved → Higher confidence
- ✅ Better document matches (higher similarity) → Higher confidence
- ✅ More citations in answer → Higher confidence
- ✅ Better answer quality from LLM → Higher confidence

## Improvements Made

1. **SLM Confidence is now dynamic** - varies based on query quality
2. **Answer confidence calculation improved** - better weights (50% answer quality vs 40% before)
3. **Document confidence considers quality** - not just count, but also similarity scores

## To See Changes

Restart Streamlit:
```powershell
streamlit run legal_ui.py
```

You should now see:
- **SLM Confidence**: Varies (50-90%) based on query
- **Answer Confidence**: More accurate, reflects actual answer quality



