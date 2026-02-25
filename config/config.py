"""
Configuration management for Agentic Legal RAG system.
"""
from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings and configuration."""
    
    # Project paths
    PROJECT_ROOT: Path = Path(__file__).parent
    DATA_DIR: Path = PROJECT_ROOT / "data"
    VECTOR_DB_DIR: Path = PROJECT_ROOT / "vector_db"
    LOGS_DIR: Path = PROJECT_ROOT / "logs"
    
    # Model configurations
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    PROMPT_BOOSTER_MODEL: str = "google/flan-t5-small"
    
    # LLM configurations
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "YOUR_GROQ_API_KEY_HERE")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY_HERE")
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    TEMPERATURE: float = 0.1
    MAX_TOKENS: int = 1000
    
    # Vector database settings
    VECTOR_DB_TYPE: str = "faiss"  # faiss or chroma
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TOP_K_RETRIEVAL: int = 5
    
    # Agent settings
    ENABLE_CITATION_VERIFICATION: bool = True
    ENABLE_MULTILINGUAL: bool = False
    ENABLE_DYNAMIC_UPDATES: bool = False
    
    # API settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create necessary directories
        self.DATA_DIR.mkdir(exist_ok=True)
        self.VECTOR_DB_DIR.mkdir(exist_ok=True)
        self.LOGS_DIR.mkdir(exist_ok=True)


# Global settings instance
settings = Settings()


# Model configurations
MODEL_CONFIGS = {
    "flan-t5-small": {
        "model_name": "google/flan-t5-small",
        "max_length": 512,
        "temperature": 0.1,
        "do_sample": True
    },
    "gpt-3.5-turbo": {
        "model_name": "gpt-3.5-turbo",
        "temperature": 0.1,
        "max_tokens": 1000
    },
    "gpt-4": {
        "model_name": "gpt-4",
        "temperature": 0.1,
        "max_tokens": 2000
    }
}

# Legal document types
LEGAL_DOC_TYPES = {
    "statute": "Legal statutes and acts",
    "judgment": "Court judgments and decisions",
    "regulation": "Government regulations",
    "amendment": "Legal amendments",
    "precedent": "Legal precedents"
}

# Citation patterns for verification
CITATION_PATTERNS = {
    "case_citation": r"(?i)([A-Za-z]+ v\. [A-Za-z]+|\d+ [A-Za-z]+ \d+)",
    "statute_citation": r"(?i)(section \d+|art\. \d+|§\s*\d+)",
    "year_pattern": r"(19|20)\d{2}",
    "court_pattern": r"(?i)(supreme court|high court|district court|tribunal)"
}
