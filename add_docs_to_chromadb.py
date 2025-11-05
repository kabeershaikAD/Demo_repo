#!/usr/bin/env python3
"""
Add Sample Documents to ChromaDB for POC
This script adds the sample legal documents to ChromaDB so they can be retrieved
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Buddy', 'agentic_legal_rag'))

from retriever_agent import RetrieverAgent

def add_sample_to_chromadb():
    """Add sample documents to ChromaDB"""
    
    print("🚀 Adding sample documents to ChromaDB...")
    
    # Sample documents
    sample_docs = [
        {
            'title': 'Article 21 of Indian Constitution',
            'content': 'Article 21 of the Indian Constitution guarantees the right to life and personal liberty. It states: "No person shall be deprived of his life or personal liberty except according to procedure established by law." This fundamental right is considered one of the most important provisions in the Constitution and has been interpreted broadly by the Supreme Court to include various aspects of human dignity and well-being.',
            'doc_type': 'constitution',
            'source': 'Constitution of India',
            'doc_id': 'doc_article21',
            'court': 'Supreme Court of India',
            'date': '1950'
        },
        {
            'title': 'Right to Privacy - Puttaswamy Case',
            'content': 'In the landmark case of Justice K.S. Puttaswamy v. Union of India (2017), the Supreme Court declared that the right to privacy is a fundamental right under Article 21 of the Constitution. The nine-judge bench unanimously held that privacy is intrinsic to life and liberty, and forms the core of human dignity. This judgment has far-reaching implications for data protection and individual autonomy.',
            'doc_type': 'judgment',
            'source': 'Supreme Court Judgment',
            'doc_id': 'doc_puttaswamy',
            'court': 'Supreme Court of India',
            'date': '2017'
        },
        {
            'title': 'Section 420 of Indian Penal Code',
            'content': 'Section 420 of the Indian Penal Code deals with cheating and dishonestly inducing delivery of property. It states: "Whoever cheats and thereby dishonestly induces the person deceived to deliver any property to any person, or to make, alter or destroy the whole or any part of a valuable security, or anything which is signed or sealed, and which is capable of being converted into a valuable security, shall be punished with imprisonment of either description for a term which may extend to seven years, and shall also be liable to fine."',
            'doc_type': 'statute',
            'source': 'Indian Penal Code',
            'doc_id': 'doc_section420',
            'court': 'Parliament of India',
            'date': '1860'
        },
        {
            'title': 'Right to Education Act 2009',
            'content': 'The Right to Education Act 2009 makes education a fundamental right for all children between the ages of 6 and 14 years. The Act mandates free and compulsory education for all children in this age group. It also requires private schools to reserve 25% of their seats for children from economically weaker sections. The Act aims to ensure that every child has access to quality education regardless of their socio-economic background.',
            'doc_type': 'act',
            'source': 'Right to Education Act',
            'doc_id': 'doc_rte_2009',
            'court': 'Parliament of India',
            'date': '2009'
        },
        {
            'title': 'Consumer Protection Act 2019',
            'content': 'The Consumer Protection Act 2019 provides for protection of the interests of consumers and establishes authorities for timely and effective administration and settlement of consumer disputes. The Act defines consumer rights, establishes Consumer Protection Councils, and provides for Consumer Disputes Redressal Commissions at district, state, and national levels. It also includes provisions for product liability and unfair trade practices.',
            'doc_type': 'act',
            'source': 'Consumer Protection Act',
            'doc_id': 'doc_cpa_2019',
            'court': 'Parliament of India',
            'date': '2019'
        }
    ]
    
    # Initialize retriever agent (initializes in __init__)
    retriever = RetrieverAgent()
    
    # Check if vector_db is initialized
    if not retriever.vector_db:
        print("❌ ChromaDB not initialized. Trying to create new collection...")
        try:
            from langchain_chroma import Chroma
            from langchain_openai import OpenAIEmbeddings
            from config import config
            
            retriever.vector_db = Chroma(
                collection_name="legal_rag_collection",
                embedding_function=OpenAIEmbeddings(
                    model="text-embedding-3-small",
                    openai_api_key=config.api.OPENAI_API_KEY
                ),
                persist_directory="./chroma_db_"
            )
            print("✅ Created new ChromaDB collection")
        except Exception as e:
            print(f"❌ Failed to create ChromaDB: {e}")
            return
    
    # Add documents to ChromaDB
    print(f"\n📚 Adding {len(sample_docs)} documents to ChromaDB...")
    
    for doc in sample_docs:
        try:
            # Format document text
            doc_text = f"Title: {doc['title']}\n\nContent: {doc['content']}"
            
            # Add to ChromaDB using the vectorstore
            if retriever.vector_db:
                retriever.vector_db.add_texts(
                    texts=[doc_text],
                    metadatas=[{
                        "doc_id": doc['doc_id'],
                        "title": doc['title'],
                        "doc_type": doc['doc_type'],
                        "source": doc['source'],
                        "court": doc.get('court', ''),
                        "date": doc.get('date', '')
                    }],
                    ids=[doc['doc_id']]
                )
                print(f"  ✅ Added: {doc['title']}")
            else:
                print(f"  ❌ Vector DB not initialized")
        except Exception as e:
            print(f"  ❌ Error adding {doc['title']}: {e}")
            import traceback
            traceback.print_exc()
    
    # Test retrieval
    print(f"\n🔍 Testing retrieval...")
    test_query = "What is Article 21?"
    result = retriever.retrieve(test_query, k=3)
    
    total_docs = len(result.statutes) + len(result.judgments) if hasattr(result, 'statutes') else 0
    print(f"  ✅ Retrieved {total_docs} documents for test query")
    
    print(f"\n✅ Sample documents added to ChromaDB successfully!")

if __name__ == "__main__":
    add_sample_to_chromadb()
