#!/usr/bin/env python3
"""
Test Various Legal Queries
"""

from retriever_agent import RetrieverAgent

def test_queries():
    retriever = RetrieverAgent()
    
    queries = [
        'Article 21 right to life',
        'murder punishment IPC',
        'bail provisions criminal procedure',
        'constitutional fundamental rights'
    ]
    
    for query in queries:
        print(f'\n🔍 Query: "{query}"')
        results = retriever.retrieve(query)
        print(f'   Total: {results.total_retrieved} | Judgments: {len(results.judgments)} | Statutes: {len(results.statutes)}')
        if results.judgments:
            print(f'   Top judgment: {results.judgments[0].title[:60]}...')
        if results.statutes:
            print(f'   Top statute: {results.statutes[0].title[:60]}...')

if __name__ == "__main__":
    test_queries()
