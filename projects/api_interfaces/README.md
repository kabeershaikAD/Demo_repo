# 🌐 API & Interfaces

## Overview

API endpoints and user interfaces for the legal RAG systems.

## Project Structure

```
api_interfaces/
├── api/                        # FastAPI endpoints
│   ├── main.py
│   └── models.py
└── ui/                         # User interfaces
    └── legal_ui.py            # Streamlit UI
```

## Usage

### Streamlit UI
```bash
# From project root
streamlit run projects/api_interfaces/ui/legal_ui.py
```

### FastAPI Server
```bash
# From project root
cd projects/api_interfaces/api
python main.py
```

## Related Projects

- **SLM Orchestration**: Main backend system
- **Database Builders**: Provides data for APIs









