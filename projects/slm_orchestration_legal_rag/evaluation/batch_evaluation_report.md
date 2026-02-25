# Batch Evaluation Report - 300 Query Dataset

## Executive Summary

This report presents evaluation results for orchestration strategies on a dataset of **300 realistic legal queries** from IndicLegalQA.

**Evaluation Method**: Batch processing with 50 queries per batch, concurrent execution for efficiency.

**Key Findings:**
- **Flan-T5 (Trained)**: 14.0% routing accuracy, 64.9% WAI
- **GPT-4 (Baseline)**: 95.3% routing accuracy, 99.0% WAI
- **Cost Reduction**: infx cheaper with Flan-T5
- **Latency Improvement**: 1.9x faster with Flan-T5

## Comparison Table

| Metric | FlanT5 | RuleBased | NoOrchestration | GPT4 |
|---|---|---|---|---|
| Routing Accuracy | 14.0% | 3.0% | 0.0% | 95.3% |
| RAS (PEARL) | 14.0% | 3.0% | 0.0% | 95.3% |
| WAI (PEARL) | 64.9% | 54.8% | 47.4% | 99.0% |
| Avg Latency (ms) | 1607.2 | 0.0 | 0.0 | 3116.7 |
| Cost per Decision | $0.00000 | $0.00000 | $0.00000 | $0.00814 |
| Total Cost | $0.0000 | $0.0000 | $0.0000 | $2.4422 |
| Optimal Routing | 14.0% | 3.0% | 0.0% | 95.3% |
| Error Rate | 0.0% | 0.0% | 0.0% | 0.0% |

## Detailed Analysis

### FlanT5

**Accuracy Metrics:**
- Routing Accuracy: 14.0%
- Sequence Accuracy: 14.0%
- RAS (PEARL): 14.0%
- WAI (PEARL): 64.9%
- Complexity Classification: 93.0%

**Performance Metrics:**
- Average Latency: 1607.2ms
- P50 Latency: 1198.5ms
- P95 Latency: 2987.3ms
- P99 Latency: 3477.6ms

**Cost Metrics:**
- Total Cost: $0.0000
- Per Decision: $0.00000
- Per 1000 Decisions: $0.00

**Efficiency Metrics:**
- Unnecessary Agent Calls: 66
- Missed Necessary Agents: 251
- Optimal Routing Rate: 14.0%

**Reliability Metrics:**
- Error Rate: 0.0%
- Calibration Error: 0.000

---

### RuleBased

**Accuracy Metrics:**
- Routing Accuracy: 3.0%
- Sequence Accuracy: 3.0%
- RAS (PEARL): 3.0%
- WAI (PEARL): 54.8%
- Complexity Classification: 93.0%

**Performance Metrics:**
- Average Latency: 0.0ms
- P50 Latency: 0.0ms
- P95 Latency: 0.1ms
- P99 Latency: 0.4ms

**Cost Metrics:**
- Total Cost: $0.0000
- Per Decision: $0.00000
- Per 1000 Decisions: $0.00

**Efficiency Metrics:**
- Unnecessary Agent Calls: 47
- Missed Necessary Agents: 339
- Optimal Routing Rate: 3.0%

**Reliability Metrics:**
- Error Rate: 0.0%
- Calibration Error: 0.000

---

### NoOrchestration

**Accuracy Metrics:**
- Routing Accuracy: 0.0%
- Sequence Accuracy: 0.0%
- RAS (PEARL): 0.0%
- WAI (PEARL): 47.4%
- Complexity Classification: 0.0%

**Performance Metrics:**
- Average Latency: 0.0ms
- P50 Latency: 0.0ms
- P95 Latency: 0.0ms
- P99 Latency: 0.0ms

**Cost Metrics:**
- Total Cost: $0.0000
- Per Decision: $0.00000
- Per 1000 Decisions: $0.00

**Efficiency Metrics:**
- Unnecessary Agent Calls: 0
- Missed Necessary Agents: 405
- Optimal Routing Rate: 0.0%

**Reliability Metrics:**
- Error Rate: 0.0%
- Calibration Error: 0.000

---

### GPT4

**Accuracy Metrics:**
- Routing Accuracy: 95.3%
- Sequence Accuracy: 95.3%
- RAS (PEARL): 95.3%
- WAI (PEARL): 99.0%
- Complexity Classification: 58.3%

**Performance Metrics:**
- Average Latency: 3116.7ms
- P50 Latency: 3010.6ms
- P95 Latency: 3963.2ms
- P99 Latency: 4485.3ms

**Cost Metrics:**
- Total Cost: $2.4422
- Per Decision: $0.00814
- Per 1000 Decisions: $8.14

**Efficiency Metrics:**
- Unnecessary Agent Calls: 8
- Missed Necessary Agents: 7
- Optimal Routing Rate: 95.3%

**Reliability Metrics:**
- Error Rate: 0.0%
- Calibration Error: 0.000

---


## Dataset Information

- **Total Queries**: 300
- **Source**: IndicLegalQA Dataset
- **Evaluation Method**: Batch processing (50 queries per batch)
- **Concurrent Processing**: Enabled for efficiency

## Methodology

1. **Batch Processing**: Queries processed in batches of 50 to optimize API usage
2. **Concurrent Execution**: Multiple queries processed in parallel within each batch
3. **Metrics Calculation**: Standard PEARL metrics (RAS, WAI) applied
4. **Error Handling**: Robust error handling with fallback mechanisms

## Conclusion

This evaluation demonstrates the performance of different orchestration strategies on a realistic legal query dataset. The results show the trade-offs between accuracy, cost, and latency for each approach.

