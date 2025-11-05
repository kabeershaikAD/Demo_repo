# 📦 GitHub Repository Setup Guide

**Instructions for pushing your SLM Orchestration Legal RAG System to GitHub**

## 🔒 Pre-Push Checklist

Before pushing to GitHub, ensure:

- [ ] All sensitive files are excluded (API keys, databases, etc.)
- [ ] `.gitignore` is properly configured
- [ ] `.env` file is NOT committed (it's in `.gitignore`)
- [ ] Large files (databases, models) are excluded
- [ ] README.md is updated with correct information

## 🚀 Step-by-Step GitHub Setup

### Step 1: Initialize Git Repository (if not already done)

```bash
# Navigate to project root
cd "Major project"

# Initialize git (if not already initialized)
git init
```

### Step 2: Verify .gitignore

Check that `.gitignore` includes:
- `.env` files
- Database files (`*.db`, `*.sqlite`)
- Vector databases (`chroma_db*/`)
- Virtual environments (`legal_rag_env/`)
- Logs (`logs/`)
- `__pycache__/`

### Step 3: Add Files to Git

```bash
# Add all files (respecting .gitignore)
git add .

# Verify what will be committed
git status
```

**Important**: Check `git status` output to ensure:
- ✅ `README.md` is included
- ✅ `requirements.txt` is included
- ✅ `legal_ui.py` is included
- ✅ `.env.example` is included (if created)
- ❌ `.env` is NOT included
- ❌ Database files are NOT included
- ❌ Virtual environment is NOT included

### Step 4: Create Initial Commit

```bash
git commit -m "Initial commit: SLM Orchestration Legal RAG System

- Flan-T5-small orchestrator for multi-agent systems
- Streamlit UI for legal query processing
- Complete agent ecosystem (booster, retriever, answering, verifier)
- Evaluation framework for orchestration comparison
- Comprehensive documentation and setup guides"
```

### Step 5: Create GitHub Repository

1. Go to [GitHub](https://github.com)
2. Click "New repository"
3. Repository name: `slm-orchestration-legal-rag` (or your preferred name)
4. Description: `SLM Orchestration Framework: Efficient Multi-Agent Orchestration Using Small Language Models (Flan-T5)`
5. Choose **Public** or **Private**
6. **DO NOT** initialize with README, .gitignore, or license (we already have these)
7. Click "Create repository"

### Step 6: Connect Local Repository to GitHub

```bash
# Add remote (replace <username> and <repo-name> with your details)
git remote add origin https://github.com/<username>/<repo-name>.git

# Verify remote
git remote -v
```

### Step 7: Push to GitHub

```bash
# Push to main branch
git branch -M main
git push -u origin main
```

If prompted for credentials:
- Use GitHub Personal Access Token (not password)
- [Create token here](https://github.com/settings/tokens)

## 📋 Repository Structure (What Should Be Committed)

```
Major project/
├── .gitignore                    ✅ Commit
├── README.md                     ✅ Commit
├── SETUP.md                      ✅ Commit
├── requirements.txt              ✅ Commit
├── legal_ui.py                   ✅ Commit
├── .env.example                  ✅ Commit (if created)
│
├── Buddy/
│   └── agentic_legal_rag/
│       ├── slm_orchestration_app.py  ✅ Commit
│       ├── orchestrators/            ✅ Commit (all .py files)
│       ├── agents/                   ✅ Commit (all .py files)
│       ├── agent_adapters.py         ✅ Commit
│       ├── config.py                 ✅ Commit
│       ├── evaluation/               ✅ Commit
│       └── requirements.txt          ✅ Commit (if exists)
│
├── data_processing/              ✅ Commit (if exists)
├── api/                          ✅ Commit (if exists)
│
├── chroma_db_consolidated/       ❌ DO NOT COMMIT (too large)
├── indian_legal_db.sqlite        ❌ DO NOT COMMIT (sensitive)
├── legal_rag_env/                ❌ DO NOT COMMIT (virtual env)
├── logs/                         ❌ DO NOT COMMIT (generated)
├── .env                          ❌ DO NOT COMMIT (sensitive)
└── __pycache__/                  ❌ DO NOT COMMIT (generated)
```

## 🔐 Security Reminders

### Before Pushing:

1. **Check for API Keys**: Search for hardcoded keys
   ```bash
   # Search for common API key patterns
   grep -r "sk-" . --exclude-dir=legal_rag_env
   grep -r "gsk-" . --exclude-dir=legal_rag_env
   ```

2. **Verify .gitignore**: Ensure sensitive files are excluded
   ```bash
   git status --ignored
   ```

3. **Review Commits**: Check what's being committed
   ```bash
   git diff --cached
   ```

### If You Accidentally Committed Sensitive Data:

```bash
# Remove sensitive file from git history
git rm --cached .env
git commit -m "Remove sensitive .env file"

# Force push (if already pushed)
git push --force
```

**Note**: If you already pushed sensitive data, consider:
- Rotating your API keys immediately
- Using GitHub's secret scanning alerts
- Rewriting git history (advanced)

## 📝 Repository Description Template

Use this for your GitHub repository description:

```
SLM Orchestration Framework: Demonstrates Flan-T5-small (80M parameters) effectively orchestrating multi-agent legal RAG systems with 500x lower cost and 33x faster latency compared to GPT-4 orchestration.
```

## 🏷️ Suggested Tags/Labels

For better discoverability, add these topics to your repository:

- `machine-learning`
- `nlp`
- `rag`
- `multi-agent-systems`
- `legal-ai`
- `small-language-models`
- `orchestration`
- `streamlit`
- `chromadb`
- `langchain`

## 📄 License

Consider adding a LICENSE file:

```bash
# Create MIT License
# Visit: https://choosealicense.com/licenses/mit/
# Or create LICENSE file manually
```

## ✅ Post-Push Checklist

After pushing:

- [ ] Verify all files are visible on GitHub
- [ ] Check that sensitive files are NOT visible
- [ ] Test cloning the repository to a new location
- [ ] Verify README displays correctly
- [ ] Test setup instructions on a fresh machine
- [ ] Add repository description
- [ ] Add topics/tags
- [ ] Create initial release (optional)

## 🎉 Done!

Your repository is now on GitHub. Others can clone and set up the system using:

```bash
git clone <your-repo-url>
cd "Major project"
# Follow SETUP.md instructions
```

## 📞 Need Help?

- [GitHub Documentation](https://docs.github.com)
- [Git Basics](https://git-scm.com/book/en/v2/Getting-Started-Git-Basics)
- [GitHub Security Best Practices](https://docs.github.com/en/code-security)

