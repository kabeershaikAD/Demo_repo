#!/usr/bin/env python3
"""
Simple Document to Vector Database Converter
Takes a document and creates embeddings in ChromaDB
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any
import logging

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_loader import LegalDocument, DocumentProcessor
from retriever_agent import RetrieverAgent
from config import config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentToVectorDB:
    """Convert documents to vector database"""
    
    def __init__(self):
        self.processor = DocumentProcessor()
        self.retriever = RetrieverAgent()
        
    def process_document(self, file_path: str, doc_type: str = "statute") -> LegalDocument:
        """Process a single document file"""
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Extract text based on file type
            if file_path.suffix.lower() == '.pdf':
                content = self.processor.extract_pdf_text(str(file_path))
            elif file_path.suffix.lower() == '.docx':
                content = self.processor.extract_docx_text(str(file_path))
            elif file_path.suffix.lower() == '.txt':
                content = self.processor.extract_text_file(str(file_path))
            else:
                raise ValueError(f"Unsupported file type: {file_path.suffix}")
            
            # Create legal document
            doc = LegalDocument(
                doc_id=f"{file_path.stem}_{doc_type}",
                title=file_path.stem,
                content=content,
                doc_type=doc_type,
                source=str(file_path),
                metadata={
                    "file_name": file_path.name,
                    "file_size": file_path.stat().st_size,
                    "file_type": file_path.suffix
                }
            )
            
            logger.info(f"Processed document: {doc.title}")
            return doc
            
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {e}")
            return None
    
    def add_document_to_chromadb(self, document: LegalDocument):
        """Add document to ChromaDB"""
        try:
            # Convert document to the format expected by ChromaDB
            doc_text = f"Title: {document.title}\n\nContent: {document.content}"
            
            # Add to ChromaDB
            self.retriever.vector_db.add_texts(
                texts=[doc_text],
                metadatas=[{
                    "doc_id": document.doc_id,
                    "title": document.title,
                    "doc_type": document.doc_type,
                    "source": document.source,
                    "court": document.court or "",
                    "date": document.date or "",
                    "citations": ", ".join(document.citations) if document.citations else ""
                }],
                ids=[document.doc_id]
            )
            
            logger.info(f"Added document to ChromaDB: {document.doc_id}")
            
        except Exception as e:
            logger.error(f"Error adding document to ChromaDB: {e}")
    
    def process_file(self, file_path: str, doc_type: str = "statute"):
        """Process a single file and add to vector database"""
        print(f"📄 Processing file: {file_path}")
        
        # Process document
        document = self.process_document(file_path, doc_type)
        if not document:
            print("❌ Failed to process document")
            return False
        
        # Add to ChromaDB
        self.add_document_to_chromadb(document)
        
        print(f"✅ Successfully added document to vector database!")
        print(f"   - ID: {document.doc_id}")
        print(f"   - Title: {document.title}")
        print(f"   - Type: {document.doc_type}")
        print(f"   - Content length: {len(document.content)} characters")
        
        return True

def main():
    """Main function for command line usage"""
    if len(sys.argv) < 2:
        print("Usage: python document_to_vectordb.py <file_path> [doc_type]")
        print("Example: python document_to_vectordb.py legal_doc.pdf statute")
        print("Supported file types: .pdf, .docx, .txt")
        print("Doc types: statute, judgment, amendment, constitution")
        return
    
    file_path = sys.argv[1]
    doc_type = sys.argv[2] if len(sys.argv) > 2 else "statute"
    
    converter = DocumentToVectorDB()
    success = converter.process_file(file_path, doc_type)
    
    if success:
        print("\n🎉 Document successfully added to vector database!")
        print("You can now query the document using the RAG system.")
    else:
        print("\n❌ Failed to process document.")

if __name__ == "__main__":
    main()
