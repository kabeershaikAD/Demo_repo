#!/usr/bin/env python3
"""
Add Sample Legal Data to ChromaDB
"""

import sys
import os
from pathlib import Path

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_loader import LegalDocument
from retriever_agent import RetrieverAgent

def add_sample_legal_data():
    """Add sample legal documents to ChromaDB"""
    
    print("📚 Adding Sample Legal Data to ChromaDB")
    print("=" * 50)
    
    # Initialize retriever
    retriever = RetrieverAgent()
    
    # Sample legal documents
    sample_docs = [
        LegalDocument(
            doc_id="constitution_article_21",
            title="Article 21 - Right to Life and Personal Liberty",
            content="No person shall be deprived of his life or personal liberty except according to procedure established by law. This fundamental right under Article 21 of the Indian Constitution is one of the most important rights guaranteed to every citizen. It includes the right to live with human dignity, right to livelihood, right to health, right to education, and right to clean environment. The Supreme Court has interpreted this article expansively to include various rights that are essential for a meaningful life.",
            doc_type="constitution",
            source="Constitution of India",
            court="Supreme Court of India",
            date="1950-01-26",
            citations=["Article 21", "Constitution of India"],
            metadata={"article_number": "21", "part": "III", "fundamental_right": True}
        ),
        LegalDocument(
            doc_id="constitution_article_21a",
            title="Article 21A - Right to Education",
            content="The State shall provide free and compulsory education to all children of the age of six to fourteen years in such manner as the State may, by law, determine. This right was inserted by the 86th Constitutional Amendment Act, 2002. It makes education a fundamental right for children aged 6-14 years. The Right to Education Act, 2009 was enacted to give effect to this constitutional provision.",
            doc_type="constitution",
            source="Constitution of India",
            court="Supreme Court of India",
            date="2002-12-12",
            citations=["Article 21A", "Constitution of India", "Right to Education Act, 2009"],
            metadata={"article_number": "21A", "part": "III", "fundamental_right": True, "amendment": "86th"}
        ),
        LegalDocument(
            doc_id="patent_act_section_2j",
            title="Indian Patent Act, 1970 - Section 2(j) - Definition of Invention",
            content="Invention means a new product or process involving an inventive step and capable of industrial application. An invention must be novel, non-obvious, and useful to be patentable under Indian law. The inventive step must involve technical advancement as compared to existing knowledge or economic significance or both. The invention must be capable of being made or used in an industry.",
            doc_type="statute",
            source="Indian Patent Act, 1970",
            court="Parliament of India",
            date="1970-01-01",
            citations=["Section 2(j)", "Indian Patent Act, 1970"],
            metadata={"act": "Patent Act", "year": "1970", "section": "2(j)"}
        ),
        LegalDocument(
            doc_id="novartis_case_2013",
            title="Novartis AG v. Union of India - Supreme Court Judgment",
            content="The Supreme Court held that living organisms cannot be patented as they are products of nature and not human inventions. The court emphasized that patent law requires human intervention and inventive step. The judgment clarified that mere discovery of a new form of a known substance does not qualify for patent protection unless it shows enhanced therapeutic efficacy. This landmark judgment has significant implications for pharmaceutical patents in India.",
            doc_type="judgment",
            source="Supreme Court of India",
            court="Supreme Court of India",
            date="2013-04-01",
            citations=["Novartis AG v. Union of India", "AIR 2013 SC 1311"],
            metadata={"case_number": "Civil Appeal No. 2706-2716 of 2013", "bench": "2-judge", "landmark": True}
        ),
        LegalDocument(
            doc_id="criminal_procedure_section_438",
            title="Criminal Procedure Code - Section 438 - Anticipatory Bail",
            content="When any person has reason to believe that he may be arrested on an accusation of having committed a non-bailable offence, he may apply to the High Court or the Court of Session for a direction under this section. The court may direct that in the event of such arrest, he shall be released on bail. This provision allows for anticipatory bail to prevent unnecessary arrest and harassment.",
            doc_type="statute",
            source="Criminal Procedure Code, 1973",
            court="Parliament of India",
            date="1973-01-01",
            citations=["Section 438", "Criminal Procedure Code, 1973"],
            metadata={"act": "CrPC", "year": "1973", "section": "438", "topic": "anticipatory_bail"}
        )
    ]
    
    print(f"📄 Processing {len(sample_docs)} sample documents...")
    
    success_count = 0
    for doc in sample_docs:
        try:
            # Convert document to the format expected by ChromaDB
            doc_text = f"Title: {doc.title}\n\nContent: {doc.content}"
            
            # Add to ChromaDB
            retriever.vector_db.add_texts(
                texts=[doc_text],
                metadatas=[{
                    "doc_id": doc.doc_id,
                    "title": doc.title,
                    "doc_type": doc.doc_type,
                    "source": doc.source,
                    "court": doc.court or "",
                    "date": doc.date or "",
                    "citations": ", ".join(doc.citations) if doc.citations else ""
                }],
                ids=[doc.doc_id]
            )
            
            print(f"✅ Added: {doc.title}")
            success_count += 1
            
        except Exception as e:
            print(f"❌ Failed to add {doc.title}: {e}")
    
    print(f"\n🎉 Successfully added {success_count}/{len(sample_docs)} documents to ChromaDB!")
    
    # Test retrieval
    print("\n🔍 Testing retrieval...")
    try:
        test_query = "What are fundamental rights in Indian Constitution?"
        result = retriever.retrieve(test_query, k=3)
        print(f"✅ Retrieved {result.total_retrieved} documents for test query")
        if result.statutes:
            print(f"   - Statutes: {len(result.statutes)}")
        if result.judgments:
            print(f"   - Judgments: {len(result.judgments)}")
    except Exception as e:
        print(f"❌ Retrieval test failed: {e}")

if __name__ == "__main__":
    add_sample_legal_data()
