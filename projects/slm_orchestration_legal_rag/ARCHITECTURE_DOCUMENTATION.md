# 🏗️ Agentic Legal RAG - Architecture Documentation

## 📖 **Complete System Architecture & Implementation Guide**

This document provides a comprehensive technical overview of the Agentic Legal RAG system, explaining how each component works, why it's designed that way, and how all pieces fit together.

## 🎯 **System Overview**

The Agentic Legal RAG system is a production-ready legal research assistant that uses a Small Language Model (SLM) as an orchestrator to manage multiple specialized agents. The system follows a citation-first policy, ensuring every legal claim is backed by verified evidence.

## 🏗️ **Architecture Diagram**

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                           │
├─────────────────┬─────────────────┬─────────────────────────────┤
│   Streamlit UI  │   FastAPI API   │        CLI Interface        │
└─────────────────┴─────────────────┴─────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      ORCHESTRATOR (SLM)                        │
│  • Query Enhancement Decision                                 │
│  • Agent Coordination                                         │
│  • Fallback Management                                        │
│  • Performance Tracking                                       │
└─────────────────────────────────────────────────────────────────┘
                                │
                    ┌───────────┼───────────┐
                    │           │           │
            ┌───────▼───┐ ┌─────▼─────┐ ┌───▼───┐
            │  Prompt   │ │ Retriever │ │Answering│
            │  Booster  │ │   Agent   │ │ Agent  │
            │   (SLM)   │ │           │ │ (LLM)  │
            └───────────┘ └───────────┘ └────────┘
                    │           │           │
            ┌───────▼───┐ ┌─────▼─────┐ ┌───▼───┐
            │Multilingual│ │Citation   │ │Dynamic│
            │   Agent    │ │ Verifier  │ │Updater│
            └───────────┘ └───────────┘ └────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DATA LAYER                                  │
│  • ChromaDB (Vector Store)                                    │
│  • SQLite (Conversations)                                     │
│  • File System (Documents)                                    │
└─────────────────────────────────────────────────────────────────┘
```

## 🔧 **Core Components Deep Dive**

### 1. **Orchestrator** (`orchestrator.py`)

**Purpose**: Central coordinator that manages all agents and implements decision logic.

**Key Responsibilities**:
- **Agent Management**: Initialize, monitor, and coordinate all agents
- **Query Processing**: Route queries through the appropriate agent pipeline
- **Decision Logic**: Determine when to use enhanced vs. original queries
- **Fallback Management**: Handle agent failures gracefully
- **Performance Tracking**: Monitor system performance and agent status

**Why This Design**:
- **Centralized Control**: Single point of coordination ensures consistent behavior
- **Modularity**: Easy to add/remove agents without affecting others
- **Fault Tolerance**: Graceful handling of agent failures
- **Monitoring**: Centralized performance tracking and logging

**Key Methods**:
```python
def process_query(self, user_query, language, user_context, session_id):
    # 1. Enhance query using Prompt Booster
    # 2. Retrieve documents using Retriever Agent
    # 3. Generate answer using Answering Agent
    # 4. Verify citations using Citation Verifier
    # 5. Return final result with confidence score
```

### 2. **Prompt Booster Agent** (`booster_agent.py`)

**Purpose**: Enhance user queries using Flan-T5 SLM for better legal retrieval.

**Key Features**:
- **SLM Enhancement**: Uses Flan-T5 for query rewriting
- **Rule-based Fallback**: Heuristic enhancement when SLM fails
- **Jurisdiction Awareness**: Adds Indian legal context
- **Legal Specificity**: Enhances vague queries with legal terms

**Why Flan-T5**:
- **Small Size**: Fast inference, low memory usage
- **Instruction Following**: Good at following enhancement prompts
- **Legal Context**: Can be fine-tuned for legal domain
- **Fallback Support**: Rule-based enhancement when model fails

**Enhancement Process**:
```python
def enhance_query(self, query, context):
    # 1. Check if SLM is available
    # 2. If yes: Use Flan-T5 for enhancement
    # 3. If no: Use rule-based enhancement
    # 4. Add jurisdiction context if missing
    # 5. Expand legal abbreviations
    # 6. Calculate confidence score
```

### 3. **Data Loader** (`data_loader.py`)

**Purpose**: Ingest legal documents from multiple sources and standardize them.

**Supported Sources**:
- **ILDC**: Indian Legal Documents Corpus
- **InLegalBERT**: Legal statutes from Hugging Face
- **Bare Acts**: Government legal documents (PDF/DOCX)
- **Indian Kanoon**: Live legal database via API

**Why Multiple Sources**:
- **Comprehensive Coverage**: Different types of legal documents
- **Redundancy**: Backup sources if one fails
- **Freshness**: Live updates from APIs
- **Quality**: Curated datasets vs. scraped content

**Data Processing Pipeline**:
```python
def load_all_sources(self):
    # 1. Load from ILDC (offline dataset)
    # 2. Load from InLegalBERT (Hugging Face)
    # 3. Load from Bare Acts (local files)
    # 4. Load from Indian Kanoon (API)
    # 5. Standardize all documents
    # 6. Return unified document list
```

### 4. **Index Builder** (`index_builder.py`)

**Purpose**: Process documents into searchable chunks with embeddings.

**Key Features**:
- **Legal Text Splitting**: Specialized chunking for legal documents
- **Metadata Extraction**: Extract sections, acts, courts, dates
- **Embedding Generation**: Create vector representations
- **ChromaDB Indexing**: Store in vector database

**Why This Approach**:
- **Legal-Specific Chunking**: Preserves legal document structure
- **Rich Metadata**: Enables filtering and cross-referencing
- **Vector Search**: Semantic similarity for better retrieval
- **Persistence**: ChromaDB provides durable storage

**Indexing Process**:
```python
def build_index(self, documents):
    # 1. Split documents into chunks (400-600 tokens)
    # 2. Extract metadata (sections, acts, courts)
    # 3. Generate embeddings using sentence-transformers
    # 4. Store in ChromaDB with metadata
    # 5. Create separate collections for statutes/judgments
```

### 5. **Retriever Agent** (`retriever_agent.py`)

**Purpose**: Retrieve relevant documents and create cross-links between statutes and judgments.

**Key Features**:
- **Semantic Search**: Vector similarity search
- **Cross-Linking**: Connect statutes with citing judgments
- **Citation Extraction**: Parse legal citations
- **Filtering**: Support for various document filters

**Why Cross-Linking**:
- **Legal Relationships**: Statutes and judgments are interconnected
- **Enhanced Retrieval**: Find related documents automatically
- **Comprehensive Answers**: Include both primary and secondary sources
- **Legal Accuracy**: Ensure answers are grounded in legal precedent

**Retrieval Process**:
```python
def retrieve(self, query, k, filters):
    # 1. Search in statutes collection
    # 2. Search in judgments collection
    # 3. Extract citations from retrieved documents
    # 4. Find cross-links between statutes and judgments
    # 5. Apply filters if specified
    # 6. Return ranked results with metadata
```

### 6. **Answering Agent** (`answering_agent.py`)

**Purpose**: Generate legal answers with proper citations using LLM.

**Key Features**:
- **Citation-First Policy**: Every claim must be cited
- **Legal Accuracy**: Specialized prompts for legal domain
- **Fallback Support**: Rule-based answers when LLM fails
- **Confidence Scoring**: Assess answer quality

**Why Citation-First**:
- **Legal Standards**: Legal research requires source attribution
- **Verifiability**: Users can verify claims independently
- **Trust**: Builds confidence in the system
- **Compliance**: Meets legal research standards

**Answer Generation Process**:
```python
def generate_answer(self, query, enhanced_query, retrieval_result):
    # 1. Format retrieved documents for LLM prompt
    # 2. Create legal-specific prompt template
    # 3. Generate answer using Groq LLM
    # 4. Parse citations from response
    # 5. Calculate confidence score
    # 6. Flag for human review if needed
```

### 7. **Citation Verifier** (`citation_verifier.py`)

**Purpose**: Verify that claims in answers are supported by retrieved documents.

**Key Features**:
- **Semantic Verification**: Use embeddings to check claim support
- **Keyword Verification**: Fallback using keyword matching
- **Confidence Scoring**: Assess verification quality
- **Human Review Flagging**: Flag low-confidence claims

**Why Verification is Critical**:
- **Legal Accuracy**: Prevents hallucination in legal context
- **Trust**: Ensures users can rely on answers
- **Compliance**: Meets legal research standards
- **Quality Control**: Maintains high answer quality

**Verification Process**:
```python
def verify_citations(self, answer_text, retrieved_documents):
    # 1. Extract claims from answer text
    # 2. For each claim, find supporting documents
    # 3. Calculate semantic similarity
    # 4. Use keyword matching as fallback
    # 5. Calculate verification confidence
    # 6. Flag claims requiring human review
```

### 8. **Multilingual Agent** (`multilingual_agent.py`)

**Purpose**: Support multiple Indian languages for broader accessibility.

**Supported Languages**:
- English, Hindi, Telugu, Tamil, Bengali, Gujarati, Marathi, Punjabi

**Key Features**:
- **Language Detection**: Automatically detect input language
- **Neural Translation**: Use Helsinki models for translation
- **Legal Terminology**: Preserve legal terms during translation
- **Fallback Support**: Rule-based translation when models fail

**Why Multilingual Support**:
- **Accessibility**: Serve diverse Indian population
- **Legal Context**: Legal documents exist in multiple languages
- **User Experience**: Natural language interaction
- **Compliance**: Government requirements for multilingual support

**Translation Process**:
```python
def process_query(self, query, target_language):
    # 1. Detect input language
    # 2. If not English, translate to English
    # 3. Process through normal pipeline
    # 4. Translate response back to user language
    # 5. Return multilingual result
```

### 9. **Dynamic Updater** (`updater.py`)

**Purpose**: Keep legal database current with latest legal developments.

**Update Sources**:
- **Supreme Court RSS**: Latest judgments
- **Legal Gazette**: Government notifications
- **Indian Kanoon API**: Live legal database
- **Custom Sources**: User-defined sources

**Why Dynamic Updates**:
- **Legal Currency**: Law changes frequently
- **Accuracy**: Ensure answers reflect current law
- **Completeness**: Include latest legal developments
- **Relevance**: Maintain system usefulness

**Update Process**:
```python
def update_all_sources(self):
    # 1. Check each configured source
    # 2. Fetch new documents
    # 3. Process and standardize
    # 4. Add to existing index
    # 5. Update metadata
    # 6. Log update results
```

### 10. **Evaluation System** (`evaluation.py`)

**Purpose**: Comprehensive evaluation of system performance across multiple metrics.

**Evaluation Metrics**:
- **Retrieval**: Precision@k, Recall@k, NDCG@k, MRR
- **Answer Quality**: BLEU, ROUGE, BERTScore
- **Legal Accuracy**: Citation accuracy, legal correctness
- **Human Evaluation**: GPT-based assessment

**Why Comprehensive Evaluation**:
- **Quality Assurance**: Ensure system meets standards
- **Performance Monitoring**: Track system improvements
- **Benchmarking**: Compare against other systems
- **Research**: Advance the field of legal AI

**Evaluation Process**:
```python
def run_comprehensive_evaluation(self, orchestrator, test_queries):
    # 1. Process each test query
    # 2. Calculate retrieval metrics
    # 3. Calculate answer quality metrics
    # 4. Calculate legal-specific metrics
    # 5. Generate comprehensive report
    # 6. Save results for analysis
```

## 🔄 **Data Flow Architecture**

### **Query Processing Pipeline**:

1. **User Input** → Language Detection → Translation (if needed)
2. **Query Enhancement** → SLM Enhancement → Rule-based Fallback
3. **Document Retrieval** → Vector Search → Cross-linking
4. **Answer Generation** → LLM Processing → Citation Extraction
5. **Citation Verification** → Semantic Check → Keyword Fallback
6. **Response Formatting** → Translation (if needed) → User Output

### **Index Building Pipeline**:

1. **Document Ingestion** → Multiple Sources → Standardization
2. **Text Processing** → Legal Chunking → Metadata Extraction
3. **Embedding Generation** → Vector Creation → Similarity Calculation
4. **Database Storage** → ChromaDB → Metadata Indexing
5. **Cross-Reference Building** → Citation Mapping → Relationship Storage

## 🛡️ **Error Handling & Resilience**

### **Multi-Level Error Handling**:

1. **Agent Level**: Each agent handles its own errors
2. **Orchestrator Level**: Coordinates fallbacks between agents
3. **System Level**: Global error handling and logging
4. **User Level**: Graceful error messages and recovery

### **Fallback Mechanisms**:

- **SLM Failure** → Rule-based enhancement
- **LLM Failure** → Template-based answers
- **Translation Failure** → Original language processing
- **Retrieval Failure** → Cached results or error message

## 📊 **Performance Optimization**

### **Caching Strategy**:
- **Query Results**: Cache frequent queries
- **Embeddings**: Cache document embeddings
- **Model Loading**: Lazy loading of models
- **Database**: ChromaDB persistence

### **Parallel Processing**:
- **Agent Coordination**: Parallel agent execution where possible
- **Batch Processing**: Batch embedding generation
- **Async Updates**: Background data updates
- **Concurrent Requests**: Handle multiple users

## 🔒 **Security & Privacy**

### **Data Protection**:
- **Local Processing**: Most processing happens locally
- **API Security**: Secure API key management
- **Session Isolation**: User sessions are isolated
- **Data Encryption**: Sensitive data is encrypted

### **Legal Compliance**:
- **Disclaimer**: Clear legal disclaimers
- **Source Attribution**: All sources are properly cited
- **Audit Trail**: Complete logging of system decisions
- **Human Review**: Low-confidence results flagged for review

## 🚀 **Deployment Architecture**

### **Production Deployment**:
- **FastAPI Server**: RESTful API for integration
- **Streamlit UI**: User-friendly web interface
- **CLI Tools**: Command-line utilities
- **Docker Support**: Containerized deployment

### **Scalability Considerations**:
- **Horizontal Scaling**: Multiple API instances
- **Database Sharding**: Distribute ChromaDB collections
- **Load Balancing**: Distribute user requests
- **Caching**: Redis for session and query caching

## 🔧 **Configuration Management**

### **Environment Variables**:
```bash
GROQ_API_KEY="your_groq_api_key"
OPENAI_API_KEY="your_openai_api_key"
KANOON_API_KEY="your_kanoon_api_key"
```

### **Configuration Files**:
- **config.py**: Central configuration
- **requirements.txt**: Python dependencies
- **Dockerfile**: Container configuration
- **docker-compose.yml**: Multi-service deployment

## 📈 **Monitoring & Observability**

### **Logging Strategy**:
- **Structured Logging**: JSON-formatted logs
- **Log Levels**: DEBUG, INFO, WARNING, ERROR
- **Log Rotation**: Automatic log file rotation
- **Centralized Logging**: Aggregated log collection

### **Metrics Collection**:
- **Performance Metrics**: Response times, throughput
- **Quality Metrics**: Accuracy, confidence scores
- **Usage Metrics**: Query patterns, user behavior
- **System Metrics**: CPU, memory, disk usage

## 🧪 **Testing Strategy**

### **Test Types**:
- **Unit Tests**: Individual component testing
- **Integration Tests**: Component interaction testing
- **End-to-End Tests**: Complete workflow testing
- **Performance Tests**: Load and stress testing

### **Test Coverage**:
- **Code Coverage**: 90%+ line coverage
- **Functional Coverage**: All features tested
- **Edge Cases**: Error conditions tested
- **Performance**: Response time validation

## 🔮 **Future Enhancements**

### **Planned Features**:
- **Fine-tuning**: Domain-specific model fine-tuning
- **Advanced Cross-linking**: Graph-based relationships
- **Real-time Collaboration**: Multi-user features
- **Mobile App**: Native mobile application

### **Research Directions**:
- **Legal Reasoning**: Advanced legal argumentation
- **Case Law Analysis**: Precedent analysis
- **Legal Prediction**: Outcome prediction
- **Multi-modal**: Image and document processing

---

This architecture documentation provides a comprehensive technical overview of the Agentic Legal RAG system. Each component is designed with specific purposes and considerations, working together to create a robust, scalable, and accurate legal research assistant.

