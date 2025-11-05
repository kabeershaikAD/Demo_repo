# System Architecture

## Overview

The Agentic Legal RAG system follows a multi-agent architecture where specialized agents work together to provide comprehensive legal question answering. The system is designed to be modular, extensible, and research-oriented.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Agentic Legal RAG System                    │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │    API      │  │ Orchestrator│  │ Data        │  │ Config  │ │
│  │  Interface  │  │             │  │ Processing  │  │         │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘ │
├─────────────────────────────────────────────────────────────────┤
│                        Agent Layer                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │   Prompt    │  │  Retriever  │  │  Answering  │  │Citation │ │
│  │   Booster   │  │    Agent    │  │    Agent    │  │Verifier │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘ │
├─────────────────────────────────────────────────────────────────┤
│                      Infrastructure Layer                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │   Vector    │  │  Embedding  │  │    LLM      │  │Document │ │
│  │   Store     │  │   Models    │  │  Backends   │  │Parsers  │ │
│  │  (FAISS)    │  │(Transformers)│  │ (OpenAI)    │  │         │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Orchestrator (`orchestrator.py`)

The main orchestrator coordinates all agents and manages the overall workflow.

**Responsibilities:**
- Initialize and manage all agents
- Coordinate the query processing pipeline
- Handle error recovery and fallback strategies
- Provide system status and monitoring

**Key Methods:**
- `initialize()`: Initialize all agents
- `process_query()`: Main query processing pipeline
- `add_documents()`: Add documents to the system
- `get_system_status()`: Get system health status

### 2. Agent Layer

#### Prompt Booster Agent (`agents/prompt_booster_agent.py`)

Enhances vague legal queries into precise, searchable forms.

**Technology:** Flan-T5-small (Hugging Face)

**Responsibilities:**
- Query enhancement and clarification
- Legal entity extraction
- Search keyword generation
- Confidence scoring

**Key Methods:**
- `_enhance_query()`: Enhance query using Flan-T5
- `_extract_legal_entities()`: Extract legal terms and concepts
- `_generate_keywords()`: Generate search keywords

#### Retriever Agent (`agents/retriever_agent.py`)

Manages document retrieval from the vector store.

**Technology:** FAISS + sentence-transformers

**Responsibilities:**
- Vector store management
- Semantic similarity search
- Document ranking and filtering
- Index maintenance

**Key Methods:**
- `add_documents()`: Add documents to vector store
- `process()`: Retrieve relevant documents
- `_load_index()`: Load existing index
- `_save_index()`: Save index to disk

#### Answering Agent (`agents/answering_agent.py`)

Generates grounded answers using retrieved documents.

**Technology:** OpenAI GPT (configurable)

**Responsibilities:**
- Answer generation with context
- Citation extraction
- Confidence scoring
- Follow-up question generation

**Key Methods:**
- `_generate_answer()`: Generate answer using LLM
- `_extract_citations()`: Extract citations from answer
- `_calculate_confidence()`: Calculate answer confidence

#### Citation Verifier (`agents/citation_verifier.py`)

Ensures all outputs are backed by retrieved sources.

**Responsibilities:**
- Citation validation
- Unsupported claim detection
- Verification scoring
- Quality recommendations

**Key Methods:**
- `_verify_citations()`: Verify citations against sources
- `_find_unsupported_claims()`: Find unsupported claims
- `_calculate_verification_score()`: Calculate verification score

### 3. Data Processing Layer

#### Document Processor (`data_processing/document_processor.py`)

Main processor for legal documents.

**Responsibilities:**
- Document discovery and processing
- Metadata extraction
- Corpus statistics
- Batch processing

#### Legal Parser (`data_processing/legal_parser.py`)

Parses various legal document formats.

**Supported Formats:**
- PDF (using PyPDF2)
- DOCX (using python-docx)
- TXT (plain text)
- HTML (using BeautifulSoup)
- XML (using ElementTree)

**Responsibilities:**
- Format-specific parsing
- Legal metadata extraction
- Content cleaning and normalization
- Language detection

#### Text Chunker (`data_processing/text_chunker.py`)

Intelligent text segmentation for legal documents.

**Strategies:**
- Legal structure-based chunking
- Size-based chunking with overlap
- Sentence boundary preservation
- Legal entity preservation

**Responsibilities:**
- Intelligent text segmentation
- Chunk metadata generation
- Legal entity extraction
- Quality filtering

### 4. API Layer

#### FastAPI Application (`api/main.py`)

RESTful API for system interaction.

**Endpoints:**
- `GET /health`: Health check
- `GET /status`: System status
- `POST /query`: Process legal queries
- `POST /documents/upload`: Upload documents
- `POST /documents/process`: Process documents from path
- `DELETE /documents/clear`: Clear all documents
- `GET /agents/{name}`: Get agent status

#### Pydantic Models (`api/models.py`)

Data validation and serialization.

**Models:**
- `QueryRequest`: Query input validation
- `QueryResponse`: Query output format
- `DocumentUploadRequest`: Document upload format
- `SystemStatusResponse`: System status format

### 5. Configuration Layer

#### Settings (`config.py`)

Centralized configuration management.

**Configuration Areas:**
- Model settings (embedding, LLM, SLM)
- Vector database settings
- Agent behavior settings
- API settings
- Logging settings

## Data Flow

### Query Processing Pipeline

```
1. User Query
   ↓
2. Prompt Booster Agent
   ├─ Query Enhancement
   ├─ Entity Extraction
   └─ Keyword Generation
   ↓
3. Retriever Agent
   ├─ Query Embedding
   ├─ Vector Search
   └─ Document Ranking
   ↓
4. Answering Agent
   ├─ Context Preparation
   ├─ Answer Generation
   └─ Citation Extraction
   ↓
5. Citation Verifier
   ├─ Citation Validation
   ├─ Claim Verification
   └─ Quality Assessment
   ↓
6. Final Response
```

### Document Processing Pipeline

```
1. Document Input
   ↓
2. Legal Parser
   ├─ Format Detection
   ├─ Content Extraction
   └─ Metadata Extraction
   ↓
3. Text Chunker
   ├─ Structure Analysis
   ├─ Intelligent Segmentation
   └─ Chunk Metadata
   ↓
4. Retriever Agent
   ├─ Embedding Generation
   ├─ Index Update
   └─ Storage
```

## Technology Stack

### Core Technologies

- **Python 3.10+**: Main programming language
- **FastAPI**: Web framework for API
- **Pydantic**: Data validation and serialization
- **asyncio**: Asynchronous programming

### AI/ML Technologies

- **sentence-transformers**: Text embeddings
- **transformers**: Hugging Face transformers
- **Flan-T5-small**: Query enhancement
- **OpenAI GPT**: Answer generation
- **FAISS**: Vector similarity search

### Data Processing

- **PyPDF2**: PDF parsing
- **python-docx**: DOCX parsing
- **BeautifulSoup**: HTML parsing
- **ElementTree**: XML parsing

### Development Tools

- **pytest**: Testing framework
- **loguru**: Logging
- **uvicorn**: ASGI server

## Scalability Considerations

### Horizontal Scaling

- **Stateless Agents**: Agents can be deployed independently
- **Load Balancing**: API can be load balanced
- **Database Sharding**: Vector store can be sharded

### Vertical Scaling

- **GPU Acceleration**: Models can use GPU acceleration
- **Memory Optimization**: Efficient memory usage patterns
- **Caching**: Response caching for common queries

### Performance Optimization

- **Async Processing**: Non-blocking operations
- **Batch Processing**: Efficient document processing
- **Index Optimization**: Optimized vector search

## Security Considerations

### Data Protection

- **Input Validation**: All inputs are validated
- **Output Sanitization**: Outputs are sanitized
- **Error Handling**: Secure error messages

### API Security

- **Rate Limiting**: Prevent abuse (to be implemented)
- **Authentication**: User authentication (to be implemented)
- **Authorization**: Role-based access (to be implemented)

## Monitoring and Observability

### Logging

- **Structured Logging**: JSON-formatted logs
- **Log Levels**: Configurable log levels
- **Log Rotation**: Automatic log rotation

### Metrics

- **Performance Metrics**: Response times, throughput
- **Quality Metrics**: Accuracy, confidence scores
- **System Metrics**: Resource usage, health status

### Health Checks

- **Agent Health**: Individual agent status
- **System Health**: Overall system status
- **Dependency Health**: External service status

## Future Architecture Considerations

### Microservices

- **Agent Services**: Deploy agents as separate services
- **API Gateway**: Centralized API management
- **Service Discovery**: Dynamic service discovery

### Cloud Deployment

- **Containerization**: Docker containers
- **Orchestration**: Kubernetes deployment
- **Auto-scaling**: Dynamic scaling based on load

### Advanced Features

- **Streaming**: Real-time query processing
- **WebSockets**: Real-time communication
- **GraphQL**: Flexible query interface
