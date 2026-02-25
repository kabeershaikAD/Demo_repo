# 🗄️ Database Builders & Data Processing

## Overview

Scripts and utilities for building and maintaining the Indian legal database.

## Project Structure

```
database_builders/
├── scripts/                    # Database building scripts
│   ├── build_indian_legal_database.py
│   ├── indian_legal_database.py
│   ├── indian_kanoon_api.py
│   ├── dynamic_updater.py
│   ├── consolidate_chromadb.py
│   └── ...
├── data_processing/            # Data processing utilities
│   ├── document_processor.py
│   ├── legal_parser.py
│   └── text_chunker.py
└── databases/                 # Database files
    ├── indian_legal_db.sqlite
    └── vector_db/
```

## Key Scripts

### Building Database
```bash
python scripts/build_indian_legal_database.py
```

### Consolidating ChromaDB
```bash
python scripts/consolidate_chromadb.py
```

### Dynamic Updates
```bash
python scripts/dynamic_updater.py
```

## Related Projects

- **SLM Orchestration**: Uses databases built by these scripts
- **Voicebot**: Uses databases built by these scripts









