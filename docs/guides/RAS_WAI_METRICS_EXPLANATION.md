# RAS and WAI Metrics: Calculation and Rationale

## Overview

**RAS (Routing Accuracy Score)** and **WAI (Workflow Appropriateness Index)** are two novel evaluation metrics developed specifically for the PEARL framework to assess orchestration quality in multi-agent RAG systems. These metrics were created because existing evaluation methods (like end-to-end answer quality) don't capture the nuances of orchestration decisions.

---

## Why These Metrics Were Created

### Problem Statement

Traditional evaluation metrics for RAG systems focus on:
- **Answer quality** (correctness, relevance)
- **Response time** (latency)
- **Cost** (computational expenses)

However, in **multi-agent orchestration systems**, these metrics don't answer critical questions:
1. **Did the orchestrator select the right agents?** (e.g., should it have called the retriever AND verifier, or just retriever?)
2. **Did it call agents in the correct order?** (e.g., retriever → answering → verifier vs. answering → retriever)
3. **Did it avoid unnecessary agent calls?** (e.g., calling booster when not needed)
4. **Did it miss necessary agents?** (e.g., not calling verifier when citations need verification)

### Solution: Orchestration-Specific Metrics

RAS and WAI were designed to evaluate **orchestration quality** independently from answer quality, allowing researchers to:
- Compare different orchestration strategies (SLM vs. LLM vs. rule-based)
- Identify specific orchestration failures (wrong agent selection vs. wrong order)
- Optimize orchestration models separately from answer generation
- Measure the effectiveness of knowledge distillation for orchestration

---

## 1. Routing Accuracy Score (RAS)

### Definition

**RAS** measures the percentage of queries where the orchestrator correctly identified **which agents** are needed, regardless of the order in which they're called.

### Formula

```
RAS = (Number of queries with correct agent selection) / (Total queries)
```

Where "correct agent selection" means:
- The **set** of predicted agents exactly matches the **set** of expected agents
- Order doesn't matter for RAS

### Implementation

```python
def _calculate_ras(self, predicted: List[List[str]], expected: List[List[str]]) -> float:
    """
    Calculate Routing Accuracy Score (RAS) - PEARL metric
    
    RAS measures the accuracy of agent selection (set-based comparison)
    """
    if not predicted or not expected:
        return 0.0
    
    correct = 0
    for pred, exp in zip(predicted, expected):
        if set(pred) == set(exp):  # Set comparison (order-independent)
            correct += 1
    
    return correct / len(predicted) if predicted else 0.0
```

### Example

**Query**: "What is Article 21 of the Indian Constitution?"

| Scenario | Predicted Agents | Expected Agents | RAS Match? |
|----------|------------------|-----------------|------------|
| Correct | `[retriever, answering]` | `[retriever, answering]` | ✅ Yes (1.0) |
| Wrong order | `[answering, retriever]` | `[retriever, answering]` | ✅ Yes (1.0) - order doesn't matter |
| Missing agent | `[retriever]` | `[retriever, answering]` | ❌ No (0.0) |
| Extra agent | `[retriever, answering, verifier]` | `[retriever, answering]` | ❌ No (0.0) |
| Wrong agents | `[booster, answering]` | `[retriever, answering]` | ❌ No (0.0) |

### Interpretation

- **RAS = 1.0 (100%)**: Perfect agent selection for all queries
- **RAS = 0.8 (80%)**: Correct agent selection for 80% of queries
- **RAS = 0.0 (0%)**: Never selects the correct set of agents

**Key Insight**: RAS answers "Did we call the right agents?" but not "Did we call them in the right order?"

---

## 2. Workflow Appropriateness Index (WAI)

### Definition

**WAI** is a composite metric that evaluates the **overall appropriateness** of the workflow, considering:
1. **Agent selection accuracy** (which agents were called)
2. **Sequence order correctness** (the order in which agents were called)
3. **Penalties for wrong agents** (extra or missing agents)

### Formula

The WAI calculation is more nuanced:

```
For each query:
  If predicted_agents == expected_agents (perfect match):
    WAI_score = 1.0
  
  Else if predicted_set == expected_set (right agents, wrong order):
    agent_score = correct_agents / total_expected_agents
    order_score = LCS_similarity(predicted, expected)
    WAI_score = 0.7 * agent_score + 0.3 * order_score
  
  Else (wrong agents):
    agent_score = correct_agents / total_expected_agents
    extra_agents = |predicted_set - expected_set|
    missing_agents = |expected_set - predicted_set|
    penalty = (extra_agents + missing_agents) * 0.1
    WAI_score = max(0.0, agent_score - penalty)

Overall WAI = mean(WAI_score for all queries)
```

### Implementation

```python
def _calculate_wai(self, predicted: List[List[str]], expected: List[List[str]], queries: List[str]) -> float:
    """
    Calculate Workflow Appropriateness Index (WAI) - PEARL metric
    
    WAI measures how appropriate the workflow is for the query:
    - Considers both agent selection AND sequence order
    - Penalizes unnecessary agents
    - Rewards appropriate agent sequences
    """
    if not predicted or not expected:
        return 0.0
    
    scores = []
    for pred, exp, query in zip(predicted, expected, queries):
        score = 0.0
        
        # Perfect match (both agents and order)
        if pred == exp:
            score = 1.0
        else:
            # Partial credit for correct agents (wrong order)
            pred_set = set(pred)
            exp_set = set(exp)
            
            # Agent selection accuracy
            correct_agents = len(pred_set & exp_set)
            total_agents = len(exp_set)
            agent_score = correct_agents / total_agents if total_agents > 0 else 0.0
            
            # Sequence order accuracy (if agents match)
            if pred_set == exp_set:
                # Check order similarity using Longest Common Subsequence (LCS)
                order_score = self._sequence_order_similarity(pred, exp)
                score = 0.7 * agent_score + 0.3 * order_score
            else:
                # Penalize for wrong agents
                extra_agents = len(pred_set - exp_set)
                missing_agents = len(exp_set - pred_set)
                penalty = (extra_agents + missing_agents) * 0.1
                score = max(0.0, agent_score - penalty)
        
        scores.append(score)
    
    return np.mean(scores) if scores else 0.0

def _sequence_order_similarity(self, pred: List[str], exp: List[str]) -> float:
    """Calculate similarity of sequence order using Longest Common Subsequence (LCS)"""
    if not pred or not exp:
        return 0.0
    
    # Calculate LCS length
    def lcs_length(seq1, seq2):
        m, n = len(seq1), len(seq2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if seq1[i-1] == seq2[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])
        return dp[m][n]
    
    lcs = lcs_length(pred, exp)
    max_len = max(len(pred), len(exp))
    return lcs / max_len if max_len > 0 else 0.0
```

### Example Calculations

**Query**: "Compare Article 14 and Article 21 of the Constitution"

**Expected**: `[retriever, answering, verifier]`

| Scenario | Predicted | Agent Score | Order Score | Penalty | WAI Score |
|----------|-----------|-------------|-------------|---------|-----------|
| **Perfect** | `[retriever, answering, verifier]` | 1.0 | 1.0 | 0 | **1.0** |
| **Wrong order** | `[answering, retriever, verifier]` | 1.0 | 0.67 (LCS=2/3) | 0 | **0.9** (0.7×1.0 + 0.3×0.67) |
| **Missing agent** | `[retriever, answering]` | 0.67 (2/3) | N/A | 0.1 | **0.57** (0.67 - 0.1) |
| **Extra agent** | `[retriever, answering, verifier, booster]` | 1.0 | N/A | 0.1 | **0.9** (1.0 - 0.1) |
| **Wrong agents** | `[booster, answering]` | 0.33 (1/3) | N/A | 0.2 | **0.13** (0.33 - 0.2) |

### Interpretation

- **WAI = 1.0 (100%)**: Perfect workflows (correct agents in correct order)
- **WAI = 0.8-0.9**: Good workflows (correct agents, minor order issues or small penalties)
- **WAI = 0.5-0.7**: Moderate workflows (some missing/extra agents or significant order issues)
- **WAI < 0.5**: Poor workflows (many wrong agents or severe order problems)

**Key Insight**: WAI provides a nuanced score that rewards correct agent selection, penalizes wrong agents, and considers sequence order importance.

---

## Key Differences: RAS vs. WAI

| Aspect | RAS | WAI |
|--------|-----|-----|
| **Focus** | Agent selection only | Agent selection + order + penalties |
| **Order sensitivity** | No (set-based) | Yes (sequence-based) |
| **Penalties** | Binary (correct/incorrect) | Graduated (partial credit) |
| **Use case** | "Did we call the right agents?" | "Is the overall workflow appropriate?" |
| **Range** | 0.0 to 1.0 | 0.0 to 1.0 |

### When to Use Each Metric

- **Use RAS** when you want to know if the orchestrator identifies the correct set of agents
- **Use WAI** when you want a comprehensive measure of workflow quality including order and efficiency

---

## Design Rationale

### Why Set-Based Comparison for RAS?

Agent selection is fundamentally a **set problem**: the orchestrator needs to identify which agents are required, but the order can sometimes be flexible (especially for independent agents). RAS uses set comparison to focus on the core routing decision.

### Why Weighted Components for WAI?

WAI uses a weighted formula (70% agent selection, 30% order) because:
- **Agent selection is more critical**: Calling the wrong agents leads to incorrect results
- **Order matters but less**: Some agents can be reordered without major impact, but dependencies must be respected
- **Penalties prevent gaming**: Extra or missing agents reduce efficiency and correctness

### Why LCS for Order Similarity?

The **Longest Common Subsequence (LCS)** algorithm measures how much of the correct sequence is preserved, even if some elements are out of order. This provides partial credit for "mostly correct" sequences.

---

## Research Context

These metrics were developed as part of the **PEARL (Performance-Efficient Agentic RAG through Learned Orchestration)** research framework to:

1. **Evaluate knowledge distillation**: Compare SLM orchestrators (Flan-T5) to LLM orchestrators (GPT-4)
2. **Measure orchestration quality independently**: Separate orchestration decisions from answer quality
3. **Enable systematic optimization**: Identify specific orchestration failures (selection vs. order)
4. **Support academic research**: Provide standardized metrics for comparing orchestration strategies

### Results from PEARL Research

According to the project reports:
- **Flan-T5 (SLM)**: RAS = 87.5%, WAI = 91.3%
- **GPT-4 (LLM)**: RAS = 92.9%, WAI = 91.2%
- **Rule-Based**: RAS = 28.6%, WAI = 63.3%

This demonstrates that:
- SLMs can achieve near-LLM orchestration quality (87.5% vs. 92.9% RAS)
- WAI captures workflow quality beyond simple accuracy
- The metrics successfully distinguish between different orchestration strategies

---

## Implementation Location

The metrics are implemented in:
- **File**: `projects/slm_orchestration_legal_rag/evaluation/orchestration_metrics.py`
- **Class**: `OrchestrationEvaluator`
- **Methods**: `_calculate_ras()` and `_calculate_wai()`

---

## References

- PEARL Framework Project Report: `PEARL_FRAMEWORK_PROJECT_REPORT.md`
- Implementation: `projects/slm_orchestration_legal_rag/evaluation/orchestration_metrics.py`
- Evaluation Results: `projects/slm_orchestration_legal_rag/GPT4_COMPARISON_RESULTS.md`





