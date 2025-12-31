# 🚀 Quick Start Guide - Agentic Legal RAG

## ⚡ **Get Up and Running in 5 Minutes**

This guide will help you get the Agentic Legal RAG system running quickly.

## 📋 **Prerequisites**

- Python 3.10+
- 8GB+ RAM
- 10GB+ free disk space
- Internet connection (for model downloads)

## 🔑 **Step 1: Get Your API Key**

### **Required: Groq API Key**
1. Go to [console.groq.com](https://console.groq.com/)
2. Sign up for a free account
3. Get your API key from the dashboard
4. Copy the key (starts with `gsk_...`)

### **Optional: OpenAI API Key** (for enhanced features)
1. Go to [platform.openai.com](https://platform.openai.com/)
2. Sign up and get API key
3. Copy the key (starts with `sk-...`)

## 🚀 **Step 2: Quick Installation**

```bash
# 1. Navigate to the project directory
cd agentic_legal_rag

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set your API key
export GROQ_API_KEY="your_groq_api_key_here"

# 4. Run the system
python app.py ui
```

## 🎯 **Step 3: Test the System**

### **Option A: Streamlit UI (Recommended)**
```bash
python app.py ui
```
- Open your browser to `http://localhost:8501`
- Ask a legal question like "What is Article 21?"
- See the system work in real-time

### **Option B: CLI Interface**
```bash
python app.py --query "What is Article 21?"
```

### **Option C: Interactive Mode**
```bash
python app.py --interactive
```

## 📚 **Step 4: Add Legal Data (Optional)**

### **Add Your Own Documents**
1. Place PDF/DOCX files in `data/bare_acts/`
2. Run: `python app.py --build-index`
3. Your documents will be searchable

### **Use Sample Data**
The system comes with sample legal data for testing.

## 🌍 **Step 5: Try Multilingual Features**

### **Ask Questions in Different Languages**
- Hindi: "अनुच्छेद 21 क्या है?"
- Telugu: "ఆర్టికల్ 21 అంటే ఏమిటి?"
- Tamil: "கட்டுரை 21 என்றால் என்ன?"

The system will automatically detect the language and respond appropriately.

## 🔧 **Step 6: Configure the System**

### **Basic Configuration**
Edit `config.py` to customize:
- Model settings
- Retrieval parameters
- Language support
- Update frequencies

### **Advanced Configuration**
- API endpoints
- Database settings
- Logging levels
- Performance tuning

## 📊 **Step 7: Run Evaluation**

```bash
python app.py --evaluate
```

This will run comprehensive evaluation and show system performance metrics.

## 🧪 **Step 8: Run Tests**

```bash
pytest tests/ -v
```

Verify all components are working correctly.

## 🎉 **You're Ready!**

Your Agentic Legal RAG system is now running with:

- ✅ **Query Enhancement**: SLM-powered query improvement
- ✅ **Document Retrieval**: Semantic search with cross-linking
- ✅ **Answer Generation**: LLM-powered legal answers
- ✅ **Citation Verification**: Automatic claim verification
- ✅ **Multilingual Support**: 8 Indian languages
- ✅ **Dynamic Updates**: Real-time legal data ingestion

## 🆘 **Troubleshooting**

### **Common Issues**

**1. API Key Error**
```bash
# Make sure your API key is set
echo $GROQ_API_KEY
# Should show your key starting with gsk_
```

**2. Model Loading Error**
```bash
# Check internet connection
# Models will download automatically on first run
```

**3. Memory Error**
```bash
# Reduce batch size in config.py
# Or use smaller models
```

**4. Import Error**
```bash
# Make sure all dependencies are installed
pip install -r requirements.txt
```

### **Get Help**
- Check the logs in `logs/` directory
- Review the full README.md
- Check the architecture documentation
- Run tests to identify issues

## 🎯 **Next Steps**

### **Production Deployment**
1. Set up proper API key management
2. Configure production database
3. Set up monitoring and logging
4. Deploy with Docker

### **Customization**
1. Add your own legal documents
2. Fine-tune models for your domain
3. Customize the UI
4. Add new data sources

### **Advanced Features**
1. Set up dynamic updates
2. Configure multilingual models
3. Add custom evaluation metrics
4. Integrate with existing systems

## 📞 **Support**

- **Documentation**: Check README.md and ARCHITECTURE_DOCUMENTATION.md
- **Issues**: Create an issue on GitHub
- **Tests**: Run `pytest tests/ -v` to verify setup
- **Logs**: Check `logs/` directory for error details

---

**🎉 Congratulations! You now have a fully functional Agentic Legal RAG system!** ⚖️🤖

