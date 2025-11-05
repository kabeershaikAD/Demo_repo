"""
Setup script for SLM Orchestration Framework
Installs dependencies and initializes the system
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ required")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
    return True

def install_dependencies():
    """Install required dependencies"""
    
    # Core dependencies
    dependencies = [
        "torch>=2.0.0",
        "transformers>=4.35.0", 
        "sentencepiece>=0.1.99",
        "sentence-transformers>=2.2.2",
        "openai>=1.0.0",
        "numpy>=1.24.0",
        "pandas>=2.0.0",
        "scikit-learn>=1.3.0",
        "chromadb>=0.4.15",
        "faiss-cpu>=1.7.4",
        "streamlit>=1.28.0",
        "fastapi>=0.104.0",
        "uvicorn>=0.24.0",
        "pydantic>=2.5.0",
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.0",
        "python-dotenv>=1.0.0",
        "tqdm>=4.66.0",
        "pytest>=7.4.0"
    ]
    
    for dep in dependencies:
        if not run_command(f"pip install {dep}", f"Installing {dep}"):
            return False
    
    return True

def create_directories():
    """Create necessary directories"""
    directories = [
        "logs",
        "evaluation",
        "core",
        "orchestrators", 
        "agents",
        "data",
        "models"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")

def create_config_file():
    """Create configuration file"""
    config_content = '''# SLM Orchestration Configuration

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
'''
    
    with open("slm_config.py", "w") as f:
        f.write(config_content)
    
    print("✅ Created slm_config.py")

def test_installation():
    """Test if installation was successful"""
    test_imports = [
        "torch",
        "transformers", 
        "sentencepiece",
        "sentence_transformers",
        "openai",
        "numpy",
        "pandas",
        "chromadb",
        "faiss"
    ]
    
    print("\n🧪 Testing installation...")
    
    for module in test_imports:
        try:
            __import__(module)
            print(f"✅ {module} imported successfully")
        except ImportError as e:
            print(f"❌ Failed to import {module}: {e}")
            return False
    
    return True

def main():
    """Main setup function"""
    print("🚀 Setting up SLM Orchestration Framework")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create directories
    print("\n📁 Creating directories...")
    create_directories()
    
    # Install dependencies
    print("\n📦 Installing dependencies...")
    if not install_dependencies():
        print("❌ Dependency installation failed")
        sys.exit(1)
    
    # Create config file
    print("\n⚙️ Creating configuration...")
    create_config_file()
    
    # Test installation
    if not test_installation():
        print("❌ Installation test failed")
        sys.exit(1)
    
    print("\n✅ SLM Orchestration Framework setup complete!")
    print("\nNext steps:")
    print("1. Update API keys in slm_config.py")
    print("2. Run: python slm_orchestration_app.py --demo")
    print("3. Run evaluation: python evaluation/run_orchestration_evaluation.py")

if __name__ == "__main__":
    main()
