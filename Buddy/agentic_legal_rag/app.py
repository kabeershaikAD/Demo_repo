
"""
Main Application for Agentic Legal RAG
Entry point for the complete agentic legal research system
"""

import logging
import streamlit as st
import time
from typing import Dict, Any

from orchestrator import Orchestrator
from config import config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgenticLegalRAGApp:
    """Main application class for Agentic Legal RAG"""
    
    def __init__(self):
        self.orchestrator = None
        self.initialized = False
        self._initialize_system()
    
    def _initialize_system(self):
        """Initialize the agentic system"""
        try:
            logger.info("Initializing Agentic Legal RAG System...")
            
            # Initialize orchestrator
            self.orchestrator = Orchestrator()
            
            self.initialized = True
            logger.info("System initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing system: {e}")
            self.initialized = False
    
    def process_query(self, user_query: str, language: str = "en", user_context: str = None) -> Dict[str, Any]:
        """
        Process a user query through the agentic pipeline
        
        Args:
            user_query: The user's legal question
            language: Language of the query
            user_context: Additional context about the user
            
        Returns:
            Dict containing the complete result
        """
        if not self.initialized:
            return {
                'error': 'System not initialized',
                'answer': 'Please wait while the system initializes...'
            }
        
        try:
            # Process query through orchestrator using the new run method
            result = self.orchestrator.run(
                query=user_query,
                language=language,
                user_context=user_context
            )
            
            # Convert result to dictionary for easier handling
            return {
                'answer': result.get('answer', 'No answer generated'),
                'citations': result.get('citations', []),
                'sources': result.get('retrieved_documents', []),
                'confidence': result.get('confidence', 0.0),
                'human_review_required': result.get('human_review_required', False),
                'processing_time': result.get('processing_time', 0.0),
                'status': 'success' if 'error' not in result else 'error',
                'metadata': {
                    'enhanced_query': result.get('boosted_query', ''),
                    'language': language,
                    'user_context': user_context,
                    'retrieval_mode': result.get('retrieval_mode', 'both'),
                    'top_k': result.get('top_k', 5)
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                'error': str(e),
                'answer': 'I apologize, but I encountered an error while processing your query.',
                'confidence': 0.0,
                'human_review_required': True
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        if not self.initialized:
            return {'status': 'not_initialized'}
        
        try:
            health = self.orchestrator.get_system_health()
            return {
                'status': 'initialized',
                'health': health,
                'agents': len(health.get('agent_statuses', {})),
                'healthy_agents': health.get('healthy_agents', 0)
            }
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {'status': 'error', 'error': str(e)}

def main():
    """Main function to run the application"""
    st.set_page_config(
        page_title="Agentic Legal RAG",
        page_icon="⚖️",
        layout="wide"
    )
    
    st.title("⚖️ Agentic Legal RAG System")
    st.markdown("**Intelligent Legal Research with Multi-Agent Architecture**")
    
    # Initialize app
    if 'app' not in st.session_state:
        st.session_state.app = AgenticLegalRAGApp()
    
    app = st.session_state.app
    
    # Sidebar for system status
    with st.sidebar:
        st.header("System Status")
        
        if app.initialized:
            status = app.get_system_status()
            st.success("✅ System Online")
            st.metric("Healthy Agents", f"{status.get('healthy_agents', 0)}/{status.get('agents', 0)}")
            
            if st.button("Refresh Status"):
                st.rerun()
        else:
            st.error("❌ System Offline")
            if st.button("Retry Initialization"):
                app._initialize_system()
                st.rerun()
    
    # Main interface
    if not app.initialized:
        st.error("System initialization failed. Please check the logs and try again.")
        return
    
    # Query input
    st.header("Legal Query Interface")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        user_query = st.text_area(
            "Enter your legal question:",
            placeholder="e.g., What are the fundamental rights under Article 21 of the Indian Constitution?",
            height=100
        )
    
    with col2:
        language = st.selectbox(
            "Language:",
            ["en", "hi", "bn", "te", "mr", "ta", "gu", "kn", "ml", "pa", "or", "as", "ne", "ur"],
            index=0
        )
        
        user_context = st.text_input(
            "Context (optional):",
            placeholder="e.g., Supreme Court case"
        )
    
    # Process query
    if st.button("🔍 Process Query", type="primary"):
        if not user_query.strip():
            st.warning("Please enter a legal question.")
            return
        
        with st.spinner("Processing your query through the agentic pipeline..."):
            start_time = time.time()
            result = app.process_query(user_query, language, user_context)
            processing_time = time.time() - start_time
        
        # Display results
        st.header("📋 Results")
        
        # Answer
        if 'error' in result:
            st.error(f"Error: {result['error']}")
        else:
            # Show Enhanced Query (Boosted Prompt) prominently
            if result.get('metadata', {}).get('enhanced_query'):
                st.subheader("🚀 Enhanced Query (Boosted Prompt)")
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.write("**Original Query:**")
                    st.code(user_query, language="text")
                with col2:
                    st.write("**Enhanced Query:**")
                    st.code(result['metadata']['enhanced_query'], language="text")
                st.success("✅ Query enhanced by Prompt Booster Agent")
            
            st.subheader("💬 Answer")
            st.write(result.get('answer', 'No answer generated'))
            
            # Confidence and status
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Confidence", f"{result.get('confidence', 0):.2f}")
            with col2:
                st.metric("Processing Time", f"{result.get('processing_time', 0):.2f}s")
            with col3:
                status = "⚠️ Review Required" if result.get('human_review_required', False) else "✅ Verified"
                st.metric("Status", status)
            
            # Citations (Verified Claims)
            if result.get('citations'):
                st.subheader("📚 Verified Citations")
                st.info(f"Citation Verifier found {len(result['citations'])} claims to verify")
                
                for i, citation in enumerate(result['citations'], 1):
                    with st.expander(f"Claim {i}: {'✅ Supported' if citation.get('supported', False) else '❌ Not Supported'}"):
                        st.write(f"**Claim Text:** {citation.get('text', 'N/A')}")
                        st.write(f"**Supported:** {'✅ Yes' if citation.get('supported', False) else '❌ No'}")
                        st.write(f"**Confidence:** {citation.get('confidence', 0):.2f}")
                        if citation.get('best_doc'):
                            st.write(f"**Best Supporting Document:** {citation['best_doc']}")
                        if citation.get('reasoning'):
                            st.write(f"**Reasoning:** {citation['reasoning']}")
            else:
                st.subheader("📚 Citations")
                st.warning("No citations were verified by the Citation Verifier Agent")
            
            # Sources
            if result.get('sources'):
                st.subheader("📖 Retrieved Sources")
                
                # Group sources by type
                judgments = [s for s in result['sources'] if s.get('doc_type') == 'judgment']
                statutes = [s for s in result['sources'] if s.get('doc_type') in ['constitution', 'crpc', 'ipc']]
                other = [s for s in result['sources'] if s.get('doc_type') not in ['judgment', 'constitution', 'crpc', 'ipc']]
                
                if judgments:
                    st.write(f"**⚖️ Supreme Court Judgments ({len(judgments)})**")
                    for i, source in enumerate(judgments, 1):
                        with st.expander(f"Judgment {i}: {source.get('title', 'Untitled')[:60]}..."):
                            st.write(f"**Court:** {source.get('court', 'Supreme Court of India')}")
                            st.write(f"**Similarity:** {source.get('similarity_score', 0):.3f}")
                            if source.get('date'):
                                st.write(f"**Date:** {source['date']}")
                            if source.get('content'):
                                st.write(f"**Content Preview:** {source['content'][:300]}...")
                
                if statutes:
                    st.write(f"**📜 Legal Statutes ({len(statutes)})**")
                    for i, source in enumerate(statutes, 1):
                        with st.expander(f"Statute {i}: {source.get('title', 'Untitled')[:60]}..."):
                            st.write(f"**Type:** {source.get('doc_type', 'Unknown')}")
                            st.write(f"**Similarity:** {source.get('similarity_score', 0):.3f}")
                            if source.get('section'):
                                st.write(f"**Section:** {source['section']}")
                            if source.get('act'):
                                st.write(f"**Act:** {source['act']}")
                            if source.get('content'):
                                st.write(f"**Content Preview:** {source['content'][:300]}...")
                
                if other:
                    st.write(f"**📄 Other Documents ({len(other)})**")
                    for i, source in enumerate(other, 1):
                        with st.expander(f"Document {i}: {source.get('title', 'Untitled')[:60]}..."):
                            st.write(f"**Type:** {source.get('doc_type', 'Unknown')}")
                            st.write(f"**Similarity:** {source.get('similarity_score', 0):.3f}")
                            if source.get('content'):
                                st.write(f"**Content Preview:** {source['content'][:300]}...")
            
            # Agent Processing Steps
            st.subheader("🤖 Agent Processing Steps")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.success("🚀 Prompt Booster")
                st.write("Query enhanced")
            
            with col2:
                st.success("🔍 Retriever")
                st.write(f"{len(result.get('sources', []))} documents found")
            
            with col3:
                st.success("💬 Answering")
                st.write("Answer generated")
            
            with col4:
                if result.get('citations'):
                    st.success("✅ Citation Verifier")
                    st.write(f"{len(result['citations'])} claims verified")
                else:
                    st.warning("⚠️ Citation Verifier")
                    st.write("No claims to verify")
            
            # Metadata
            if result.get('metadata'):
                with st.expander("🔧 Detailed Processing Information"):
                    metadata = result['metadata']
                    if metadata.get('enhanced_query'):
                        st.write(f"**Enhanced Query:** {metadata['enhanced_query']}")
                    if metadata.get('language'):
                        st.write(f"**Language:** {metadata['language']}")
                    if metadata.get('user_context'):
                        st.write(f"**User Context:** {metadata['user_context']}")
    
    # System information
    with st.expander("ℹ️ System Information"):
        st.markdown("""
        **Agentic Legal RAG System Features:**
        
        - **Prompt Booster Agent**: Enhances queries for better legal retrieval
        - **Retriever Agent**: Finds relevant legal documents using existing ChromaDB
        - **Answering Agent**: Generates comprehensive legal answers with citations
        - **Citation Verifier**: Verifies claims against retrieved documents
        - **Multilingual Agent**: Supports multiple Indian languages
        - **Dynamic Updater**: Keeps legal database current
        
        **API Integration Points:**
        - Groq API for LLM-based answer generation
        - Indian Kanoon API for legal data updates
        - Translation APIs for multilingual support
        """)
        
        if app.initialized:
            status = app.get_system_status()
            st.json(status)

if __name__ == "__main__":
    main()
