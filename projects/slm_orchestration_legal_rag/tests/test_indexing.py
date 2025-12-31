"""
Test suite for indexing functionality
"""

import pytest
import tempfile
import os
from pathlib import Path

from index_builder import IndexManager, LegalTextSplitter, EmbeddingGenerator
from data_loader import LegalDocument, DataLoader

class TestLegalTextSplitter:
    """Test legal text splitter"""
    
    def test_split_document(self):
        """Test document splitting"""
        splitter = LegalTextSplitter(chunk_size=100, chunk_overlap=20)
        
        # Create test document
        doc = LegalDocument(
            doc_id="test_1",
            title="Test Document",
            content="This is a test legal document. " * 20,  # Long content
            doc_type="statute",
            source="test"
        )
        
        chunks = splitter.split_document(doc)
        
        assert len(chunks) > 1
        assert all(len(chunk[0]) <= 100 for chunk in chunks)
        assert all(chunk[1].doc_id == "test_1" for chunk in chunks)
    
    def test_extract_section(self):
        """Test section extraction"""
        splitter = LegalTextSplitter()
        
        text = "Section 302 of the Indian Penal Code deals with murder."
        section = splitter._extract_section(text)
        assert section == "302"
        
        text = "Article 21 of the Constitution guarantees fundamental rights."
        section = splitter._extract_section(text)
        assert section == "21"
    
    def test_extract_act(self):
        """Test act extraction"""
        splitter = LegalTextSplitter()
        
        text = "The Indian Penal Code 1860 defines various offences."
        act = splitter._extract_act(text)
        assert "Indian Penal Code" in act or "1860" in act

class TestEmbeddingGenerator:
    """Test embedding generator"""
    
    def test_generate_embeddings(self):
        """Test embedding generation"""
        generator = EmbeddingGenerator()
        
        texts = ["This is a test.", "Another test sentence."]
        embeddings = generator.generate_embeddings(texts)
        
        assert len(embeddings) == 2
        assert embeddings.shape[1] > 0  # Should have embedding dimension
    
    def test_generate_single_embedding(self):
        """Test single embedding generation"""
        generator = EmbeddingGenerator()
        
        text = "Test legal content"
        embedding = generator.generate_single_embedding(text)
        
        assert len(embedding) > 0

class TestIndexManager:
    """Test index manager"""
    
    def test_build_from_documents(self):
        """Test building index from documents"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test documents
            documents = [
                LegalDocument(
                    doc_id="test_1",
                    title="Test Statute",
                    content="This is a test statute about legal matters.",
                    doc_type="statute",
                    source="test"
                ),
                LegalDocument(
                    doc_id="test_2",
                    title="Test Judgment",
                    content="This is a test judgment from the Supreme Court.",
                    doc_type="judgment",
                    source="test"
                )
            ]
            
            # Create index manager with temp directory
            index_manager = IndexManager()
            index_manager.index_builder.db_path = temp_dir
            
            # Build index
            stats = index_manager.build_from_documents(documents)
            
            assert stats['total_chunks'] > 0
            assert stats['statutes_chunks'] > 0
            assert stats['judgments_chunks'] > 0
    
    def test_get_index_stats(self):
        """Test getting index statistics"""
        with tempfile.TemporaryDirectory() as temp_dir:
            index_manager = IndexManager()
            index_manager.index_builder.db_path = temp_dir
            
            stats = index_manager.get_index_stats()
            assert 'statutes_count' in stats
            assert 'judgments_count' in stats
            assert 'total_count' in stats

class TestDataLoader:
    """Test data loader"""
    
    def test_legal_document_creation(self):
        """Test LegalDocument creation"""
        doc = LegalDocument(
            doc_id="test_1",
            title="Test Document",
            content="Test content",
            doc_type="statute",
            source="test"
        )
        
        assert doc.doc_id == "test_1"
        assert doc.title == "Test Document"
        assert doc.doc_type == "statute"
        assert doc.citations == []
        assert doc.metadata == {}
    
    def test_bare_acts_loader(self):
        """Test bare acts loader"""
        loader = DataLoader()
        
        # Test with empty directory
        with tempfile.TemporaryDirectory() as temp_dir:
            docs = loader.bare_acts_loader.load_from_directory(temp_dir)
            assert len(docs) == 0

if __name__ == "__main__":
    pytest.main([__file__])

