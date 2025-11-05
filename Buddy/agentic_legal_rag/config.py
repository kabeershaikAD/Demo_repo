"""
Configuration file for Agentic Legal RAG System
Contains all API keys, model settings, thresholds, and paths
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
    # Vector Database
    CHROMA_DB_PATH: str = "../Indian-Law-Voicebot/chroma_db_"
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
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    
    # OpenAI API (Fallback LLM) - OPTIONAL
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Indian Kanoon API (Incremental updates only) - OPTIONAL
    INDIAN_KANOON_API_KEY: str = os.getenv("INDIAN_KANOON_API_KEY", "YOUR_INDIAN_KANOON_API_KEY_HERE")
    KANOON_BASE_URL: str = "https://api.kanoon.ir"
    
    # Government APIs
    SUPREME_COURT_RSS: str = "https://main.sci.gov.in/rss/rss.xml"
    LEGAL_GAZETTE_URL: str = "https://egazette.nic.in"
    
    # Rate Limiting
    API_RATE_LIMIT: int = 100  # requests per minute

@dataclass
class UIConfig:
    """User interface configuration"""
    # Streamlit settings
    PAGE_TITLE: str = "Agentic Legal RAG"
    PAGE_ICON: str = "⚖️"
    LAYOUT: str = "wide"
    
    # Display settings
    MAX_DISPLAY_DOCS: int = 10
    SHOW_CONFIDENCE_SCORES: bool = True
    ENABLE_DARK_MODE: bool = False

@dataclass
class LoggingConfig:
    """Logging configuration"""
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: str = "logs/agentic_legal_rag.log"
    MAX_LOG_SIZE: int = 10 * 1024 * 1024  # 10MB
    BACKUP_COUNT: int = 5

@dataclass
class EvaluationConfig:
    """Evaluation and metrics configuration"""
    # Evaluation metrics
    ENABLE_EVALUATION: bool = True
    EVALUATION_DATASET: str = "data/evaluation/ground_truths.csv"
    
    # Metrics thresholds
    MIN_PRECISION: float = 0.7
    MIN_RECALL: float = 0.6
    MIN_F1_SCORE: float = 0.65

# Global Configuration Instance
class Config:
    """Main configuration class combining all configs"""
    
    def __init__(self):
        self.model = ModelConfig()
        self.database = DatabaseConfig()
        self.retrieval = RetrievalConfig()
        self.api = APIConfig()
        self.free_data = FreeDataConfig()  # FREE data sources
        self.ui = UIConfig()
        self.logging = LoggingConfig()
        self.evaluation = EvaluationConfig()
        
        # Error handling mode
        self.ERROR_MODE: str = "fail_safe"  # fail_safe, strict, permissive
        
        # Human-in-loop settings
        self.HUMAN_REVIEW_REQUIRED: bool = True
        self.MIN_CONFIDENCE_THRESHOLD: float = 0.7
        
        # Performance settings
        self.ENABLE_CACHING: bool = True
        self.CACHE_TTL: int = 3600  # 1 hour
        self.MAX_CONCURRENT_REQUESTS: int = 5

# Create global config instance
config = Config()

# Environment variable validation
def validate_api_keys() -> Dict[str, bool]:
    """Validate that required API keys are set"""
    validation_results = {
        "groq_api_key": bool(config.api.GROQ_API_KEY and config.api.GROQ_API_KEY != "YOUR_GROQ_API_KEY_HERE"),
        "openai_api_key": bool(config.api.OPENAI_API_KEY and config.api.OPENAI_API_KEY != "YOUR_OPENAI_API_KEY_HERE"),
        "kanoon_api_key": bool(config.api.INDIAN_KANOON_API_KEY and config.api.INDIAN_KANOON_API_KEY != "YOUR_INDIAN_KANOON_API_KEY_HERE"),
    }
    return validation_results

def get_missing_api_keys() -> list:
    """Get list of missing API keys"""
    validation = validate_api_keys()
    missing = [key for key, is_set in validation.items() if not is_set]
    return missing

# API Key Requirements Documentation
API_KEY_REQUIREMENTS = {
    "GROQ_API_KEY": {
        "description": "Required for primary LLM (Llama-3) responses",
        "how_to_get": "Sign up at https://console.groq.com/ and get API key",
        "required": True,
        "fallback": "OpenAI API key"
    },
    "OPENAI_API_KEY": {
        "description": "Fallback LLM and evaluation purposes",
        "how_to_get": "Sign up at https://platform.openai.com/ and get API key",
        "required": False,
        "fallback": None
    },
    "INDIAN_KANOON_API_KEY": {
        "description": "For accessing Indian legal database (optional)",
        "how_to_get": "Contact Indian Kanoon for API access",
        "required": False,
        "fallback": "Static legal documents"
    }
}

if __name__ == "__main__":
    print("Agentic Legal RAG Configuration")
    print("=" * 40)
    print(f"Embedding Model: {config.model.EMBEDDING_MODEL_NAME}")
    print(f"LLM Model: {config.model.LLM_ANSWERING_MODEL}")
    print(f"Database Path: {config.database.CHROMA_DB_PATH}")
    print(f"Free Data Sources: {len(config.free_data.HIGH_COURTS)} High Courts")
    print(f"API Keys Status: {validate_api_keys()}")