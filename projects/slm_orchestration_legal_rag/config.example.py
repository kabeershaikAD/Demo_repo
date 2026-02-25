"""
Configuration file for Agentic Legal RAG System
Contains all API keys, model settings, thresholds, and paths

COPY THIS FILE TO config.py AND ADD YOUR API KEYS
"""

import os
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class ModelConfig:
    """Model configuration settings"""
    # Embedding Models
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    LEGAL_EMBEDDING_MODEL: str = "law-ai/InLegalBERT"  # Fallback if available
    
    # SLM for Prompt Boosting (Note: Rule-based enhancement recommended for Indian legal context)
    BOOSTER_MODEL_NAME: str = "google/flan-t5-small"
    BOOSTER_FORCE_RULE_BASED: bool = True  # Use rule-based enhancement for better Indian legal context
    
    # LLM for Answering
    LLM_ANSWERING_MODEL: str = "llama-3.1-8b-instant"  # Groq model
    OPENAI_MODEL: str = "gpt-3.5-turbo"  # OpenAI fallback
    
    # Translation Models
    TRANSLATION_MODEL: str = "Helsinki-NLP/opus-mt-en-hi"  # English to Hindi
    INDIC_TRANS_MODEL: str = "ai4bharat/IndicTrans2"  # Multi-language support

@dataclass
class DatabaseConfig:
    """Database and storage configuration"""
    # Vector Database (updated path after reorganization)
    CHROMA_DB_PATH: str = "./chroma_db_consolidated"  # Use consolidated DB in project root
    STATUTES_COLLECTION: str = "statutes"
    JUDGMENTS_COLLECTION: str = "judgments"
    
    # SQLite Database
    SQLITE_DB_PATH: str = "./law_buddy_agentic.db"
    
    # Data Directories
    DATA_DIR: str = "./data"
    BARE_ACTS_DIR: str = "./data/bare_acts"
    ILDC_DIR: str = "./data/ildc"
    LOGS_DIR: str = "./logs"

@dataclass
class RetrievalConfig:
    """Retrieval and search configuration"""
    # Retrieval Parameters
    RETRIEVAL_K: int = 10
    SIMILARITY_THRESHOLD: float = 0.7
    CROSS_LINK_THRESHOLD: float = 0.8
    
    # Chunking Parameters
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 100
    
    # Citation Verification
    CITATION_VERIFICATION_ENABLED: bool = True
    CITATION_VERIFICATION_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    CITATION_THRESHOLD: float = 0.7
    MIN_CITATION_CONFIDENCE: float = 0.6

@dataclass
class FreeDataConfig:
    """Free data sources configuration - NO API KEYS REQUIRED"""
    # ILDC Dataset (35k+ judgments) - FREE
    ILDC_DATASET_URL: str = "https://zenodo.org/record/4599830/files/ILDC_single.zip"
    ILDC_DATASET_SIZE: str = "~2GB"
    ILDC_DATASET_DESCRIPTION: str = "Indian Legal Documents Corpus - 35k+ judgments"
    
    # Legislative.gov.in (Official documents) - FREE
    LEGISLATIVE_GOV_IN_URL: str = "https://legislative.gov.in/"
    LEGISLATIVE_SECTIONS: list = None
    
    # Supreme Court RSS - FREE
    SUPREME_COURT_RSS_URL: str = "https://main.sci.gov.in/rss/judgments.xml"
    
    # High Court Websites - FREE
    HIGH_COURTS: dict = None
    
    def __post_init__(self):
        if self.LEGISLATIVE_SECTIONS is None:
            self.LEGISLATIVE_SECTIONS = ['constitution', 'bare-acts', 'amendments']
        
        if self.HIGH_COURTS is None:
            self.HIGH_COURTS = {
                'madras': 'https://www.hc.tn.gov.in/judis/',
                'delhi': 'https://delhihighcourt.nic.in/',
                'bombay': 'https://bombayhighcourt.nic.in/',
                'calcutta': 'https://www.calcuttahighcourt.gov.in/',
                'karnataka': 'https://karnatakajudiciary.kar.nic.in/'
            }

@dataclass
class APIConfig:
    """API keys and external service configuration"""
    # Groq API (Primary LLM) - REQUIRED for full functionality
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "YOUR_GROQ_API_KEY_HERE")
    
    # OpenAI API (Fallback LLM) - OPTIONAL
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY_HERE")
    
    # Indian Kanoon API (Incremental updates only) - OPTIONAL
    INDIAN_KANOON_API_KEY: str = os.getenv("INDIAN_KANOON_API_KEY", "YOUR_INDIAN_KANOON_API_KEY_HERE")
    KANOON_BASE_URL: str = "https://api.kanoon.ir"
    
    # Government APIs
    SUPREME_COURT_RSS: str = "https://main.sci.gov.in/rss/rss.xml"

# Create config instance
model = ModelConfig()
database = DatabaseConfig()
retrieval = RetrievalConfig()
free_data = FreeDataConfig()
api = APIConfig()

# Main config object
class Config:
    def __init__(self):
        self.model = model
        self.database = database
        self.retrieval = retrieval
        self.free_data = free_data
        self.api = api

config = Config()

def validate_api_keys() -> Dict[str, bool]:
    """Validate that required API keys are set"""
    return {
        "groq_api_key": bool(config.api.GROQ_API_KEY and config.api.GROQ_API_KEY != "YOUR_GROQ_API_KEY_HERE"),
        "openai_api_key": bool(config.api.OPENAI_API_KEY and config.api.OPENAI_API_KEY != "YOUR_OPENAI_API_KEY_HERE"),
        "kanoon_api_key": bool(config.api.INDIAN_KANOON_API_KEY and config.api.INDIAN_KANOON_API_KEY != "YOUR_INDIAN_KANOON_API_KEY_HERE"),
    }

def get_missing_api_keys() -> list:
    """Get list of missing API keys"""
    validation = validate_api_keys()
    return [key for key, valid in validation.items() if not valid]

API_KEY_REQUIREMENTS = {
    "GROQ_API_KEY": {
        "required": True,
        "description": "Primary LLM provider for answering agent",
        "how_to_get": "Sign up at https://console.groq.com/ and get API key",
        "free_tier": "14,400 requests/day",
        "fallback": "OpenAI API key"
    },
    "OPENAI_API_KEY": {
        "required": False,
        "description": "Fallback LLM provider",
        "how_to_get": "Sign up at https://platform.openai.com/ and get API key",
        "free_tier": "No free tier",
        "fallback": None
    },
    "INDIAN_KANOON_API_KEY": {
        "required": False,
        "description": "For incremental legal document updates",
        "how_to_get": "Contact Indian Kanoon for API access",
        "free_tier": "Limited",
        "fallback": "Use free data sources (ILDC, Legislative.gov.in)"
    }
}

if __name__ == "__main__":
    print(f"API Keys Status: {validate_api_keys()}")
    missing = get_missing_api_keys()
    if missing:
        print(f"Missing API Keys: {missing}")
        print("\nAPI Key Requirements:")
        for key, info in API_KEY_REQUIREMENTS.items():
            print(f"\n{key}:")
            print(f"  Required: {info['required']}")
            print(f"  Description: {info['description']}")
            print(f"  How to get: {info['how_to_get']}")


