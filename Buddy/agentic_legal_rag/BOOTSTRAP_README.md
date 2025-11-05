# Query Booster SLM Data Bootstrap System

This system generates structured training data for the Query Booster SLM using rule-based heuristics and optional GPT refinement.

## 🎯 Overview

The bootstrap system creates high-quality training data by:
1. **Rule-based Heuristics**: Intelligent classification based on legal query patterns
2. **GPT Refinement**: Optional enhancement using OpenAI's GPT models
3. **Structured Output**: Consistent JSON format for all training examples
4. **Comprehensive Logging**: Full audit trail of all decisions

## 📁 Files

- `bootstrap_dataset.py` - Main bootstrap script
- `train_booster_slm.py` - Training script for the SLM
- `demo_bootstrap.py` - Demonstration script
- `data/query_booster.jsonl` - Generated training dataset
- `data/training_format.jsonl` - Training-ready format
- `logs/data_bootstrap.log` - Bootstrap process logs

## 🚀 Quick Start

### 1. Generate Training Dataset

```bash
python bootstrap_dataset.py
```

This will:
- Process 20 sample legal queries
- Generate structured JSON decisions
- Save dataset to `data/query_booster.jsonl`
- Log all decisions to `logs/data_bootstrap.log`

### 2. Run Demonstration

```bash
python demo_bootstrap.py
```

This will show:
- Bootstrap dataset generation
- Dataset analysis and statistics
- Integration with existing system
- Training data preparation

### 3. Train the SLM (Optional)

```bash
python train_booster_slm.py
```

**Note**: Requires `transformers` and `torch` libraries:
```bash
pip install transformers torch
```

## 📊 Generated Dataset Format

Each training example contains:

```json
{
  "query": "377 rights",
  "need_boost": true,
  "boosted_query": "Section 377 of the Indian Penal Code, Supreme Court judgments after 2018, constitutional validity",
  "retrieval_mode": "both",
  "top_k": 5,
  "require_human_review": true,
  "confidence": 0.3,
  "reasoning": "Query is vague or too short, needs enhancement; Query is general, searching both statutes and judgments; Retrieving top 5 documents based on query complexity",
  "method": "rule_based"
}
```

## 🔧 Configuration

### Rule-based Heuristics

The system uses intelligent patterns to classify queries:

- **Statute Keywords**: `article`, `section`, `act`, `code`, `ipc`, `constitution`
- **Judgment Keywords**: `judgment`, `case`, `court`, `supreme court`, `high court`
- **Sensitive Topics**: `rape`, `murder`, `terrorism`, `sedition`, `contempt`
- **Vague Terms**: `rights`, `law`, `legal`, `help`, `advice`

### Retrieval Mode Classification

- **Statutes**: Queries mentioning specific legal provisions
- **Judgments**: Queries about court cases or decisions
- **Both**: General legal queries requiring comprehensive search

### Top-K Determination

- **Simple queries** (≤3 words): `top_k = 5`
- **Medium queries** (4-6 words): `top_k = 8`
- **Complex queries** (>6 words): `top_k = 10`

## 🤖 GPT Refinement (Optional)

To enable GPT refinement:

1. Set your OpenAI API key:
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

2. Modify `bootstrap_dataset.py`:
   ```python
   use_gpt_refinement = True
   ```

3. Run the bootstrap script

## 📈 Dataset Statistics

The generated dataset includes:

- **20 training examples** (expandable)
- **Balanced distribution**: 50% boosted, 50% not boosted
- **Mode distribution**: 60% statutes, 35% both, 5% judgments
- **Average confidence**: 0.51
- **Comprehensive reasoning** for each decision

## 🔗 Integration with Existing System

The bootstrap system integrates seamlessly with the existing Query Booster agent:

```python
from bootstrap_dataset import QueryBootstrapGenerator
from booster_agent import PromptBooster

# Generate training data
generator = QueryBootstrapGenerator()
decision = generator.process_query("377 rights")

# Use with existing agent
booster = PromptBooster()
decision = booster.generate_decision("377 rights")
```

## 📝 Customization

### Adding More Queries

Edit the `QUERIES` list in `bootstrap_dataset.py`:

```python
QUERIES = [
    "your custom query 1",
    "your custom query 2",
    # ... add more queries
]
```

### Loading from File

Create a text file with queries (one per line) and load it:

```python
queries = load_queries_from_file("my_queries.txt")
```

### Custom Patterns

Modify the `legal_patterns` dictionary in `QueryBootstrapGenerator`:

```python
self.legal_patterns = {
    'statute_keywords': ['your', 'custom', 'keywords'],
    'judgment_keywords': ['court', 'case', 'judgment'],
    # ... add more patterns
}
```

## 🎓 Training the SLM

The generated dataset can be used to train a custom Query Booster SLM:

1. **Prepare data**: Run `bootstrap_dataset.py`
2. **Train model**: Run `train_booster_slm.py`
3. **Use trained model**: Update `booster_agent.py` to use the trained model

## 📊 Monitoring and Logging

All bootstrap activities are logged to `logs/data_bootstrap.log`:

- Query processing decisions
- Rule-based classifications
- GPT refinement results
- Error handling and fallbacks

## 🔍 Quality Assurance

The system includes several quality checks:

- **JSON validation**: Ensures all outputs are valid JSON
- **Field validation**: Verifies all required fields are present
- **Confidence scoring**: Provides confidence metrics for decisions
- **Reasoning generation**: Explains the decision-making process

## 🚀 Next Steps

1. **Expand dataset**: Add more diverse legal queries
2. **Train SLM**: Use the dataset to train a custom model
3. **Evaluate performance**: Test the trained model on new queries
4. **Iterate**: Refine patterns and rules based on results

## 📞 Support

For questions or issues:
- Check the logs in `logs/data_bootstrap.log`
- Run the demonstration script: `python demo_bootstrap.py`
- Review the generated dataset: `data/query_booster.jsonl`

---

**Generated by Query Booster Bootstrap System** 🎯

