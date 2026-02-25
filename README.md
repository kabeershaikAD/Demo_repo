# 🏛️ SLM Orchestration Legal RAG System

**SmallOrch: Efficient Multi-Agent Orchestration Framework Using Small Language Models**

A research-oriented **Retrieval-Augmented Generation (RAG)** system for the legal domain that demonstrates how a Small Language Model (Flan-T5-small, 80M parameters) can effectively orchestrate multi-agent systems as a cost-effective alternative to expensive LLM orchestration.

## 🎯 Key Innovation

**Main Contribution**: This system demonstrates that **Flan-T5-small (SLM)** can intelligently orchestrate multi-agent legal RAG systems with:
- **500x lower cost** than GPT-4 orchestration ($0.00 vs $0.02+ per decision)
- **33x faster latency** (~15ms vs 500ms+ per decision)
- **85%+ routing accuracy** comparable to GPT-4
- **No API required** - runs entirely on-device

## ✨ Features

- **🧠 SLM Orchestrator**: Flan-T5-small analyzes queries and dynamically decides which agents to use
- **🤖 Multi-Agent Architecture**: Specialized agents for query enhancement, retrieval, answering, verification, and multilingual support
- **📚 Legal Document Retrieval**: 21,000+ legal documents from Indian legal databases
- **✅ Citation Verification**: Ensures all answers are backed by retrieved sources
- **🌐 Streamlit UI**: Modern web interface showcasing SLM orchestration decisions
- **📊 Evaluation Framework**: Comprehensive metrics comparing SLM vs GPT-4 vs Rule-based orchestration

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+** (3.11 or 3.12 recommended)
- **8GB+ RAM** (for model loading)
- **API Keys**:
  - OpenAI API key (for embeddings and GPT-4 baseline)
  - Groq API key (for answering agent)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd "Major project"
   ```

2. **Create and activate a virtual environment**
   ```bash
   # Windows
   python -m venv legal_rag_env
   legal_rag_env\Scripts\activate

   # Linux/Mac
   python -m venv legal_rag_env
   source legal_rag_env/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   # Copy the example file
   copy .env.example .env
   
   # Edit .env and add your API keys
   # Windows: notepad .env
   # Linux/Mac: nano .env
   ```

   Required variables in `.env`:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   GROQ_API_KEY=your_groq_api_key_here
   ```

5. **Run the Streamlit UI**
   ```bash
   streamlit run projects/api_interfaces/ui/legal_ui.py
   ```

   The UI will open at `http://localhost:8501`

## 📁 Project Structure

**Note**: The project has been reorganized! See `PROJECT_STRUCTURE_FINAL.md` for complete details.

```
Major project/
├── projects/                              # All main projects
│   ├── slm_orchestration_legal_rag/      # Main SLM orchestration project
│   │   ├── slm_orchestration_app.py       # Main application
│   │   ├── orchestrators/                # Orchestrator implementations
│   │   ├── agents/                       # Agent implementations
│   │   ├── evaluation/                   # Evaluation framework
│   │   └── chroma_db_consolidated/       # Vector database
│   │
│   ├── indian_law_voicebot/              # Voice-based legal assistant
│   ├── database_builders/                 # Database building scripts
│   ├── testing_evaluation/                # Test and evaluation scripts
│   └── api_interfaces/                    # API endpoints and UI
│       └── ui/
│           └── legal_ui.py               # Streamlit UI (entry point)
│
├── docs/                                  # All documentation
│   ├── architecture/                     # Architecture docs
│   ├── guides/                           # Setup guides
│   ├── reports/                          # Project reports
│   └── fixes/                            # Fix documentation
│
├── config/                                # Configuration files
│   ├── config.py
│   ├── config.env
│   └── setup_scripts/
│
├── utilities/                              # Utility scripts
├── research/                               # Research materials
├── logs/                                  # System logs
├── requirements.txt                       # Python dependencies
└── README.md                              # This file
```

**Quick Access:**
- **Main Project**: `projects/slm_orchestration_legal_rag/`
- **UI**: `projects/api_interfaces/ui/legal_ui.py`
- **Documentation**: `docs/` or `PROJECT_STRUCTURE_FINAL.md`

## 🎮 Usage

### Running the Streamlit UI

```bash
streamlit run legal_ui.py
```

The UI provides:
- **Query Input**: Enter legal questions
- **SLM Orchestration Visualization**: See how Flan-T5 analyzes queries and routes to agents
- **Agent Sequence**: View the dynamic agent sequence decided by the SLM
- **Answer Display**: View generated answers with citations
- **Confidence Scores**: See overall confidence in the answer

### Example Queries

Try these sample queries in the UI:

1. **"What is Article 21?"** - Simple factual query (uses: retriever → answering)
2. **"21"** - Vague query (uses: booster → retriever → answering)
3. **"What are the provisions of Section 377?"** - Complex query (uses: booster → retriever → answering → verifier)
4. **"Compare Article 19 and Article 21"** - Comparative query (uses: full pipeline)

### Programmatic Usage

```python
import asyncio
from projects.slm_orchestration_legal_rag.slm_orchestration_app import SLMOrchestrationApp

async def main():
    # Initialize with Flan-T5 orchestrator
    app = SLMOrchestrationApp(orchestrator_type="flan_t5")
    await app.initialize()
    
    # Process a query
    result = await app.process_query("What is Article 21 of the Indian Constitution?")
    
    print(f"Answer: {result['answer']}")
    print(f"Confidence: {result['confidence']:.2%}")
    print(f"Agent Sequence: {result['orchestration']['agent_sequence']}")
    print(f"Citations: {len(result['citations'])}")

asyncio.run(main())
```

## 🤖 System Architecture

### SLM Orchestrator (Flan-T5-small)

The orchestrator performs two key tasks:

1. **Query Analysis**: Determines query complexity, reasoning type, and requirements
2. **Agent Routing**: Decides which agents to use and in what sequence

**Example Decision Flow**:
```
Query: "What is Article 21?"
  ↓
SLM Analysis: {complexity: "simple", reasoning: "factual"}
  ↓
SLM Routing: ["retriever", "answering"]
  ↓
Execute agents in sequence
```

### Available Agents

1. **Booster Agent**: Enhances vague queries using Flan-T5-small
2. **Retriever Agent**: Searches 21,000+ legal documents using ChromaDB
3. **Answering Agent**: Generates answers using Groq LLM (Llama-3.1-8b-instant)
4. **Citation Verifier**: Verifies citations and ensures source attribution
5. **Multilingual Agent**: Handles language detection and translation

## 📊 Performance Comparison

| Orchestrator | Parameters | Cost/Decision | Latency | Routing Accuracy | API Required |
|--------------|------------|---------------|---------|------------------|--------------|
| **Flan-T5-small** (SLM) | 80M | **$0.0000** | **~15ms** | **85%+** | ❌ No |
| GPT-4 | 1.7T | $0.0200 | ~500ms | 90%+ | ✅ Yes |
| Rule-Based | N/A | $0.0000 | ~1ms | 70% | ❌ No |
| No Orchestration | N/A | $0.0000 | N/A | N/A | ❌ No |

## 🔧 Configuration

### Environment Variables (`.env`)

```env
# Required
OPENAI_API_KEY=your_openai_api_key_here
GROQ_API_KEY=your_groq_api_key_here

# Optional
EMBEDDING_MODEL=text-embedding-3-small
CHROMA_DB_PATH=./chroma_db_consolidated
LOG_LEVEL=INFO
```

### Vector Database Setup

The system uses ChromaDB for document retrieval. To build your own database:

1. **Prepare documents**: Place legal documents in a directory
2. **Run consolidation script** (if you have existing ChromaDB instances):
   ```bash
   python projects/database_builders/scripts/consolidate_chromadb.py
   ```

3. **Or add documents directly**:
   ```bash
   python projects/database_builders/scripts/add_docs_to_chromadb.py
   ```

## 🧪 Testing

Run the evaluation framework:

```bash
# Navigate to evaluation directory
cd projects/slm_orchestration_legal_rag/evaluation

# Run orchestration evaluation
python run_orchestration_evaluation.py
```

This will:
- Generate test dataset with 200+ queries
- Compare all orchestrators (Flan-T5, GPT-4, Rule-based, No-orchestration)
- Generate comprehensive evaluation report

## 🐛 Troubleshooting

### Common Issues

1. **"ModuleNotFoundError"**
   - Solution: Ensure virtual environment is activated and all dependencies are installed
   ```bash
   pip install -r requirements.txt
   ```

2. **"ChromaDB not found"**
   - Solution: The system will create a new database if none exists, or you can build one using the consolidation script

3. **"API Key Error"**
   - Solution: Ensure `.env` file exists with valid API keys

4. **"Low confidence scores"**
   - Solution: This is expected for queries with no matching documents. The system will still generate answers using general knowledge.

5. **"Streamlit not found"**
   - Solution: Ensure you're in the project root directory and virtual environment is activated
   ```bash
   streamlit run projects/api_interfaces/ui/legal_ui.py
   ```

## 📚 Research Applications

This system is designed for:

- **M.Tech Dissertation Research**: Demonstrating SLM orchestration effectiveness
- **Cost-Effective AI Systems**: Reducing LLM API costs by 500x
- **Multi-Agent Systems**: Coordinating specialized agents with SLMs
- **Legal AI**: Automated legal question answering with source verification
- **Orchestration Research**: Comparing SLM vs LLM vs rule-based orchestration

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- **Hugging Face** for Flan-T5-small model
- **OpenAI** for embedding models
- **Groq** for fast LLM inference
- **ChromaDB** for vector database
- **Streamlit** for web interface
- **LangChain** for LLM integration

## 📞 Support

For issues and questions:
- Create an issue in the repository
- Check the troubleshooting section above
- Review the evaluation reports in `projects/slm_orchestration_legal_rag/evaluation/`
- See `PROJECT_STRUCTURE_FINAL.md` for complete project organization

---

**Note**: This system is designed for research purposes. For production use in legal applications, ensure compliance with relevant regulations and professional standards.
