import sqlite3
import json
from datetime import datetime

# Add sample legal documents for POC demonstration
def add_sample_documents():
    conn = sqlite3.connect('indian_legal_db.sqlite')
    cursor = conn.cursor()
    
    # Sample legal documents
    sample_docs = [
        {
            'title': 'Article 21 of Indian Constitution',
            'content': 'Article 21 of the Indian Constitution guarantees the right to life and personal liberty. It states: "No person shall be deprived of his life or personal liberty except according to procedure established by law." This fundamental right is considered one of the most important provisions in the Constitution and has been interpreted broadly by the Supreme Court to include various aspects of human dignity and well-being.',
            'doc_type': 'constitution',
            'source': 'Constitution of India',
            'section': 'Article 21',
            'court': 'Supreme Court of India',
            'year': 1950
        },
        {
            'title': 'Right to Privacy - Puttaswamy Case',
            'content': 'In the landmark case of Justice K.S. Puttaswamy v. Union of India (2017), the Supreme Court declared that the right to privacy is a fundamental right under Article 21 of the Constitution. The nine-judge bench unanimously held that privacy is intrinsic to life and liberty, and forms the core of human dignity. This judgment has far-reaching implications for data protection and individual autonomy.',
            'doc_type': 'judgment',
            'source': 'Supreme Court Judgment',
            'section': 'Writ Petition (Civil) No. 494 of 2012',
            'court': 'Supreme Court of India',
            'year': 2017
        },
        {
            'title': 'Section 420 of Indian Penal Code',
            'content': 'Section 420 of the Indian Penal Code deals with cheating and dishonestly inducing delivery of property. It states: "Whoever cheats and thereby dishonestly induces the person deceived to deliver any property to any person, or to make, alter or destroy the whole or any part of a valuable security, or anything which is signed or sealed, and which is capable of being converted into a valuable security, shall be punished with imprisonment of either description for a term which may extend to seven years, and shall also be liable to fine."',
            'doc_type': 'statute',
            'source': 'Indian Penal Code',
            'section': 'Section 420',
            'court': 'Parliament of India',
            'year': 1860
        },
        {
            'title': 'Right to Education Act 2009',
            'content': 'The Right to Education Act 2009 makes education a fundamental right for all children between the ages of 6 and 14 years. The Act mandates free and compulsory education for all children in this age group. It also requires private schools to reserve 25% of their seats for children from economically weaker sections. The Act aims to ensure that every child has access to quality education regardless of their socio-economic background.',
            'doc_type': 'act',
            'source': 'Right to Education Act',
            'section': 'Section 3',
            'court': 'Parliament of India',
            'year': 2009
        },
        {
            'title': 'Consumer Protection Act 2019',
            'content': 'The Consumer Protection Act 2019 provides for protection of the interests of consumers and establishes authorities for timely and effective administration and settlement of consumer disputes. The Act defines consumer rights, establishes Consumer Protection Councils, and provides for Consumer Disputes Redressal Commissions at district, state, and national levels. It also includes provisions for product liability and unfair trade practices.',
            'doc_type': 'act',
            'source': 'Consumer Protection Act',
            'section': 'Section 2',
            'court': 'Parliament of India',
            'year': 2019
        }
    ]
    
    # Clear existing data
    cursor.execute("DELETE FROM legal_documents")
    
    # Insert sample documents
    for i, doc in enumerate(sample_docs):
        cursor.execute("""
            INSERT INTO legal_documents 
            (doc_id, title, content, doc_type, court, date, source, citations, keywords)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f"doc_{i+1}",
            doc['title'],
            doc['content'],
            doc['doc_type'],
            doc['court'],
            str(doc['year']),
            doc['source'],
            doc.get('section', ''),
            f"{doc['doc_type']}, {doc['source']}"
        ))
    
    conn.commit()
    conn.close()
    print(f"✅ Added {len(sample_docs)} sample legal documents for POC demonstration")

if __name__ == "__main__":
    add_sample_documents()
