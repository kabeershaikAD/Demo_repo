# ChromaDB Consolidation Guide

## What This Script Does

The `consolidate_chromadb.py` script:
1. Reads all documents from multiple ChromaDB instances
2. Reads documents from SQLite database
3. Removes duplicates
4. Creates a single consolidated ChromaDB
5. Makes it compatible with your retriever agent

## ChromaDB Locations Consolidated

1. `./chroma_db_` (root directory)
2. `./Buddy/agentic_legal_rag/chroma_db_`
3. `./Buddy/Indian-Law-Voicebot/chroma_db_`
4. `./indian_legal_db.sqlite` (SQLite database)

## How to Run

```bash
# Activate virtual environment
legal_rag_env\Scripts\activate

# Run consolidation
python consolidate_chromadb.py
```

## Output

The consolidated database will be created at:
- `./chroma_db_consolidated/`

This uses the "langchain" collection name, which is compatible with your retriever agent.

## After Consolidation

Update your retriever agent to use the consolidated database:

**File:** `Buddy/agentic_legal_rag/retriever_agent.py`

**Change line 139:**
```python
# From:
self.chroma_db_path = "./chroma_db_"

# To:
self.chroma_db_path = "./chroma_db_consolidated"
```

Or update the path relative to where the retriever runs from.

## What Gets Consolidated

- All documents from all ChromaDB instances
- All documents from SQLite database
- Duplicates are automatically removed
- Metadata is preserved
- All documents are re-embedded and indexed

## Testing

After consolidation, the script will automatically test the database with a sample query "Article 21" to verify it works.


