# SYSTEM DESIGN OF THE PEARL LEGAL RAG FRAMEWORK

## 1. Introduction to System Design

The PEARL (Performance-Efficient Agentic RAG through Learned Orchestration) framework is grounded in the need for a cost-effective, privacy-preserving, and efficient multi-agent orchestration system tailored for legal information retrieval. In contrast to fully cloud-dependent LLM orchestration systems that rely on expensive GPT-4 API calls, the proposed PEARL framework implements a knowledge distillation approach that transfers orchestration capabilities from large teacher models to a compact Flan-T5-small model (80M parameters), enabling real-time agent coordination, local processing, and significant cost reduction. This section provides a comprehensive design framework, an explanation of components, operational flows, infrastructure requirements, and software methods working together to enable PEARL to act as an intelligent orchestrator for multi-agent legal RAG systems.

The PEARL system uses a layered, modular architecture that allows each component (orchestration, query enhancement, retrieval, answering, verification, multilingual support) to act independently while all contribute to a collective main goal: providing accurate, citation-backed legal information retrieval with minimal cost and latency. Centered around a few key priorities, **local intelligence** is crucial to ensure user privacy and eliminate per-decision API costs. **Low-latency processing** is critical for providing timely legal research responses. The system offers **intelligent orchestration** through SLM-based agent routing decisions. **High reliability** is maintained via comprehensive fallback mechanisms and error handling. Mainly **cost-effectiveness** is a major goal, achieving 500× cost reduction compared to GPT-4 orchestration while maintaining comparable quality.

## 2. Proposed Project Framework

The proposed system framework for PEARL is a six-layer autonomous orchestration architecture. The collection of these layers represents the complete transformation pipeline from raw user queries to intelligent multi-agent coordination and collectively defines how PEARL analyzes queries, determines agent sequences, manages workflows, executes agent tasks, and evaluates orchestration quality for continuous improvement.

The six layers are:

1. **Core Infrastructure Layer**
2. **Query Processing and Analysis Layer**
3. **AI Orchestration and Intelligence Layer**
4. **Multi-Agent Execution Layer**
5. **Response Generation and Verification Layer**
6. **Evaluation and Knowledge Management Layer**

This framework enables PEARL to behave as a fully autonomous orchestration system capable of operating offline with deterministic reliability while maintaining orchestration quality comparable to large language models.

### 2.1 High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER INTERFACE LAYER                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Streamlit   │  │   FastAPI    │  │  CLI/API     │          │
│  │     UI       │  │   REST API   │  │  Interface   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              LAYER 3: AI ORCHESTRATION & INTELLIGENCE           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │         Flan-T5-small Orchestrator (80M params)         │   │
│  │  • Query Complexity Analysis                            │   │
│  │  • Reasoning Type Classification                        │   │
│  │  • Agent Sequence Prediction                           │   │
│  │  • Workflow Optimization                                │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│            LAYER 4: MULTI-AGENT EXECUTION LAYER                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Prompt     │  │   Retriever  │  │   Answering  │          │
│  │   Booster    │  │    Agent     │  │    Agent     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────┐  ┌──────────────┐                            │
│  │  Citation    │  │ Multilingual │                            │
│  │  Verifier    │  │    Agent     │                            │
│  └──────────────┘  └──────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              LAYER 6: EVALUATION & KNOWLEDGE MANAGEMENT         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   ChromaDB   │  │  Evaluation  │  │  Training    │          │
│  │  Vector DB   │  │   Metrics    │  │   Data       │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

**Figure 1: High-Level System Architecture**

```
┌─────────────────────────────────────────────────────────────────┐
│                    PROPOSED FRAMEWORK OF PEARL                  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Layer 1: Core Infrastructure                             │  │
│  │  • Python Runtime, Dependencies, Configuration           │  │
│  │  • ChromaDB Vector Database                              │  │
│  │  • Model Storage and Loading                            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Layer 2: Query Processing & Analysis                     │  │
│  │  • Query Input Validation                                │  │
│  │  • Language Detection                                    │  │
│  │  • Query Preprocessing                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Layer 3: AI Orchestration & Intelligence                  │  │
│  │  • Flan-T5 Query Analysis                                │  │
│  │  • Agent Sequence Prediction                             │  │
│  │  • Workflow Optimization                                 │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Layer 4: Multi-Agent Execution                           │  │
│  │  • Agent Initialization & Coordination                  │  │
│  │  • Sequential/Parallel Agent Execution                   │  │
│  │  • Context Passing Between Agents                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Layer 5: Response Generation & Verification               │  │
│  │  • Answer Synthesis                                      │  │
│  │  • Citation Verification                                 │  │
│  │  • Confidence Calculation                                │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Layer 6: Evaluation & Knowledge Management                │  │
│  │  • RAS/WAI Metrics Calculation                            │  │
│  │  • Performance Tracking                                  │  │
│  │  • Training Data Collection                              │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

**Figure 2: Proposed Framework of the PEARL System**

### 2.2 Detailed Framework Architecture

The PEARL framework architecture is composed of six interconnected layers, each containing specific sub-components that work together to enable intelligent orchestration. The following detailed architecture diagram illustrates the complete system structure with all major components and their interactions:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PEARL FRAMEWORK ARCHITECTURE                              │
│                                                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ LAYER 1: CORE INFRASTRUCTURE LAYER                                    │  │
│  ├───────────────────────────────────────────────────────────────────────┤  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │  │
│  │  │   Python     │  │  ChromaDB   │  │   Model     │  │    Config │ │  │
│  │  │   Runtime    │  │  Vector DB  │  │  Storage    │  │ Management│ │  │
│  │  │  (3.10+)     │  │  (21K docs) │  │  (Flan-T5)  │  │           │ │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘ │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │  │
│  │  │  PyTorch     │  │  Transformers│  │  Embedding   │                 │  │
│  │  │  Framework   │  │  Library     │  │  Models     │                 │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                 │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    │                                           │
│                                    ▼                                           │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ LAYER 2: QUERY PROCESSING & ANALYSIS LAYER                            │  │
│  ├───────────────────────────────────────────────────────────────────────┤  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │  │
│  │  │   Query      │  │  Language    │  │   Query     │  │ Complexity │ │  │
│  │  │   Input      │  │ Detection   │  │ Preprocessor│  │ Analyzer  │ │  │
│  │  │   Handler    │  │  Module     │  │             │  │           │ │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘ │  │
│  │                                                                         │  │
│  │  Input Sources: Streamlit UI | FastAPI REST | CLI Interface          │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    │                                           │
│                                    ▼                                           │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ LAYER 3: AI ORCHESTRATION & INTELLIGENCE LAYER                        │  │
│  ├───────────────────────────────────────────────────────────────────────┤  │
│  │  ┌───────────────────────────────────────────────────────────────┐   │  │
│  │  │         Flan-T5-small Orchestrator (80M parameters)          │   │  │
│  │  │  ┌─────────────────────────────────────────────────────────┐ │   │  │
│  │  │  │  Query Analysis Engine                                   │ │   │  │
│  │  │  │  • Complexity Classification (simple/moderate/complex)    │ │   │  │
│  │  │  │  • Reasoning Type (factual/analytical/comparative/proc)  │ │   │  │
│  │  │  │  • Confidence Scoring                                    │ │   │  │
│  │  │  │  • Pattern Matching (6 orchestration patterns)          │ │   │  │
│  │  │  └─────────────────────────────────────────────────────────┘ │   │  │
│  │  │  ┌─────────────────────────────────────────────────────────┐ │   │  │
│  │  │  │  Agent Sequence Predictor                               │ │   │  │
│  │  │  │  • Sequence-to-Sequence Generation                      │ │   │  │
│  │  │  │  • Pattern-Based Routing                                │ │   │  │
│  │  │  │  • Dependency-Aware Selection                            │ │   │  │
│  │  │  └─────────────────────────────────────────────────────────┘ │   │  │
│  │  └───────────────────────────────────────────────────────────────┘   │  │
│  │  ┌───────────────────────────────────────────────────────────────┐   │  │
│  │  │         Workflow Optimizer                                     │   │  │
│  │  │  • Dependency Validation                                       │   │  │
│  │  │  • Redundant Call Removal                                      │   │  │
│  │  │  • Complexity-Aware Routing                                     │   │  │
│  │  │  • Sequence Validation                                         │   │  │
│  │  └───────────────────────────────────────────────────────────────┘   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    │                                           │
│                                    ▼                                           │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ LAYER 4: MULTI-AGENT EXECUTION LAYER                                  │  │
│  ├───────────────────────────────────────────────────────────────────────┤  │
│  │  ┌───────────────────────────────────────────────────────────────┐  │  │
│  │  │              Agent Coordinator                                  │  │  │
│  │  │  • Agent Lifecycle Management                                  │  │  │
│  │  │  • Sequential/Parallel Execution                               │  │  │
│  │  │  • Context Passing Between Agents                               │  │  │
│  │  │  • Error Handling & Fallback                                    │  │  │
│  │  └───────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────┐   │  │
│  │  │   Prompt     │  │   Retriever  │  │   Answering │  │Citation │   │  │
│  │  │   Booster    │  │    Agent     │  │    Agent   │  │ Verifier│   │  │
│  │  │   Agent      │  │              │  │            │  │  Agent  │   │  │
│  │  │              │  │              │  │            │  │          │   │  │
│  │  │ • Flan-T5    │  │ • ChromaDB   │  │ • Groq/    │  │ • Seman │   │  │
│  │  │   Query      │  │   Search     │  │   OpenAI   │  │   Similar│   │  │
│  │  │   Enhance    │  │ • Embedding  │  │   LLM     │  │   Verify│   │  │
│  │  │ • Legal      │  │ • Citation   │  │ • Answer   │  │ • Claim │   │  │
│  │  │   Terms      │  │   Extract    │  │   Generate │  │   Valid │   │  │
│  │  │ • Context     │  │ • Cross-link │  │ • Citation │  │ • Flag  │   │  │
│  │  │   Addition   │  │              │  │   Extract  │  │   Issues │   │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └──────────┘   │  │
│  │  ┌──────────────┐                                                    │  │
│  │  │ Multilingual │                                                    │  │
│  │  │    Agent     │                                                    │  │
│  │  │              │                                                    │  │
│  │  │ • 8 Indian    │                                                    │  │
│  │  │   Languages  │                                                    │  │
│  │  │ • Neural     │                                                    │  │
│  │  │   Translation│                                                    │  │
│  │  │ • Legal Term│                                                    │  │
│  │  │   Preserve   │                                                    │  │
│  │  └──────────────┘                                                    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    │                                           │
│                                    ▼                                           │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ LAYER 5: RESPONSE GENERATION & VERIFICATION LAYER                     │  │
│  ├───────────────────────────────────────────────────────────────────────┤  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │  │
│  │  │  Response    │  │  Citation    │  │ Confidence   │  │ Multilingual│ │  │
│  │  │  Formatter   │  │ Presentation │  │ Calculator   │  │   Output   │ │  │
│  │  │              │  │             │  │              │  │   Handler  │ │  │
│  │  │ • Structure  │  │ • Legal     │  │ • SLM Conf   │  │ • Language │ │  │
│  │  │   Answer     │  │   Format    │  │   (30%)     │  │   Format   │ │  │
│  │  │ • Metadata   │  │ • Case Names │  │ • Answer    │  │ • Cultural │ │  │
│  │  │   Attach     │  │ • Statutes  │  │   Conf (45%)│  │   Context  │ │  │
│  │  │ • Source     │  │ • Articles  │  │ • Doc Conf  │  │ • Term Pres│ │  │
│  │  │   References │  │             │  │   (25%)     │  │             │ │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘ │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    │                                           │
│                                    ▼                                           │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ LAYER 6: EVALUATION & KNOWLEDGE MANAGEMENT LAYER                      │  │
│  ├───────────────────────────────────────────────────────────────────────┤  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │  │
│  │  │  ChromaDB    │  │  Evaluation  │  │  Training   │  │ Interaction│ │  │
│  │  │  Vector      │  │  Metrics     │  │  Data       │  │    Logs     │ │  │
│  │  │  Store       │  │  Calculator  │  │  Repository │  │            │ │  │
│  │  │              │  │              │  │             │  │            │ │  │
│  │  │ • 21K+ Legal │  │ • RAS Calc   │  │ • Expert    │  │ • Query    │ │  │
│  │  │   Documents  │  │ • WAI Calc   │  │   Traces    │  │   History  │ │  │
│  │  │ • Embeddings │  │ • Performance│  │ • Query-    │  │ • Decision │ │  │
│  │  │ • Metadata   │  │   Metrics    │  │   Workflow  │  │   Logs     │ │  │
│  │  │ • Citations  │  │ • Latency    │  │   Pairs     │  │ • Outcomes │ │  │
│  │  │ • Cross-link │  │ • Cost Track │  │ • GPT-4     │  │ • Analytics│ │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘ │  │
│  │  ┌──────────────┐                                                    │  │
│  │  │   Model      │                                                    │  │
│  │  │  Checkpoint  │                                                    │  │
│  │  │   Storage    │                                                    │  │
│  │  │              │                                                    │  │
│  │  │ • Flan-T5    │                                                    │  │
│  │  │   Weights    │                                                    │  │
│  │  │ • Trained    │                                                    │  │
│  │  │   Models     │                                                    │  │
│  │  │ • Optimized  │                                                    │  │
│  │  │   Checkpoints│                                                    │  │
│  │  └──────────────┘                                                    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Figure 3: Detailed Framework Architecture**

### 2.3 Data Flow Architecture

The following diagram illustrates the complete data flow through the PEARL framework from query input to final response:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         QUERY PROCESSING PIPELINE                           │
└─────────────────────────────────────────────────────────────────────────────┘

    User Query
        │
        ▼
┌───────────────────────────────────────────────────────────────────────────┐
│  LAYER 2: Query Processing                                               │
│  • Input Validation → Language Detection → Preprocessing                  │
│  Output: Normalized Query + Language Info                                │
└───────────────────────┬─────────────────────────────────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────────────────────────────────┐
│  LAYER 3: AI Orchestration                                               │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  Flan-T5 Analysis:                                                │  │
│  │  Query → [Complexity, Reasoning Type, Confidence, Pattern]        │  │
│  └───────────────────────┬───────────────────────────────────────────┘  │
│                          │                                                │
│                          ▼                                                │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  Agent Sequence Prediction:                                        │  │
│  │  Analysis → [Agent Sequence] (e.g., [retriever, answering])         │  │
│  └───────────────────────┬───────────────────────────────────────────┘  │
│                          │                                                │
│                          ▼                                                │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  Workflow Optimization:                                            │  │
│  │  Sequence → [Dependency Check, Redundancy Removal] → Final Seq    │  │
│  └───────────────────────┬───────────────────────────────────────────┘  │
└──────────────────────────┼───────────────────────────────────────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────────────────────┐
│  LAYER 4: Multi-Agent Execution                                         │
│                                                                           │
│  Agent Sequence: [booster, retriever, answering, verifier]              │
│                                                                           │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐        │
│  │   Booster    │─────▶│  Retriever    │─────▶│  Answering    │        │
│  │              │      │               │      │               │        │
│  │ Input: Query │      │ Input: Enhanced│    │ Input: Query +│        │
│  │ Output:      │      │      Query    │    │      Documents │        │
│  │ Enhanced Q   │      │ Output: Docs  │    │ Output: Answer │        │
│  └──────────────┘      └──────────────┘      └──────────────┘        │
│                                                      │                  │
│                                                      ▼                  │
│                                            ┌──────────────┐            │
│                                            │   Verifier   │            │
│                                            │              │            │
│                                            │ Input: Answer │            │
│                                            │      + Docs  │            │
│                                            │ Output:      │            │
│                                            │ Verified Ans │            │
│                                            └──────────────┘            │
└───────────────────────────┬───────────────────────────────────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────────────────────┐
│  LAYER 5: Response Generation                                            │
│  • Answer Synthesis                                                      │
│  • Citation Formatting                                                   │
│  • Confidence Calculation (SLM 30% + Answer 45% + Docs 25%)            │
│  • Multilingual Formatting (if needed)                                   │
└───────────────────────┬─────────────────────────────────────────────────┘
                        │
                        ▼
                    Final Response
                    (Answer + Citations + Confidence + Sources)
                        │
                        ▼
┌───────────────────────────────────────────────────────────────────────────┐
│  LAYER 6: Evaluation & Logging                                          │
│  • Calculate RAS (Routing Accuracy Score)                               │
│  • Calculate WAI (Workflow Appropriateness Index)                      │
│  • Log Interaction                                                      │
│  • Update Performance Metrics                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

**Figure 4: Complete Data Flow Architecture**

### 2.4 Component Interaction Matrix

The following table describes how components interact across layers:

| Source Component | Target Component | Interaction Type | Data Exchanged |
|------------------|------------------|-----------------|----------------|
| Query Input Handler | Language Detection | Synchronous | Raw Query Text |
| Language Detection | Query Preprocessor | Synchronous | Query + Language Tag |
| Query Preprocessor | Flan-T5 Orchestrator | Synchronous | Normalized Query |
| Flan-T5 Orchestrator | Workflow Optimizer | Synchronous | Agent Sequence |
| Workflow Optimizer | Agent Coordinator | Synchronous | Optimized Sequence |
| Agent Coordinator | Prompt Booster | Asynchronous | Query Context |
| Prompt Booster | Retriever Agent | Asynchronous | Enhanced Query |
| Retriever Agent | ChromaDB | Synchronous | Query Embedding → Documents |
| Retriever Agent | Answering Agent | Asynchronous | Query + Documents |
| Answering Agent | LLM (Groq/OpenAI) | Asynchronous | Query + Context → Answer |
| Answering Agent | Citation Verifier | Asynchronous | Answer + Documents |
| Citation Verifier | Response Formatter | Synchronous | Verified Answer |
| Response Formatter | User Interface | Synchronous | Final Response |
| All Agents | Evaluation Metrics | Asynchronous | Performance Data |
| Flan-T5 Orchestrator | Training Data Repo | Asynchronous | Query-Workflow Pairs |

### Layer 1: Core Infrastructure Architecture

The first layer of this framework is the **Core Infrastructure Layer**, which serves as the computational and storage foundation required for orchestration, agent execution, and knowledge management. PEARL operates on standard computing infrastructure (CPU/GPU-enabled systems), leveraging Python 3.10+ runtime environment with PyTorch for model inference. The system requires approximately 8GB RAM minimum (16GB recommended) for smooth operation, with optional GPU acceleration for faster Flan-T5 inference.

For persistent knowledge storage, **ChromaDB** serves as the vector database, storing embeddings of 21,000+ Indian legal documents including statutes, judgments, and case law. The database maintains document metadata, citation relationships, and cross-linking information. The **Model Storage** component manages Flan-T5-small model weights (~300MB), embedding models (sentence-transformers), and trained orchestrator checkpoints. **Configuration Management** handles API keys, model paths, agent settings, and system parameters through centralized configuration files. All infrastructure components enable PEARL to store, retrieve, and process legal information efficiently.

### Layer 2: Query Processing and Analysis Architecture

Transformation of raw user queries into structured, analyzable representations happens in this **Query Processing and Analysis Layer**. The **Query Input Handler** receives queries from multiple interfaces (Streamlit UI, FastAPI REST API, or CLI), validates input format, and performs basic sanitization. The **Language Detection Module** identifies the query language (English or one of 8 Indian languages) to route to appropriate processing pipelines. The **Query Preprocessor** normalizes text, handles special characters, and prepares queries for orchestration analysis.

The **Query Complexity Analyzer** performs initial assessment to determine if the query requires enhancement, multiple retrieval passes, or verification steps. This preprocessing is critical for the orchestrator to make informed routing decisions with high reliability. The query processing layer ensures that all inputs are properly formatted and ready for intelligent orchestration analysis.

### Layer 3: AI Orchestration and Cognitive Intelligence

This layer acts as the **cognitive backbone** of PEARL. It comprises three major sub-system components: the **Flan-T5 Orchestrator**, **Query Analysis Engine**, and **Workflow Optimizer**.

The **Flan-T5 Orchestrator** utilizes a quantized 80M-parameter Flan-T5-small model that analyzes each incoming query to assess complexity, classify reasoning type (factual, analytical, comparative, procedural), and predict the optimal agent sequence. The model processes query text through a sequence-to-sequence architecture, generating structured analysis including complexity level, confidence scores, and recommended agent workflow. As shown in the diagram below, when the orchestrator completes analysis, it outputs an agent sequence prediction that is then optimized and executed.

```
┌─────────────────────────────────────────────────────────────┐
│                    Query Input                               │
│              "What is Article 21?"                           │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│          Flan-T5 Orchestrator Analysis                       │
│  • Complexity: simple                                        │
│  • Reasoning: factual                                       │
│  • Confidence: 0.85                                         │
│  • Pattern: simple_factual                                   │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│          Agent Sequence Prediction                          │
│          [retriever, answering]                             │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│          Workflow Optimization                               │
│  • Dependency validation                                    │
│  • Redundant call removal                                   │
│  • Final sequence: [retriever, answering]                   │
└─────────────────────────────────────────────────────────────┘
```

**Figure 3: Orchestration Decision Flow**

The **Query Analysis Engine** performs detailed query understanding, extracting legal entities, identifying jurisdiction requirements, and determining if multilingual processing is needed. The analysis results are formatted as structured JSON containing complexity classification, reasoning type, estimated processing steps, and confidence scores.

The **Workflow Optimizer** post-processes predicted agent sequences to ensure dependency compliance (e.g., answering agent requires retriever to run first), removes redundant agent calls, and applies complexity-aware routing adjustments. This optimization ensures that workflows are both correct and efficient.

### Layer 4: System Logic and Control

All agent coordination and workflow execution are governed by this layer using an **event-driven architecture**. Each query analysis result, agent completion event, and error condition is converted into an internal system event. These events are prioritized and dispatched to the relevant agent controllers.

The **Agent Coordinator** manages the lifecycle of all five specialized agents:
- **Prompt Booster Agent**: Enhances vague queries using Flan-T5 SLM with legal terminology and context
- **Retriever Agent**: Performs semantic similarity search in ChromaDB, extracts citations, and cross-links related documents
- **Answering Agent**: Generates comprehensive answers using LLM (Groq/OpenAI) with citation-first policy
- **Citation Verifier Agent**: Validates claims against retrieved documents using semantic similarity
- **Multilingual Agent**: Translates queries and responses across 8 Indian languages

```
┌─────────────────────────────────────────────────────────────┐
│              Agent Execution Workflow                        │
│                                                              │
│  Query → Orchestrator → Agent Sequence → Execution          │
│                                                              │
│  [retriever, answering, verifier]                           │
│       │          │            │                             │
│       ▼          ▼            ▼                             │
│  Retrieve → Generate → Verify                               │
│  Documents   Answer    Citations                            │
└─────────────────────────────────────────────────────────────┘
```

**Figure 4: Multi-Agent Execution Flow**

The **Context Manager** maintains state across agent executions, passing retrieved documents from retriever to answering agent, and answer text from answering to verifier agent. The **Error Handler** implements comprehensive fallback mechanisms: if Flan-T5 orchestration fails, the system falls back to rule-based routing; if an agent fails, alternative agents or simplified workflows are attempted.

The **Performance Monitor** tracks latency, cost (zero for local SLM, minimal for optional cloud APIs), and success rates for each orchestration decision and agent execution.

### Layer 5: User Interaction and Output

This serves as PEARL's **expressive interface** for delivering legal research results. The **Response Formatter** structures answers with proper legal citations, confidence scores, and source document references. **Citation Presentation** ensures all legal claims are backed by verified sources, with proper formatting for legal documents (case names, statute sections, article numbers).

The **Confidence Calculator** combines multiple confidence signals: SLM orchestration confidence (30%), answer quality confidence (45%), and document support confidence (25%) to provide overall response reliability scores. **Error Messages** are user-friendly and informative, guiding users when queries cannot be processed or when results have low confidence.

The **Multilingual Output Handler** formats responses in the user's preferred language, preserving legal terminology accuracy while ensuring cultural and linguistic appropriateness. This layer ensures that all outputs are legally accurate, well-cited, and accessible to users.

### Layer 6: Data Storage and Knowledge

This layer handles all **persistent data** generated and used by PEARL. The **ChromaDB Vector Store** maintains embeddings of 21,000+ legal documents with metadata including document type (statute/judgment), jurisdiction, dates, and citation relationships. The **Training Data Repository** stores expert traces collected from GPT-4 teacher model, formatted as query-to-workflow pairs for knowledge distillation training.

**Interaction Logs** record all queries, orchestration decisions, agent sequences, and outcomes to support analysis and system improvement. The **Evaluation Metrics Database** stores RAS (Routing Accuracy Score) and WAI (Workflow Appropriateness Index) calculations for each orchestration decision, enabling continuous quality assessment.

The **Model Checkpoint Storage** maintains trained Flan-T5 orchestrator weights, allowing the system to load optimized models without retraining. All data remains locally stored to maintain complete privacy, with optional encrypted backups for production deployments.

## 3. System Behaviors

The proposed framework of PEARL follows an **event-driven behavioral model** with intelligent orchestration at its core. When the system initializes, the Flan-T5 orchestrator model loads into memory, ChromaDB vector database connects, and all five agents initialize their respective components (embedding models, LLM connections, translation models). The system enters a ready state, waiting for user queries.

When a user submits a legal query, PEARL enters **Orchestration Mode**: the Flan-T5 orchestrator analyzes the query, determines complexity and reasoning type, and predicts the optimal agent sequence. The workflow optimizer validates and refines this sequence, ensuring dependencies are satisfied and redundant calls are removed. The system then enters **Execution Mode**, sequentially invoking each agent in the predicted sequence, passing context between agents (retrieved documents → answering agent, generated answer → verifier agent).

If the query is in an Indian language, the **Multilingual Processing Mode** activates, translating the query to English for processing, then translating the response back to the original language. Throughout execution, the **Monitoring Mode** tracks performance metrics, calculates RAS/WAI scores, and logs all decisions for evaluation.

If any agent fails or returns low confidence, the **Fallback Mode** activates, attempting alternative workflows or simplified agent sequences. Upon completion, the system formats the final response with citations, confidence scores, and source references, then returns to ready state for the next query.

This behavioral pipeline ensures that users receive accurate, citation-backed legal information with optimal efficiency, while the system continuously learns and improves through evaluation metrics and training data collection.

## 4. Integrated Hardware–Software Architecture

An uninterrupted **cognitive orchestration loop** is formed by aligning hardware infrastructure and software components. As mentioned in the layers, hardware sensors (user input devices, network interfaces) capture queries, the query processing layer structures that input, the AI orchestration layer infers optimal agent sequences through Flan-T5 inference, the system logic layer executes agent workflows, the interaction layer exhibits formatted responses, and the storage layer records all interactions for learning and evaluation.

The overall proposed design supports **real-time operation** (2-5 seconds average query processing), **local privacy** (all orchestration decisions made locally, optional cloud APIs only for answer generation), **low computational cost** (500× cheaper than GPT-4 orchestration), and **high reliability** (comprehensive fallback mechanisms and error handling), making PEARL a practical and scalable orchestration framework for multi-agent legal RAG systems.

### 4.1 Hardware Requirements

- **CPU**: 4+ cores (8+ recommended) for parallel agent execution
- **RAM**: 8GB minimum (16GB recommended) for model loading and vector operations
- **Storage**: 10GB+ for models, ChromaDB, and training data
- **GPU**: Optional but recommended for faster Flan-T5 inference (CUDA-compatible)
- **Network**: Internet connection optional (only needed for cloud LLM APIs like Groq/OpenAI)

### 4.2 Software Stack

- **Python 3.10+**: Core runtime environment
- **PyTorch 2.0+**: Deep learning framework for Flan-T5
- **Transformers 4.30+**: Hugging Face model library
- **ChromaDB 0.4+**: Vector database for document storage
- **Sentence Transformers**: Embedding generation
- **FastAPI/Streamlit**: Web interface frameworks
- **asyncio**: Asynchronous agent coordination

### 4.3 Performance Characteristics

- **Orchestration Latency**: 15-30ms (local Flan-T5 inference)
- **Total Query Processing**: 2-5 seconds (including agent execution)
- **Cost per Decision**: $0.00 (local SLM) vs. $0.02+ (GPT-4 API)
- **Routing Accuracy**: 87.5% (RAS) compared to 92.9% (GPT-4)
- **Workflow Appropriateness**: 91.3% (WAI) comparable to GPT-4's 91.2%

---

## 5. Key Design Principles

### 5.1 Cost Efficiency
- Local SLM orchestration eliminates per-decision API costs
- Optional cloud APIs only for answer generation (not orchestration)
- 500× cost reduction compared to GPT-4 orchestration

### 5.2 Privacy Preservation
- All orchestration decisions made locally
- No query data sent to external services for routing
- ChromaDB and training data stored locally

### 5.3 Quality Maintenance
- Knowledge distillation preserves orchestration quality
- Comprehensive evaluation metrics (RAS, WAI)
- Workflow optimization ensures correctness

### 5.4 Modularity and Extensibility
- Each agent operates independently
- New agents can be added without system redesign
- Orchestrator can be swapped (Flan-T5, GPT-4, rule-based)

### 5.5 Reliability and Robustness
- Multiple fallback mechanisms
- Error handling at every layer
- Graceful degradation on failures

---

This system design demonstrates how PEARL achieves efficient, cost-effective, and privacy-preserving orchestration of multi-agent legal RAG systems through intelligent knowledge distillation and local SLM-based decision-making.

