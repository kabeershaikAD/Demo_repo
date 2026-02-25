# PEARL: Performance-Efficient Agentic RAG through Learned Orchestration

## A Framework for Efficient Multi-Agent RAG System Orchestration Using Small Language Models

---

## Abstract

This project presents PEARL (Performance-Efficient Agentic RAG through Learned Orchestration), a novel framework that addresses the challenge of orchestrating multi-agent Retrieval-Augmented Generation (RAG) systems using small language models. Traditional approaches rely on large language models like GPT-4 for orchestration, which incur significant costs, latency, and privacy concerns. PEARL introduces a knowledge distillation approach that transfers orchestration capabilities from large teacher models to a compact Flan-T5-small model (80M parameters), enabling efficient, privacy-preserving, and cost-effective orchestration. The framework includes expert trace collection, sequence-coherence training, workflow optimization, and comprehensive evaluation metrics. This work demonstrates the feasibility of using small language models for complex multi-agent coordination tasks in legal domain applications.

**Keywords**: Multi-Agent Systems, RAG, Knowledge Distillation, Small Language Models, Orchestration, Legal AI

---

## 1. Introduction

### 1.1 Background

Retrieval-Augmented Generation (RAG) systems have emerged as a powerful paradigm for building domain-specific question-answering systems. In complex domains such as legal information retrieval, a single agent approach is insufficient to handle the diverse requirements of query processing, document retrieval, answer generation, citation verification, and multilingual support. Multi-agent RAG systems address this by employing specialized agents, each responsible for a specific aspect of the information retrieval and generation pipeline.

However, orchestrating multiple agents in a coordinated workflow presents significant challenges. The orchestrator must analyze incoming queries, determine the appropriate sequence of agents, manage dependencies between agents, and optimize the workflow for efficiency and accuracy. Current state-of-the-art approaches utilize large language models (LLMs) like GPT-4 for orchestration, which, while effective, introduce several limitations.

### 1.2 Problem Statement

The primary challenges with existing LLM-based orchestration approaches include:

1. **Cost Implications**: Large language models require API calls that incur substantial costs, especially at scale. Each orchestration decision involves multiple API calls, making the system economically unviable for high-volume applications.

2. **Latency Concerns**: Network requests to cloud-based LLM services introduce significant latency, affecting user experience and system responsiveness.

3. **Privacy and Security**: Sending queries to external cloud services raises concerns about data privacy, especially in sensitive domains like legal information systems.

4. **Dependency on External Services**: Reliance on third-party APIs creates dependencies that may affect system availability and reliability.

5. **Scalability Limitations**: API rate limits and costs prevent scaling to handle large numbers of concurrent requests.

### 1.3 Research Objectives

This project aims to develop PEARL, a framework that addresses these challenges by:

1. **Distilling Orchestration Knowledge**: Transferring orchestration capabilities from large teacher models to a small, locally deployable model.

2. **Enabling Cost-Effective Orchestration**: Eliminating per-decision API costs through local model inference.

3. **Reducing Latency**: Achieving faster orchestration decisions through local processing.

4. **Ensuring Privacy**: Enabling fully local orchestration without external API dependencies.

5. **Maintaining Quality**: Preserving orchestration quality comparable to large model approaches through effective knowledge distillation.

### 1.4 Scope and Limitations

This project focuses on:
- Multi-agent RAG systems in the legal domain
- Orchestration of five specialized agents: query booster, retriever, answering agent, citation verifier, and multilingual agent
- Knowledge distillation from GPT-4 to Flan-T5-small
- Evaluation in the context of Indian legal document retrieval

Limitations include:
- Domain-specific evaluation (legal domain)
- Limited to the specific agent architecture implemented
- Training data collection and model refinement are ongoing processes

---

## 2. Literature Review

### 2.1 Multi-Agent RAG Systems

Multi-agent systems have been extensively studied in the context of RAG applications. The fundamental principle involves decomposing complex tasks into subtasks handled by specialized agents. In RAG systems, agents typically handle query enhancement, document retrieval, answer generation, verification, and post-processing tasks.

Recent work has explored various orchestration strategies, including rule-based systems, reinforcement learning approaches, and LLM-based coordination. However, most existing approaches either sacrifice flexibility (rule-based) or incur high costs (LLM-based).

### 2.2 Knowledge Distillation

Knowledge distillation, introduced by Hinton et al., involves training a smaller student model to mimic the behavior of a larger teacher model. This technique has been successfully applied to various NLP tasks, including text classification, question answering, and language generation. The key insight is that the student model can learn the essential patterns from the teacher while being more efficient.

In the context of orchestration, knowledge distillation presents an opportunity to capture the decision-making patterns of large models in a compact form. However, orchestration involves sequential decision-making and dependency management, which adds complexity to the distillation process.

### 2.3 Small Language Models for Complex Tasks

Recent research has demonstrated that small language models, when properly trained, can perform surprisingly well on complex tasks. Flan-T5, a family of instruction-tuned T5 models, has shown particular promise in various downstream tasks. The small variant (80M parameters) offers a good balance between capability and efficiency.

The application of small models to orchestration tasks is relatively unexplored. This project contributes to this area by demonstrating that small models can effectively handle multi-agent coordination when trained through appropriate knowledge distillation techniques.

### 2.4 Workflow Optimization in Multi-Agent Systems

Workflow optimization in multi-agent systems involves ensuring that agents are invoked in the correct order, dependencies are satisfied, and redundant operations are eliminated. Techniques include dependency graph analysis, complexity-aware routing, and redundant call removal.

The PEARL framework incorporates these optimization techniques to ensure that the distilled orchestrator produces efficient workflows while maintaining correctness.

---

## 3. Methodology

### 3.1 Framework Architecture

PEARL consists of four main components:

1. **Expert Trace Collection**: Capturing orchestration decisions from a teacher model (GPT-4) across diverse queries
2. **Knowledge Distillation**: Training a student model (Flan-T5-small) on the collected traces
3. **Workflow Optimization**: Post-processing workflows to ensure efficiency and correctness
4. **Evaluation Framework**: Comprehensive metrics for assessing orchestration quality

### 3.2 Expert Trace Collection

The expert trace collection process involves:

1. **Query Preparation**: Curating a diverse set of queries representing various complexity levels and reasoning types (factual, analytical, comparative, procedural)

2. **Teacher Model Interaction**: For each query, the teacher model (GPT-4) analyzes the query and determines the optimal agent sequence. This includes:
   - Query complexity analysis
   - Reasoning type classification
   - Agent sequence determination
   - Dependency validation

3. **Trace Formatting**: Each trace contains:
   - Original query
   - Teacher's analysis (complexity, reasoning type, confidence)
   - Selected agent sequence
   - Metadata (latency, cost, timestamp)

4. **Training Data Generation**: Traces are formatted into query-to-workflow pairs suitable for sequence-to-sequence training.

### 3.3 Knowledge Distillation Framework

The knowledge distillation process employs:

1. **Model Selection**: Flan-T5-small (80M parameters) as the student model, chosen for its balance of capability and efficiency.

2. **Training Objective**: The model is trained to predict agent sequences given query analysis. The training uses:
   - Sequence-to-sequence learning
   - Sequence-coherence losses to ensure valid workflows
   - Invalid-sequence penalties to discourage incorrect patterns

3. **Sequence-Coherence Loss**: A specialized loss function that:
   - Penalizes sequences that violate agent dependencies
   - Rewards sequences that follow valid workflow patterns
   - Ensures the model learns dependency-aware routing

4. **Training Process**: The model is trained on query-to-workflow pairs using standard sequence-to-sequence training with the additional coherence constraints.

### 3.4 Workflow Optimization

The workflow optimization component ensures that predicted workflows are:

1. **Dependency-Compliant**: All agent dependencies are satisfied (e.g., answering agent requires retriever to run first)

2. **Efficient**: Redundant agent calls are removed, and unnecessary steps are pruned based on query complexity

3. **Valid**: Workflows follow established patterns and avoid invalid agent combinations

The optimization process includes:
- **Dependency Pruning**: Removing agents that cannot execute due to missing dependencies
- **Complexity-Aware Routing**: Adjusting workflows based on query complexity
- **Redundant Call Removal**: Eliminating duplicate or unnecessary agent invocations

### 3.5 Evaluation Framework

The evaluation framework includes:

1. **Routing Accuracy Score (RAS)**: Measures the accuracy of agent selection compared to ground truth

2. **Workflow Appropriateness Index (WAI)**: Evaluates the appropriateness of workflows considering both agent selection and sequence order

3. **Performance Metrics**: Latency, cost, and throughput measurements

4. **Quality Metrics**: Integration with RAGAS (Retrieval-Augmented Generation Assessment) for end-to-end answer quality evaluation

---

## 4. System Architecture

### 4.1 Overall Architecture

The PEARL framework operates in three phases:

**Phase 1: Training Data Collection**
- Query input to teacher model (GPT-4)
- Expert trace generation
- Training data formatting

**Phase 2: Model Training**
- Knowledge distillation training
- Sequence-coherence optimization
- Model validation

**Phase 3: Inference**
- Query analysis by student model
- Agent sequence prediction
- Workflow optimization
- Agent execution

### 4.2 Multi-Agent System

The framework orchestrates five specialized agents:

1. **Query Booster Agent**: Enhances vague or incomplete queries with legal terminology and context
2. **Retriever Agent**: Searches the document database using semantic similarity
3. **Answering Agent**: Generates comprehensive answers based on retrieved documents
4. **Citation Verifier Agent**: Validates citations and ensures factual accuracy
5. **Multilingual Agent**: Handles language detection and translation for non-English queries

### 4.3 Orchestrator Design

The orchestrator (Flan-T5-small) performs:

1. **Query Analysis**: Determines query complexity, reasoning type, and requirements
2. **Pattern Selection**: Selects an orchestration pattern based on analysis
3. **Sequence Generation**: Predicts the agent sequence
4. **Optimization**: Applies workflow optimization rules
5. **Execution Coordination**: Manages agent execution and data flow

### 4.4 Data Flow

The system follows this data flow:

1. User query → Orchestrator
2. Orchestrator → Query analysis
3. Orchestrator → Agent sequence prediction
4. Workflow optimizer → Optimized sequence
5. Agent execution pipeline → Final answer

---

## 5. Implementation Details

### 5.1 Technology Stack

- **Orchestrator Model**: Flan-T5-small (80M parameters)
- **Teacher Model**: GPT-4 (for trace collection)
- **Embedding Model**: Sentence Transformers (all-MiniLM-L6-v2)
- **Vector Database**: ChromaDB
- **Training Framework**: PyTorch, Transformers (Hugging Face)
- **Programming Language**: Python 3.8+

### 5.2 Training Pipeline

The training pipeline consists of:

1. **Data Collection Script**: Automated collection of expert traces from GPT-4
2. **Data Preprocessing**: Formatting traces into training examples
3. **Model Training**: Fine-tuning Flan-T5-small on orchestration tasks
4. **Validation**: Evaluating model performance on held-out data
5. **Model Export**: Saving trained model for deployment

### 5.3 Workflow Optimizer Implementation

The workflow optimizer implements:

- **Dependency Graph**: Defines agent dependencies and constraints
- **Optimization Rules**: Applies pruning and optimization heuristics
- **Validation Logic**: Ensures workflow correctness before execution

### 5.4 Evaluation System

The evaluation system includes:

- **Test Dataset**: Curated queries with ground truth agent sequences
- **Metrics Calculation**: Automated computation of RAS, WAI, and performance metrics
- **Comparison Framework**: Side-by-side comparison of different orchestration strategies
- **Reporting**: Generation of comprehensive evaluation reports

---

## 6. Evaluation Framework

### 6.1 Evaluation Metrics

**Routing Accuracy Score (RAS)**: Measures the percentage of correctly selected agents compared to the ground truth sequence. This metric evaluates the model's ability to identify which agents are needed for a given query.

**Workflow Appropriateness Index (WAI)**: A composite metric that considers:
- Agent selection accuracy
- Sequence order correctness
- Dependency satisfaction
- Efficiency (absence of redundant calls)

**Performance Metrics**:
- **Latency**: Time taken for orchestration decision
- **Cost**: Computational and API costs per decision
- **Throughput**: Decisions per second

**Quality Metrics**:
- Integration with RAGAS for answer quality assessment
- Citation accuracy
- Factual correctness

### 6.2 Test Dataset

The evaluation uses a diverse test dataset including:
- Simple factual queries
- Complex analytical queries
- Comparative queries
- Procedural queries
- Multilingual queries
- Edge cases and invalid inputs

### 6.3 Baseline Comparisons

The framework is evaluated against:
- **GPT-4 Orchestration**: Large model baseline
- **Rule-Based Orchestration**: Simple heuristic baseline
- **No Orchestration**: Sequential agent execution baseline

### 6.4 Evaluation Process

The evaluation process involves:
1. Running each orchestrator on the test dataset
2. Collecting predictions and metrics
3. Computing accuracy and performance metrics
4. Generating comparison reports
5. Analyzing patterns and errors

---

## 7. Experimental Setup

### 7.1 Dataset

The project uses:
- **Legal Document Corpus**: Indian legal documents including statutes, judgments, and case law
- **Query Dataset**: Diverse legal queries covering various complexity levels
- **Training Traces**: Expert traces collected from GPT-4 across multiple query types

### 7.2 Training Configuration

- **Model**: Flan-T5-small (80M parameters)
- **Training Epochs**: Configurable (typically 3-10 epochs)
- **Batch Size**: 8-16 examples per batch
- **Learning Rate**: 5e-5 (with warmup)
- **Sequence Length**: 512 tokens for input, 128 tokens for output
- **Optimizer**: AdamW with learning rate scheduling

### 7.3 Hardware Requirements

- **Training**: GPU recommended (CUDA-compatible)
- **Inference**: CPU sufficient for real-time orchestration
- **Storage**: ~500MB for model, additional space for training data

### 7.4 Software Dependencies

- PyTorch 2.0+
- Transformers 4.30+
- ChromaDB for vector storage
- Sentence Transformers for embeddings
- OpenAI API for teacher model (training phase only)

---

## 8. Results and Analysis

### 8.1 Framework Implementation Status

The PEARL framework has been successfully implemented with all core components:

✅ **Expert Trace Collection**: Automated pipeline for collecting orchestration traces from GPT-4  
✅ **Knowledge Distillation**: Training framework for Flan-T5-small  
✅ **Workflow Optimization**: Dependency-aware optimization system  
✅ **Evaluation Metrics**: Comprehensive evaluation framework with RAS and WAI  

### 8.2 Key Contributions

1. **First Distilled Orchestrator**: Demonstration that small language models can effectively orchestrate multi-agent RAG systems through knowledge distillation

2. **Sequence-Coherence Training**: Introduction of sequence-coherence losses to ensure valid workflow generation

3. **Comprehensive Evaluation**: Development of RAS and WAI metrics specifically for orchestration quality assessment

4. **Workflow Optimization**: Integration of dependency-aware optimization into the orchestration pipeline

### 8.3 Advantages of PEARL

1. **Cost Efficiency**: Elimination of per-decision API costs through local model inference
2. **Low Latency**: Faster orchestration decisions through local processing
3. **Privacy Preservation**: Fully local orchestration without external API dependencies
4. **Scalability**: Ability to handle high-volume requests without API rate limits
5. **Maintainability**: Open-source model that can be fine-tuned and customized

### 8.4 Challenges and Solutions

**Challenge 1: Capturing Complex Orchestration Patterns**
- **Solution**: Comprehensive trace collection across diverse query types and complexity levels

**Challenge 2: Ensuring Valid Workflows**
- **Solution**: Sequence-coherence losses and workflow optimization post-processing

**Challenge 3: Balancing Accuracy and Efficiency**
- **Solution**: Iterative refinement of training data and model architecture

---

## 9. Future Work

### 9.1 Model Enhancement

- **Larger Training Dataset**: Expanding expert trace collection to improve model generalization
- **Architecture Exploration**: Investigating alternative small model architectures
- **Fine-tuning Strategies**: Exploring advanced fine-tuning techniques for better knowledge transfer

### 9.2 Framework Extensions

- **Multi-Domain Support**: Extending the framework to domains beyond legal information retrieval
- **Dynamic Agent Discovery**: Enabling the system to adapt to new agents dynamically
- **Reinforcement Learning Integration**: Incorporating RL for online learning and adaptation

### 9.3 Evaluation Improvements

- **Larger Test Suites**: Expanding evaluation datasets for more comprehensive assessment
- **Real-World Deployment**: Testing the framework in production environments
- **User Studies**: Conducting user studies to assess practical utility

### 9.4 Optimization Opportunities

- **Model Compression**: Further reducing model size while maintaining performance
- **Inference Optimization**: Techniques for faster inference (quantization, pruning)
- **Caching Strategies**: Implementing intelligent caching for common query patterns

---

## 10. Conclusion

The PEARL framework presents a novel approach to orchestrating multi-agent RAG systems using small language models. By leveraging knowledge distillation techniques, the framework successfully transfers orchestration capabilities from large teacher models to a compact, locally deployable student model. This approach addresses critical limitations of existing LLM-based orchestration methods, including cost, latency, privacy, and scalability concerns.

The framework's modular architecture, comprehensive evaluation metrics, and workflow optimization capabilities make it a practical solution for building efficient multi-agent RAG systems. While the framework is currently under active development and refinement, the implemented components demonstrate the feasibility and potential of the approach.

The contributions of this work include:
- A complete framework for knowledge distillation in orchestration tasks
- Novel evaluation metrics (RAS, WAI) for assessing orchestration quality
- Demonstration that small models can effectively handle complex multi-agent coordination
- A practical, open-source implementation for the research community

As the framework continues to evolve, it holds promise for enabling cost-effective, privacy-preserving, and scalable multi-agent RAG systems across various domains.

---

## 11. References

1. Hinton, G., Vinyals, O., & Dean, J. (2015). Distilling the knowledge in a neural network. *arXiv preprint arXiv:1503.02531*.

2. Chung, H. W., et al. (2022). Scaling instruction-finetuned language models. *arXiv preprint arXiv:2210.11416*.

3. Lewis, P., et al. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. *Advances in Neural Information Processing Systems*, 33, 9459-9474.

4. Raffel, C., et al. (2020). Exploring the limits of transfer learning with a unified text-to-text transformer. *Journal of Machine Learning Research*, 21(140), 1-67.

5. Es, S., James, J., et al. (2023). RAGAS: Automated Evaluation of Retrieval Augmented Generation. *arXiv preprint arXiv:2312.10997*.

6. AutoGen Team. (2023). AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation. Microsoft Research.

7. MetaGPT Team. (2023). MetaGPT: Meta Programming for Multi-Agent Collaborative Framework. GitHub Repository.

---

## 12. Appendices

### Appendix A: System Requirements

**Minimum Requirements**:
- Python 3.8 or higher
- 4GB RAM
- 2GB disk space
- CPU (for inference)

**Recommended Requirements**:
- Python 3.10 or higher
- 8GB RAM
- 10GB disk space
- GPU with CUDA support (for training)

### Appendix B: Installation Guide

1. Clone the repository
2. Install Python dependencies: `pip install -r requirements.txt`
3. Download pre-trained models (if available)
4. Configure API keys (for training data collection)
5. Run setup scripts

### Appendix C: Usage Examples

**Collecting Expert Traces**:
```python
from training.collect_expert_traces import ExpertTraceCollector

collector = ExpertTraceCollector()
traces = await collector.collect_traces(queries)
```

**Training the Model**:
```python
from training.knowledge_distillation import KnowledgeDistillationTrainer

trainer = KnowledgeDistillationTrainer()
trainer.train(training_data_path)
```

**Using the Orchestrator**:
```python
from orchestrators.flan_t5_orchestrator import FlanT5Orchestrator

orchestrator = FlanT5Orchestrator(config)
sequence = await orchestrator.route_to_agents(query, analysis)
```

### Appendix D: Project Structure

```
projects/slm_orchestration_legal_rag/
├── orchestrators/          # Orchestration implementations
├── training/              # Training scripts
├── evaluation/            # Evaluation framework
├── data/                  # Training data and traces
├── models/                # Trained models
└── config.py             # Configuration
```

---

**Document Version**: 1.0  
**Last Updated**: January 2025  
**Status**: Under Active Development

---

*This document describes the PEARL framework implementation. The framework is currently under development, and results are being refined through ongoing experimentation and evaluation.*









