"""
Pydantic models for API requests and responses.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class QueryRequest(BaseModel):
    """Request model for legal queries."""
    query: str = Field(..., description="The legal question to be answered")
    context: Optional[str] = Field(None, description="Additional context for the query")
    top_k: Optional[int] = Field(5, description="Number of documents to retrieve", ge=1, le=20)
    enable_citation_verification: Optional[bool] = Field(True, description="Enable citation verification")
    
    class Config:
        schema_extra = {
            "example": {
                "query": "What are the requirements for filing a patent application?",
                "context": "I am a startup founder looking to protect my intellectual property",
                "top_k": 5,
                "enable_citation_verification": True
            }
        }


class QueryResponse(BaseModel):
    """Response model for legal queries."""
    success: bool = Field(..., description="Whether the query was processed successfully")
    query: str = Field(..., description="Original query")
    enhanced_query: Optional[str] = Field(None, description="Enhanced version of the query")
    answer: Optional[str] = Field(None, description="Generated answer")
    citations: List[Dict[str, Any]] = Field(default_factory=list, description="Citations in the answer")
    confidence_score: Optional[float] = Field(None, description="Confidence score of the answer", ge=0.0, le=1.0)
    sources_used: int = Field(0, description="Number of sources used")
    retrieved_documents: List[Dict[str, Any]] = Field(default_factory=list, description="Retrieved documents")
    verification: Optional[Dict[str, Any]] = Field(None, description="Citation verification results")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Processing metadata")
    error: Optional[str] = Field(None, description="Error message if processing failed")
    timestamp: str = Field(..., description="Response timestamp")


class DocumentUploadRequest(BaseModel):
    """Request model for document upload."""
    documents: List[Dict[str, Any]] = Field(..., description="List of documents to upload")
    overwrite: Optional[bool] = Field(False, description="Whether to overwrite existing documents")
    
    class Config:
        schema_extra = {
            "example": {
                "documents": [
                    {
                        "content": "Section 1. This Act may be called the Patent Act, 1970...",
                        "title": "Patent Act 1970",
                        "doc_type": "statute",
                        "source": "patent_act_1970.pdf"
                    }
                ],
                "overwrite": False
            }
        }


class DocumentUploadResponse(BaseModel):
    """Response model for document upload."""
    success: bool = Field(..., description="Whether the upload was successful")
    documents_processed: int = Field(0, description="Number of documents processed")
    chunks_created: int = Field(0, description="Number of chunks created")
    error: Optional[str] = Field(None, description="Error message if upload failed")
    timestamp: str = Field(..., description="Response timestamp")


class SystemStatusResponse(BaseModel):
    """Response model for system status."""
    system_initialized: bool = Field(..., description="Whether the system is initialized")
    agents: Dict[str, Dict[str, Any]] = Field(..., description="Status of all agents")
    timestamp: str = Field(..., description="Response timestamp")


class HealthCheckResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(..., description="System status")
    version: str = Field(..., description="System version")
    timestamp: str = Field(..., description="Response timestamp")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    timestamp: str = Field(..., description="Error timestamp")
