# API Reference

## Overview

The Agentic Legal RAG system provides a RESTful API for legal question answering and document management.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, no authentication is required. For production use, implement appropriate authentication mechanisms.

## Endpoints

### Health Check

#### GET `/health`

Check system health status.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### GET `/status`

Get detailed system status including all agents.

**Response:**
```json
{
  "system_initialized": true,
  "agents": {
    "prompt_booster": {
      "name": "PromptBooster",
      "is_initialized": true,
      "config": {}
    },
    "retriever": {
      "name": "Retriever",
      "is_initialized": true,
      "config": {}
    },
    "answering": {
      "name": "Answering",
      "is_initialized": true,
      "config": {}
    },
    "citation_verifier": {
      "name": "CitationVerifier",
      "is_initialized": true,
      "config": {}
    }
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Query Processing

#### POST `/query`

Process a legal query and return an answer.

**Request Body:**
```json
{
  "query": "What are the requirements for patentability?",
  "context": "I am researching intellectual property law",
  "top_k": 5,
  "enable_citation_verification": true
}
```

**Parameters:**
- `query` (string, required): The legal question to be answered
- `context` (string, optional): Additional context for the query
- `top_k` (integer, optional): Number of documents to retrieve (1-20, default: 5)
- `enable_citation_verification` (boolean, optional): Enable citation verification (default: true)

**Response:**
```json
{
  "success": true,
  "query": "What are the requirements for patentability?",
  "enhanced_query": "What are the specific legal requirements and criteria for obtaining patent protection for an invention?",
  "answer": "According to the Patents Act 1970, the requirements for patentability include...",
  "citations": [
    {
      "text": "Section 2(j)",
      "type": "statute_reference",
      "position": 45
    }
  ],
  "confidence_score": 0.85,
  "sources_used": 3,
  "retrieved_documents": [
    {
      "content": "Section 2(j) defines invention as...",
      "source": "patents_act_1970.pdf",
      "doc_type": "statute"
    }
  ],
  "verification": {
    "verification_passed": true,
    "verification_score": 0.9,
    "verified_citations": [...],
    "unverified_citations": [],
    "unsupported_claims": []
  },
  "metadata": {
    "processing_time": "2024-01-01T12:00:00Z",
    "agents_used": ["prompt_booster", "retriever", "answering", "citation_verifier"],
    "booster_metadata": {...},
    "retriever_metadata": {...},
    "answering_metadata": {...}
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Document Management

#### POST `/documents/upload`

Upload and process legal documents.

**Request Body:**
```json
{
  "documents": [
    {
      "content": "Section 1. This Act may be called the Patents Act, 1970...",
      "title": "Patents Act 1970",
      "doc_type": "statute",
      "source": "patents_act_1970.pdf",
      "page_number": 1
    }
  ],
  "overwrite": false
}
```

**Parameters:**
- `documents` (array, required): List of documents to upload
- `overwrite` (boolean, optional): Whether to overwrite existing documents (default: false)

**Response:**
```json
{
  "success": true,
  "documents_processed": 1,
  "chunks_created": 5,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### POST `/documents/process`

Process documents from a file path.

**Request Body:**
```json
{
  "input_path": "/path/to/legal/documents"
}
```

**Response:**
```json
{
  "success": true,
  "documents_processed": 10,
  "chunks_created": 50,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### DELETE `/documents/clear`

Clear all documents from the vector store.

**Response:**
```json
{
  "success": true,
  "message": "All documents cleared successfully",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Agent Management

#### GET `/agents/{agent_name}`

Get the status of a specific agent.

**Parameters:**
- `agent_name` (string): Name of the agent (prompt_booster, retriever, answering, citation_verifier)

**Response:**
```json
{
  "agent_name": "prompt_booster",
  "status": {
    "name": "PromptBooster",
    "is_initialized": true,
    "config": {
      "model_name": "google/flan-t5-small",
      "temperature": 0.1
    }
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Error Handling

All endpoints return appropriate HTTP status codes:

- `200`: Success
- `400`: Bad Request (invalid input)
- `404`: Not Found (agent not found)
- `500`: Internal Server Error
- `503`: Service Unavailable (system not initialized)

Error responses follow this format:

```json
{
  "error": "Error message",
  "detail": "Detailed error information",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Rate Limiting

Currently, no rate limiting is implemented. For production use, implement appropriate rate limiting based on your requirements.

## CORS

CORS is enabled for all origins. For production use, configure appropriate CORS settings.

## Examples

### Python Client

```python
import requests

# Query the system
response = requests.post("http://localhost:8000/query", json={
    "query": "What is the definition of invention?",
    "context": "Patent law research",
    "top_k": 5
})

if response.status_code == 200:
    result = response.json()
    print(f"Answer: {result['answer']}")
    print(f"Confidence: {result['confidence_score']}")
else:
    print(f"Error: {response.json()['error']}")
```

### JavaScript Client

```javascript
const response = await fetch('http://localhost:8000/query', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    query: 'What is the definition of invention?',
    context: 'Patent law research',
    top_k: 5
  })
});

const result = await response.json();
console.log('Answer:', result.answer);
console.log('Confidence:', result.confidence_score);
```

### cURL

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the definition of invention?",
    "context": "Patent law research",
    "top_k": 5
  }'
```
