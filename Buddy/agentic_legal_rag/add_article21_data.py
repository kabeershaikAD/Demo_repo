#!/usr/bin/env python3
"""
Add Article 21 specific content to the database
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from retriever_agent import RetrieverAgent
from data_loader import RetrievedDocument
import uuid

def add_article21_content():
    """Add comprehensive Article 21 content to the database"""
    
    print("Adding Article 21 content to database...")
    
    # Article 21 content
    article21_content = """
    Article 21 of the Indian Constitution states: "No person shall be deprived of his life or personal liberty except according to procedure established by law."
    
    Key Points about Article 21:
    
    1. Right to Life and Personal Liberty:
    - Protects the life and liberty of every person (citizen or non-citizen)
    - The state cannot take away life or liberty unless there is a legal procedure that is fair, just, and reasonable
    
    2. Historical Development:
    - Initially (before 1978), courts interpreted it narrowly: as long as there was a law passed by Parliament/State legislature, deprivation of life/liberty was valid
    - In Maneka Gandhi v. Union of India (1978), the Supreme Court gave Article 21 a wider interpretation: the procedure must be "just, fair, and reasonable", not arbitrary
    
    3. Rights Included under Article 21 (by judicial interpretation):
    Over time, the Supreme Court expanded Article 21 to include many derived rights, such as:
    - Right to live with dignity
    - Right to livelihood
    - Right to health and medical care
    - Right to privacy (Justice K.S. Puttaswamy case, 2017)
    - Right to free and compulsory education (later moved to Article 21-A)
    - Right to clean environment
    - Right against custodial torture
    - Right to shelter, and many more
    
    4. Nature of Article 21:
    - It is available to both citizens and foreigners
    - It cannot be suspended even during Emergency (unlike other fundamental rights such as Article 19)
    
    5. Important Cases:
    - Maneka Gandhi v. Union of India (1978) - Expanded the scope of Article 21
    - Justice K.S. Puttaswamy v. Union of India (2017) - Right to privacy as fundamental right
    - Olga Tellis v. Bombay Municipal Corporation (1985) - Right to livelihood
    - Francis Coralie Mullin v. Administrator, Union Territory of Delhi (1981) - Right to live with dignity
    
    Article 21 is considered the heart of fundamental rights, ensuring every person the right to live a life of dignity with freedom, unless restricted by a just and fair law.
    """
    
    # Create document
    doc = RetrievedDocument(
        doc_id=f"article_21_constitution_{uuid.uuid4().hex[:8]}",
        title="Article 21 of the Indian Constitution - Right to Life and Personal Liberty",
        content=article21_content.strip(),
        doc_type="statute",
        similarity_score=1.0,
        metadata={
            "article": "21",
            "constitution": "India",
            "fundamental_rights": True,
            "right_to_life": True,
            "right_to_liberty": True,
            "source": "Constitution of India"
        }
    )
    
    # Add to database
    retriever = RetrieverAgent()
    
    # Convert to the format expected by the database
    doc_dict = {
        "doc_id": doc.doc_id,
        "title": doc.title,
        "content": doc.content,
        "doc_type": doc.doc_type,
        "similarity_score": doc.similarity_score,
        "metadata": doc.metadata
    }
    
    try:
        # Add to ChromaDB
        retriever.vectorstore.add_documents([doc_dict])
        print("✅ Article 21 content added successfully!")
        
        # Test retrieval
        result = retriever.retrieve("article 21 constitution", k=3)
        all_docs = result.statutes + result.judgments
        print(f"\n📚 Test retrieval found {len(all_docs)} documents:")
        for i, doc in enumerate(all_docs):
            print(f"   {i+1}. {doc.title[:60]}... (similarity: {doc.similarity_score:.3f})")
        
    except Exception as e:
        print(f"❌ Error adding Article 21 content: {e}")

if __name__ == "__main__":
    add_article21_content()

