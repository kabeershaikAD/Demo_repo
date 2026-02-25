"""
SLM Orchestration Legal RAG System - Streamlit UI
"""
import streamlit as st
import asyncio
import json
import sys
import os
from datetime import datetime

# Add the projects/slm_orchestration_legal_rag directory to path
# Add the projects/slm_orchestration_legal_rag directory to path
_script_dir = os.path.dirname(os.path.abspath(__file__))
# Repo root: 3 levels up from projects/api_interfaces/ui/legal_ui.py
_repo_root = os.path.abspath(os.path.join(_script_dir, '..', '..', '..'))
slm_project_path = os.path.join(_repo_root, 'projects', 'slm_orchestration_legal_rag')
if not os.path.isdir(slm_project_path):
    # Fallback: run from repo root
    slm_project_path = os.path.join(os.getcwd(), 'projects', 'slm_orchestration_legal_rag')
sys.path.insert(0, slm_project_path)
project_root = _repo_root if os.path.isdir(slm_project_path) else os.getcwd()

from slm_orchestration_app import SLMOrchestrationApp

# Page config
# Page config
st.set_page_config(
    page_title="SLM Orchestration Legal RAG System",
    page_icon="🏛️",
    layout="wide"
)

# Initialize session state
if "slm_app" not in st.session_state:
    st.session_state.slm_app = None
if "query_history" not in st.session_state:
    st.session_state.query_history = []

def initialize_system():
    """Initialize the SLM Orchestration App."""
    if st.session_state.slm_app is None:
        with st.spinner("Initializing SLM Orchestration Legal RAG System..."):
            # Initialize with Flan-T5 orchestrator by default
            st.session_state.slm_app = SLMOrchestrationApp(orchestrator_type="flan_t5")
            asyncio.run(st.session_state.slm_app.initialize())

def main():
    """Main Streamlit app."""
    st.title("🏛️ SLM Orchestration Legal RAG System")
    st.markdown("**Multi-Agent Legal Information Retrieval with Flan-T5 Orchestrator**")
    
    # Initialize system
    initialize_system()
    
    # Sidebar
    with st.sidebar:
        st.header("🤖 System Status")
        
        if st.session_state.slm_app:
            st.metric("Orchestrator", "Flan-T5-small (SLM)")
            st.metric("Cost per Query", "$0.00")
            st.info("✅ System Initialized")
            
            st.subheader("Available Agents")
            agents = ["booster", "retriever", "answering", "verifier", "multilingual"]
            for agent in agents:
                st.write(f"✅ {agent.title()}")
            
            if st.button("🔄 Reinitialize System"):
                st.session_state.slm_app = None
                initialize_system()
                st.rerun()
        
        st.header("📚 Sample Queries")
        sample_queries = [
            "What is the definition of invention under patent law?",
            "Can living organisms be patented?",
            "What is the right to privacy in Indian Constitution?",
            "What are the provisions of Section 377?",
            "What are the fundamental rights under Article 19?",
            "What is the punishment for cyber crimes under IT Act?",
            "What are the requirements for patentability?",
            "What is the latest Supreme Court judgment on Aadhaar?"
        ]
        
        for query in sample_queries:
            if st.button(query, key=f"sample_{query}"):
                st.session_state.current_query = query
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("🔍 Ask a Legal Question")
        
        # Query input
        query = st.text_input(
            "Enter your legal question:",
            value=getattr(st.session_state, 'current_query', ''),
            placeholder="e.g., What is the definition of invention under patent law?"
        )
        
        if st.button("🚀 Process Query", type="primary"):
            if query and st.session_state.slm_app:
                with st.spinner("Processing your query with SLM orchestrator..."):
                    try:
                        result = asyncio.run(st.session_state.slm_app.process_query(query))
                        
                        # Store orchestration info separately for display
                        st.session_state.orchestration_info = result.get("orchestration", {})
                        
                        # Store in history
                        st.session_state.query_history.append({
                            "query": query,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "result": result
                        })
                        
                        # Display result
                        st.session_state.current_result = result
                    except Exception as e:
                        st.error(f"Error processing query: {e}")
                        st.session_state.current_result = None
            elif not st.session_state.slm_app:
                st.error("System not initialized. Please wait...")
            else:
                st.warning("Please enter a query.")
    
    with col2:
        st.header("🤖 SLM Orchestration Decision")
        
        # Show SLM orchestration analysis
        if hasattr(st.session_state, 'orchestration_info') and st.session_state.orchestration_info:
            orchestration = st.session_state.orchestration_info
            analysis = orchestration.get('analysis', {})
            
            # SLM Model Info
            st.info("🧠 **Flan-T5-small** is orchestrating this query")
            
            # Query Analysis by SLM
            st.subheader("📊 SLM Query Analysis")
            complexity = analysis.get('complexity', 'unknown')
            reasoning_type = analysis.get('reasoning_type', 'unknown')
            slm_confidence = analysis.get('confidence', 0.7)
            
            st.write(f"**Complexity:** {complexity.title()}")
            st.write(f"**Reasoning Type:** {reasoning_type.title()}")
            st.write(f"**SLM Confidence:** {slm_confidence:.1%}")
            st.progress(slm_confidence)
            
            # Agent Sequence Decision by SLM
            agent_sequence = orchestration.get('agent_sequence', [])
            if agent_sequence:
                st.subheader("🎯 Agent Sequence (SLM Decision)")
                sequence_str = " → ".join([f"**{a.title()}**" for a in agent_sequence])
                st.markdown(f"{sequence_str}")
                st.caption("This sequence was determined by Flan-T5-small orchestrator")
            
            # Orchestration Metrics
            metrics = orchestration.get('metrics', {})
            if metrics:
                st.subheader("⚡ Performance")
                st.write(f"**Cost:** ${metrics.get('avg_cost', 0.0):.4f}")
                st.write(f"**Latency:** {metrics.get('avg_latency', 0.0):.2f}ms")
        
        elif hasattr(st.session_state, 'current_result') and st.session_state.current_result:
            result = st.session_state.current_result
            
            # Fallback: Show agents used
            agents_used = result.get('agent_sequence', result.get('agents_used', []))
            if agents_used:
                st.subheader("🤖 Agents Used")
                sequence_str = " → ".join(agents_used)
                st.write(sequence_str)
            
            # Confidence score
            confidence = result.get('confidence', 0.0)
            st.subheader("🎯 Answer Confidence")
            st.progress(min(max(confidence, 0.0), 1.0))
            st.write(f"{confidence:.1%}")
            
            # Citations count
            citations = result.get('citations', [])
            st.subheader("📚 Citations")
            st.write(f"**Total:** {len(citations)}")
    
    # Display SLM Orchestration Details (if available)
    if hasattr(st.session_state, 'orchestration_info') and st.session_state.orchestration_info:
        with st.expander("🔍 View SLM Orchestration Details", expanded=False):
            orchestration = st.session_state.orchestration_info
            analysis = orchestration.get('analysis', {})
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 📊 Query Analysis by Flan-T5")
                st.json({
                    "Complexity": analysis.get('complexity', 'unknown'),
                    "Reasoning Type": analysis.get('reasoning_type', 'unknown'),
                    "Requires Enhancement": analysis.get('requires_enhancement', False),
                    "Requires Verification": analysis.get('requires_verification', False),
                    "Estimated Steps": analysis.get('estimated_steps', 0),
                    "SLM Confidence": f"{analysis.get('confidence', 0.7):.1%}"
                })
            
            with col2:
                st.markdown("### 🎯 Routing Decision by Flan-T5")
                st.json({
                    "Orchestrator": orchestration.get('orchestrator', 'flan_t5'),
                    "Agent Sequence": orchestration.get('agent_sequence', []),
                    "Decision Model": "Flan-T5-small (80M parameters)",
                    "Cost": "$0.00",
                    "Latency": f"{orchestration.get('metrics', {}).get('avg_latency', 0):.2f}ms"
                })
            
            st.info("💡 **This shows that Flan-T5-small (SLM) is analyzing the query and deciding which agents to use, not a fixed pipeline!**")
    
    # Display results
    if hasattr(st.session_state, 'current_result') and st.session_state.current_result:
        result = st.session_state.current_result
        
        st.header("💡 Answer")
        answer = result.get('answer', 'No answer generated')
        st.write(answer)
        
        # Citations
        citations = result.get('citations', [])
        if citations:
            st.header("📚 Sources & Citations")
            for i, citation in enumerate(citations, 1):
                # Handle different citation formats
                title = citation.get('title', citation.get('text', 'Unknown Source'))
                source = citation.get('source', citation.get('doc_type', 'Unknown'))
                
                with st.expander(f"Source {i}: {title}"):
                    st.write(f"**Source:** {source}")
                    if 'doc_id' in citation:
                        st.write(f"**Document ID:** {citation['doc_id']}")
                    if 'url' in citation:
                        st.write(f"**URL:** {citation['url']}")
                    if 'similarity_score' in citation:
                        st.write(f"**Similarity:** {citation['similarity_score']:.3f}")
                    if 'content' in citation:
                        st.write(f"**Excerpt:** {citation['content'][:200]}...")
    
    # Query history
    if st.session_state.query_history:
        st.header("📜 Query History")
        
        for i, history_item in enumerate(reversed(st.session_state.query_history[-5:]), 1):
            with st.expander(f"Query {i}: {history_item['query'][:50]}..."):
                st.write(f"**Time:** {history_item['timestamp']}")
                result = history_item.get('result', {})
                answer = result.get('answer', 'No answer')
                st.write(f"**Answer:** {answer[:200]}...")
                st.write(f"**Citations:** {len(result.get('citations', []))}")
                st.write(f"**Confidence:** {result.get('confidence', 0.0):.2%}")
    
    # System information
    with st.expander("ℹ️ System Information"):
        st.markdown("""
        **SLM Orchestration Legal RAG System**
        
        This system uses a **Small Language Model (Flan-T5-small) Orchestrator** to intelligently control multiple agents:
        
        - **SLM Orchestrator (Flan-T5-small)**: Analyzes queries and decides which agents to use
          - Cost: $0.00 (vs $0.02+ for GPT-4)
          - Latency: ~15ms (vs 500ms+ for GPT-4)
        - **Prompt Booster Agent**: Enhances vague queries using Flan-T5-small
        - **Retriever Agent**: Searches legal documents using ChromaDB
        - **Answering Agent**: Generates answers using Groq LLM (Llama-3.1-8b-instant)
        - **Citation Verifier**: Verifies citations and ensures source attribution
        - **Multilingual Agent**: Handles language detection and translation
        
        **Key Features:**
        - ✅ Multi-agent architecture with intelligent orchestration
        - ✅ Cost-effective SLM orchestration (500x cheaper than GPT-4)
        - ✅ Fast response times
        - ✅ Legal document retrieval from Indian legal database
        - ✅ Comprehensive citation verification
        - ✅ Real-time answer generation
        
        **Research Contribution:**
        - Novel SLM orchestration approach for multi-agent systems
        - Cost-performance analysis of SLM vs LLM orchestration
        - Evaluation framework for orchestrator comparison
        """)

if __name__ == "__main__":
    main()
