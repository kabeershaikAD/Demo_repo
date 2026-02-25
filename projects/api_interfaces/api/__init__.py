"""
API module for the Agentic Legal RAG system.
"""

from .main import app
from .models import QueryRequest, QueryResponse, DocumentUploadRequest

__all__ = [
    "app",
    "QueryRequest", 
    "QueryResponse",
    "DocumentUploadRequest"
]
