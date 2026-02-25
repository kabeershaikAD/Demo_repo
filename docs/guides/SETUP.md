# 🚀 Complete Setup Guide

**Step-by-step instructions to replicate the SLM Orchestration Legal RAG System on any machine**

## 📋 Prerequisites Checklist

Before starting, ensure you have:

- [ ] Python 3.10 or higher (check with `python --version`)
- [ ] Git installed (for cloning repository)
- [ ] 8GB+ RAM available
- [ ] Internet connection (for downloading models and dependencies)
- [ ] OpenAI API key ([Get one here](https://platform.openai.com/api-keys))
- [ ] Groq API key ([Get one here](https://console.groq.com/keys))

## 🔧 Step-by-Step Setup

### Step 1: Clone the Repository

```bash
# Clone the repository
git clone <your-repository-url>
cd "Major project"
```

### Step 2: Create Virtual Environment

**Windows:**
```bash
python -m venv legal_rag_env
legal_rag_env\Scripts\activate
```

**Linux/Mac:**
```bash
python -m venv legal_rag_env
source legal_rag_env/bin/activate
```

You should see `(legal_rag_env)` in your terminal prompt.

### Step 3: Upgrade pip

```bash
python -m pip install --upgrade pip
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

**Note**: This may take 10-15 minutes depending on your internet connection. The installation includes:
- PyTorch (~2GB)
- Transformers and Hugging Face libraries
- LangChain ecosystem
- ChromaDB
- Streamlit
- All other dependencies

### Step 5: Set Up Environment Variables

1. **Copy the example file:**
   ```bash
   # Windows
   copy .env.example .env
   
   # Linux/Mac
   cp .env.example .env
   ```

2. **Edit the `.env` file:**
   ```bash
   # Windows
   notepad .env
   
   # Linux/Mac
   nano .env
   ```

3. **Add your API keys:**
   ```env
   OPENAI_API_KEY=sk-your-actual-openai-key-here
   GROQ_API_KEY=gsk-your-actual-groq-key-here
   ```

4. **Save and close the file**

### Step 6: Verify Installation

Run a quick test to ensure everything is installed:

```bash
python -c "import torch; import transformers; import streamlit; import chromadb; print('✅ All dependencies installed!')"
```

You should see: `✅ All dependencies installed!`

### Step 7: Set Up Vector Database (Optional but Recommended)

The system will work without a pre-built database, but for best results:

**Option A: Use existing consolidated database**
- If you have `chroma_db_consolidated` folder, place it in the project root
- The retriever will automatically detect and use it

**Option B: Build your own database**
```bash
# Add sample documents
python add_docs_to_chromadb.py
```

**Option C: Consolidate existing databases**
```bash
# If you have multiple ChromaDB instances
python consolidate_chromadb.py
```

### Step 8: Run the Application

```bash
streamlit run legal_ui.py
```

You should see:
```
  You can now view your Streamlit app in your browser.
  Local URL: http://localhost:8501
```

Open your browser and navigate to `http://localhost:8501`

## ✅ Verification Tests

### Test 1: Check System Initialization

1. Open the Streamlit UI
2. Wait for "✅ System Initialized" message
3. Check that all agents are listed as available

### Test 2: Test a Simple Query

1. Enter: `"What is Article 21?"`
2. Click "🚀 Process Query"
3. Verify:
   - Answer is generated
   - SLM orchestration decision is shown
   - Agent sequence is displayed
   - Citations are listed

### Test 3: Test Vague Query

1. Enter: `"21"`
2. Click "🚀 Process Query"
3. Verify:
   - Booster agent is used (query is enhanced)
   - Full pipeline is executed
   - Answer is generated

## 🐛 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'X'"

**Solution:**
```bash
# Ensure virtual environment is activated
# Windows: legal_rag_env\Scripts\activate
# Linux/Mac: source legal_rag_env/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: "Streamlit command not found"

**Solution:**
```bash
# Ensure you're in the project root directory
cd "Major project"

# Activate virtual environment
# Windows: legal_rag_env\Scripts\activate
# Linux/Mac: source legal_rag_env/bin/activate

# Try running with python -m
python -m streamlit run legal_ui.py
```

### Issue: "API Key Error"

**Solution:**
1. Check that `.env` file exists in project root
2. Verify API keys are correct (no extra spaces)
3. Ensure `.env` file is in the same directory as `legal_ui.py`

### Issue: "ChromaDB not found"

**Solution:**
- This is OK! The system will create a new database
- For best results, run `python add_docs_to_chromadb.py` to add sample documents

### Issue: "No answer generated"

**Solution:**
- Check that Groq API key is valid
- Ensure internet connection is active
- Check logs for error messages

### Issue: "Low confidence scores"

**Solution:**
- This is expected if no matching documents are found
- The system will still generate answers using general knowledge
- Add more documents to ChromaDB for better results

### Issue: "CUDA out of memory" (if using GPU)

**Solution:**
- Flan-T5-small should run on CPU fine
- If using GPU, ensure you have 4GB+ VRAM
- You can force CPU by setting `device="cpu"` in config

## 📊 System Requirements

### Minimum Requirements
- **CPU**: 4 cores
- **RAM**: 8GB
- **Storage**: 10GB free space
- **OS**: Windows 10+, Linux, or macOS

### Recommended Requirements
- **CPU**: 8+ cores
- **RAM**: 16GB
- **Storage**: 20GB free space
- **GPU**: Optional (CPU works fine for Flan-T5-small)

## 🔄 Updating the System

### Update Dependencies

```bash
# Activate virtual environment
# Windows: legal_rag_env\Scripts\activate
# Linux/Mac: source legal_rag_env/bin/activate

# Update pip
pip install --upgrade pip

# Update all packages
pip install --upgrade -r requirements.txt
```

### Pull Latest Changes

```bash
git pull origin main
```

## 🎓 Next Steps

After successful setup:

1. **Explore the UI**: Try different types of queries
2. **Review Orchestration**: See how Flan-T5 decides agent routing
3. **Add Documents**: Populate ChromaDB with your legal documents
4. **Run Evaluation**: Test the evaluation framework
5. **Read Documentation**: Check `README.md` for detailed usage

## 📞 Getting Help

If you encounter issues:

1. Check the troubleshooting section above
2. Review error messages in the terminal
3. Check logs in the `logs/` directory
4. Create an issue in the repository with:
   - Your OS and Python version
   - Error message
   - Steps to reproduce

## ✅ Setup Complete!

Once you see the Streamlit UI running, you're all set! The system is ready to process legal queries using SLM orchestration.

**Happy querying! 🎉**





