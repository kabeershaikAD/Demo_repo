# Why You're Seeing "Direct Answer" Message

## What is "Direct Answer"?

The "direct answer" message is a **fallback response** that appears when the LLM (Language Model) is not properly initialized. Instead of generating a real answer using Groq's LLM, the system shows a template message.

## The Message You're Seeing

```
Based on the available information, I can provide the following response:

Query: [your query]

Retrieved Documents: 0 documents found

Note: This response is generated without LLM processing. 
For detailed legal analysis, please ensure the LLM is properly configured.
```

## Why This Happens

The answering agent checks if the LLM is available:
- ✅ If LLM is initialized → Generates real answers using Groq
- ❌ If LLM is NOT initialized → Shows fallback "direct answer" message

## Root Cause

**Missing Package**: `langchain_groq` is not installed in your virtual environment.

## How to Fix

### Step 1: Activate Virtual Environment
```powershell
cd "C:\Users\Lenovo\Downloads\Collage_Materials\Major project"
.\legal_rag_env\Scripts\Activate.ps1
```

### Step 2: Install Missing Package
```powershell
pip install langchain-groq
```

### Step 3: Verify Installation
```powershell
python test_llm_init.py
```

You should see:
- `[SUCCESS] langchain_groq imported`
- `[SUCCESS] LLM initialized!`
- `[SUCCESS] LLM is initialized - should work properly`

### Step 4: Restart Streamlit
```powershell
streamlit run legal_ui.py
```

## After Fixing

Once `langchain-groq` is installed:
- ✅ LLM will initialize properly
- ✅ Real answers will be generated (not fallback messages)
- ✅ You'll get proper legal analysis with citations
- ✅ No more "direct answer" messages

## Check Current Status

Run this to check if LLM is working:
```powershell
python test_llm_init.py
```

If you see `LLM initialized: False`, then the package is missing.



