# Agentic Legal RAG System - Project Abstract

## Abstract

Legal research and question-answering systems are increasingly critical in the digital transformation of legal services, particularly in jurisdictions like India where access to legal information remains a significant challenge. Traditional legal research methods are time-consuming, require extensive domain expertise, and often fail to provide comprehensive answers that integrate multiple legal sources including statutes, case law, and constitutional provisions. Current legal AI systems predominantly rely on single large language models with limited retrieval capabilities, resulting in generic responses, citation hallucinations, and insufficient context awareness for complex legal queries. The absence of specialized agents for different legal tasks, lack of human-in-the-loop validation, and limited multilingual support further restrict the practical applicability of existing solutions in diverse legal environments.

This project introduces an Agentic Legal RAG (Retrieval-Augmented Generation) system built using Python and specialized microservices architecture, where multiple AI agents operate collaboratively to provide comprehensive legal question-answering. The system employs a Prompt Booster agent using Flan-T5-small for query enhancement, a specialized Retriever agent with ChromaDB for document retrieval, and an Answering agent with Groq API integration for response generation. The Orchestrator agent coordinates all components using structured JSON communication and implements intelligent routing based on query complexity and legal domain. The system integrates multilingual support for Indian languages, dynamic document updating capabilities, and comprehensive logging for audit trails. A Streamlit-based user interface enables intuitive interaction, while the modular architecture supports easy extension and maintenance, establishing a robust foundation for scalable, accurate, and trustworthy legal AI systems.

The system demonstrates significant improvements in legal query processing through intelligent query enhancement and specialized retrieval mechanisms. The modular agent-based architecture enables efficient processing of complex legal queries with comprehensive error handling and fallback mechanisms. The document versioning system enables tracking of legal updates and amendments. The modular design allows for easy integration of additional legal domains and jurisdictions, making it suitable for deployment in law firms, legal aid organizations, and educational institutions. The project represents a significant advancement in legal AI technology, providing a practical solution for democratizing access to legal information while maintaining the accuracy and reliability required in legal practice.

**Name:** [Your Name]  
**Roll No:** [Your Roll Number]  
**Email:** [Your Email]  
**Phone:** [Your Phone Number]  

**Signature of the Supervisor:** Dr. V. Prashanthi (Associate Professor)  
**Signature of the Co-Supervisor:** Mr. V. Srikanth (Assistant Professor)
