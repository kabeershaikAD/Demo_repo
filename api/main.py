"""
FastAPI application for the Agentic Legal RAG system.
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import asyncio
from typing import Dict, Any
import uvicorn
from datetime import datetime

from .models import (
    QueryRequest, QueryResponse, DocumentUploadRequest, DocumentUploadResponse,
    SystemStatusResponse, HealthCheckResponse, ErrorResponse
)
from orchestrator import AgenticLegalRAG
from config import settings


# Global RAG system instance
rag_system: AgenticLegalRAG = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global rag_system
    
    # Startup
    print("Starting Agentic Legal RAG system...")
    rag_system = AgenticLegalRAG()
    
    # Initialize the system
    init_success = await rag_system.initialize()
    if not init_success:
        print("Failed to initialize RAG system")
        raise RuntimeError("Failed to initialize RAG system")
    
    print("RAG system initialized successfully")
    yield
    
    # Shutdown
    if rag_system:
        await rag_system.shutdown()
    print("RAG system shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Agentic Legal RAG System",
    description="A retrieval-augmented generation system for legal question answering",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_rag_system() -> AgenticLegalRAG:
    """Dependency to get the RAG system instance."""
    if rag_system is None:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    return rag_system


@app.get("/", response_model=HealthCheckResponse)
async def root():
    """Root endpoint with basic information."""
    return HealthCheckResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.now().isoformat()
    )


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint."""
    return HealthCheckResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.now().isoformat()
    )


@app.get("/status", response_model=SystemStatusResponse)
async def get_system_status(rag: AgenticLegalRAG = Depends(get_rag_system)):
    """Get the current status of the system and all agents."""
    try:
        status = await rag.get_system_status()
        return SystemStatusResponse(**status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    rag: AgenticLegalRAG = Depends(get_rag_system)
):
    """Process a legal query and return an answer."""
    try:
        # Update configuration based on request
        if request.enable_citation_verification is not None:
            settings.ENABLE_CITATION_VERIFICATION = request.enable_citation_verification
        
        # Process the query
        result = await rag.process_query(
            query=request.query,
            context=request.context or ""
        )
        
        # Convert to response model
        return QueryResponse(
            success=result["success"],
            query=result["query"],
            enhanced_query=result.get("enhanced_query"),
            answer=result.get("answer"),
            citations=result.get("citations", []),
            confidence_score=result.get("confidence_score"),
            sources_used=result.get("sources_used", 0),
            retrieved_documents=result.get("retrieved_documents", []),
            verification=result.get("verification"),
            metadata=result.get("metadata", {}),
            error=result.get("error"),
            timestamp=result.get("timestamp", datetime.now().isoformat())
        )
        
    except Exception as e:
        return QueryResponse(
            success=False,
            query=request.query,
            error=str(e),
            timestamp=datetime.now().isoformat()
        )


@app.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_documents(
    request: DocumentUploadRequest,
    background_tasks: BackgroundTasks,
    rag: AgenticLegalRAG = Depends(get_rag_system)
):
    """Upload and process legal documents."""
    try:
        # Process documents in background
        success = await rag.add_documents(request.documents)
        
        if success:
            # Calculate statistics
            chunks_created = sum(1 for doc in request.documents if doc.get("content"))
            
            return DocumentUploadResponse(
                success=True,
                documents_processed=len(request.documents),
                chunks_created=chunks_created,
                timestamp=datetime.now().isoformat()
            )
        else:
            return DocumentUploadResponse(
                success=False,
                error="Failed to process documents",
                timestamp=datetime.now().isoformat()
            )
            
    except Exception as e:
        return DocumentUploadResponse(
            success=False,
            error=str(e),
            timestamp=datetime.now().isoformat()
        )


@app.post("/documents/process")
async def process_documents_from_path(
    input_path: str,
    background_tasks: BackgroundTasks,
    rag: AgenticLegalRAG = Depends(get_rag_system)
):
    """Process documents from a file path."""
    try:
        from data_processing import DocumentProcessor
        
        processor = DocumentProcessor()
        chunks = await processor.process_documents(input_path)
        
        if chunks:
            # Add to vector store
            success = await rag.add_documents(chunks)
            
            if success:
                return {
                    "success": True,
                    "documents_processed": len(set(chunk["source"] for chunk in chunks)),
                    "chunks_created": len(chunks),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to add documents to vector store")
        else:
            raise HTTPException(status_code=400, detail="No documents found or processed")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/documents/clear")
async def clear_documents(rag: AgenticLegalRAG = Depends(get_rag_system)):
    """Clear all documents from the vector store."""
    try:
        success = await rag.clear_vector_store()
        
        if success:
            return {
                "success": True,
                "message": "All documents cleared successfully",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to clear documents")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents/{agent_name}")
async def get_agent_status(
    agent_name: str,
    rag: AgenticLegalRAG = Depends(get_rag_system)
):
    """Get the status of a specific agent."""
    try:
        agent = rag.get_agent(agent_name)
        
        if agent is None:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
        
        return {
            "agent_name": agent_name,
            "status": agent.get_status(),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc),
            timestamp=datetime.now().isoformat()
        ).dict()
    )


if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
