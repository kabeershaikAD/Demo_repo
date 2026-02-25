# Fix Retriever Issue - No Documents Retrieved

## Problem
The retriever is returning 0 documents because:
1. **OPENAI_API_KEY is not set** - Required for embeddings/search
2. **GROQ_API_KEY is not set** - Required for answer generation

## Solution

### Step 1: Set Environment Variables

**Option A: Using PowerShell (Recommended)**
```powershell
# Set OpenAI API Key (for embeddings/search)
$env:OPENAI_API_KEY = "your-openai-api-key-here"

# Set Groq API Key (for answer generation)
$env:GROQ_API_KEY = "your-groq-api-key-here"
```

**Option B: Create a .env file**
Create a file named `.env` in the project root:
```
OPENAI_API_KEY=your-openai-api-key-here
GROQ_API_KEY=your-groq-api-key-here
```

Then load it in your code or use `python-dotenv`:
```python
from dotenv import load_dotenv
load_dotenv()
```

### Step 2: Activate Virtual Environment

```powershell
cd "C:\Users\Lenovo\Downloads\Collage_Materials\Major project"
.\legal_rag_env\Scripts\Activate.ps1
```

### Step 3: Verify Configuration

Run the diagnostic script:
```powershell
python diagnose_retriever_issue.py
```

You should see:
- `OPENAI_API_KEY: [SET]`
- `GROQ_API_KEY: [SET]`
- `[SUCCESS] Connected to ChromaDB`
- `Collection count: X documents` (should be > 0)

### Step 4: Test the System

Run Streamlit:
```powershell
streamlit run legal_ui.py
```

Try query: "IPC section 302"

## Why This Happens

1. **OpenAI API Key**: The retriever uses OpenAI's `text-embedding-3-small` model to create embeddings for your query. Without the API key, it can't search the ChromaDB.

2. **Groq API Key**: The answering agent uses Groq's LLM to generate answers. Without it, you'll get fallback responses.

## Quick Fix Script

Save this as `setup_api_keys.ps1`:

```powershell
# Setup API Keys for Legal RAG System
Write-Host "Setting up API keys..." -ForegroundColor Yellow

# Get API keys from user
$openai_key = Read-Host "Enter your OpenAI API Key"
$groq_key = Read-Host "Enter your Groq API Key"

# Set environment variables for current session
$env:OPENAI_API_KEY = $openai_key
$env:GROQ_API_KEY = $groq_key

Write-Host "API keys set for current session!" -ForegroundColor Green
Write-Host "Note: These will be lost when you close PowerShell." -ForegroundColor Yellow
Write-Host "To make permanent, add them to your system environment variables." -ForegroundColor Yellow
```

Run it:
```powershell
.\setup_api_keys.ps1
```

## Permanent Solution

To make API keys permanent:

1. **Windows Settings** → **System** → **About** → **Advanced system settings**
2. Click **Environment Variables**
3. Under **User variables**, click **New**
4. Add:
   - Variable name: `OPENAI_API_KEY`
   - Variable value: `your-key-here`
5. Repeat for `GROQ_API_KEY`

## After Setting Keys

1. Restart your terminal/PowerShell
2. Activate virtual environment
3. Run `streamlit run legal_ui.py`
4. Test with query: "IPC section 302"

The retriever should now find documents!



