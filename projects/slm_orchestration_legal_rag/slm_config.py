# SLM Orchestration Configuration

# Model Configuration
MODEL_CONFIG = {
    "flan_t5_model": "google/flan-t5-small",
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "device": "cuda" if torch.cuda.is_available() else "cpu"
}

# API Keys (replace with your actual keys)
API_KEYS = {
    "openai_api_key": "your-openai-key-here",
    "groq_api_key": "your-groq-key-here",
    "kanoon_api_key": "your-kanoon-key-here"
}

# Orchestration Settings
ORCHESTRATION_CONFIG = {
    "max_agents_per_query": 5,
    "confidence_threshold": 0.7,
    "fallback_to_rules": True,
    "enable_metrics": True
}

# Evaluation Settings
EVALUATION_CONFIG = {
    "test_dataset_size": 200,
    "metrics_to_track": [
        "routing_accuracy",
        "sequence_accuracy", 
        "latency_ms",
        "cost_usd",
        "error_rate"
    ]
}
