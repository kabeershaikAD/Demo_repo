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
    page_icon="",
    layout="wide"
)

# Initialize session state
if "slm_app" not in st.session_state:
    st.session_state.slm_app = None
if "query_history" not in st.session_state:
    st.session_state.query_history = []
if "selected_orchestrator" not in st.session_state:
    st.session_state.selected_orchestrator = "flan_t5"

def initialize_system():
    """Initialize the SLM Orchestration App."""
    if st.session_state.slm_app is None:
        with st.spinner("Initializing SLM Orchestration Legal RAG System..."):
            orch_type = st.session_state.get("selected_orchestrator", "flan_t5")
            st.session_state.slm_app = SLMOrchestrationApp(orchestrator_type=orch_type)
            asyncio.run(st.session_state.slm_app.initialize())

def main():
    """Main Streamlit app."""
    st.title("SLM Orchestration Legal RAG System")
    st.markdown("**Multi-Agent Legal Information Retrieval with SLM Orchestration**")
    
    # Initialize system
    initialize_system()
    
    # Sidebar
    with st.sidebar:

        st.subheader("Orchestrator")
        ORCH_OPTIONS = [
            ("SLM Classifier (Flan-T5-small 80M)", "flan_t5"),
            ("Iterative SLM (80M)", "iterative_small"),
            ("Rule-based", "rule"),
            ("GPT-4 (reference)", "gpt4"),
            ("No orchestration", "none"),
        ]
        labels = [x[0] for x in ORCH_OPTIONS]
        values = [x[1] for x in ORCH_OPTIONS]
        current = st.session_state.get("selected_orchestrator", "flan_t5")
        try:
            default_idx = values.index(current)
        except ValueError:
            default_idx = 0
        chosen_label = st.selectbox("Select orchestrator", options=labels, index=default_idx, key="orch_select")
        chosen_value = values[labels.index(chosen_label)]
        if chosen_value != st.session_state.get("selected_orchestrator"):
            st.session_state.selected_orchestrator = chosen_value
            st.session_state.slm_app = None
            st.info("Orchestrator changed. Click Reinitialize or run a query.")
        st.header("System Status")
        
        if st.session_state.slm_app:
            st.metric("Active", labels[values.index(st.session_state.get("selected_orchestrator", "flan_t5"))] if st.session_state.get("selected_orchestrator") in values else "SLM Classifier (80M)")
            st.metric("Cost per Query", "$0.00")
            st.info("System Initialized")
            
            st.subheader("Available Agents")
            agents = ["booster", "retriever", "answering", "verifier", "multilingual"]
            for agent in agents:
                st.write(f"- {agent.title()}")
            
            if st.button("Reinitialize System"):
                st.session_state.slm_app = None
                initialize_system()
                st.rerun()
        
        st.header("Sample Queries")
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
        st.header("Ask a Legal Question")
        
        # Query input
        query = st.text_input(
            "Enter your legal question:",
            value=getattr(st.session_state, 'current_query', ''),
            placeholder="e.g., What is the definition of invention under patent law?"
        )
        
        if st.button("Process Query", type="primary"):
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
        st.header("SLM Orchestration Decision")
        
        # Show SLM orchestration analysis
        if hasattr(st.session_state, 'orchestration_info') and st.session_state.orchestration_info:
            orchestration = st.session_state.orchestration_info
            analysis = orchestration.get('analysis', {})
            
            # SLM Model Info
            _orch_label = {"iterative_small": "Iterative SLM (80M)", "flan_t5": "SLM Classifier (80M)", "rule": "Rule-based", "none": "No orchestration", "gpt4": "GPT-4 (reference)"}.get(st.session_state.get("selected_orchestrator", "flan_t5"), "Orchestrator"); st.info(f"**{_orch_label}** is orchestrating this query.")
            
            # Query Analysis by SLM
            st.subheader("SLM Query Analysis")
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
                st.subheader("Agent Sequence (SLM Decision)")
                sequence_str = " -> ".join([f"**{a.title()}**" for a in agent_sequence])
                st.markdown(f"{sequence_str}")
                st.caption(f"This sequence was determined by {_orch_label} orchestrator.")
            
            # Orchestration Metrics
            metrics = orchestration.get('metrics', {})
            if metrics:
                st.subheader("Performance")
                st.write(f"**Cost:** ${metrics.get('avg_cost', 0.0):.4f}")
                st.write(f"**Latency:** {metrics.get('avg_latency', 0.0):.2f}ms")
        
        elif hasattr(st.session_state, 'current_result') and st.session_state.current_result:
            result = st.session_state.current_result
            
            # Fallback: Show agents used
            agents_used = result.get('agent_sequence', result.get('agents_used', []))
            if agents_used:
                st.subheader("Agents Used")
                sequence_str = " -> ".join(agents_used)
                st.write(sequence_str)
            
            # Confidence score
            confidence = result.get('confidence', 0.0)
            st.subheader("Answer Confidence")
            st.progress(min(max(confidence, 0.0), 1.0))
            st.write(f"{confidence:.1%}")
            
            # Citations count
            citations = result.get('citations', [])
            st.subheader("Citations")
            st.write(f"**Total:** {len(citations)}")
    
    # Display SLM Orchestration Details (if available)
    if hasattr(st.session_state, 'orchestration_info') and st.session_state.orchestration_info:
        with st.expander("View SLM Orchestration Details", expanded=False):
            orchestration = st.session_state.orchestration_info
            analysis = orchestration.get('analysis', {})
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Query Analysis by Flan-T5")
                st.json({
                    "Complexity": analysis.get('complexity', 'unknown'),
                    "Reasoning Type": analysis.get('reasoning_type', 'unknown'),
                    "Requires Enhancement": analysis.get('requires_enhancement', False),
                    "Requires Verification": analysis.get('requires_verification', False),
                    "Estimated Steps": analysis.get('estimated_steps', 0),
                    "SLM Confidence": f"{analysis.get('confidence', 0.7):.1%}"
                })
            
            with col2:
                st.markdown("### Routing Decision by Flan-T5")
                st.json({
                    "Orchestrator": orchestration.get('orchestrator', 'flan_t5'),
                    "Agent Sequence": orchestration.get('agent_sequence', []),
                    "Decision Model": "Flan-T5-small (80M parameters)",
                    "Cost": "$0.00",
                    "Latency": f"{orchestration.get('metrics', {}).get('avg_latency', 0):.2f}ms"
                })
            
            st.info("This shows that the SLM orchestrator is analyzing the query and deciding which agents to use.")
    
    # Display results
    if hasattr(st.session_state, 'current_result') and st.session_state.current_result:
        result = st.session_state.current_result
        
        st.header("Answer")
        answer = result.get('answer', 'No answer generated')
        st.write(answer)
        
        # Citations / Retrieved Sources
        citations = result.get('citations', [])
        if not citations:
            citations = result.get('documents', [])
        if citations:
            st.header("Sources & Citations")
            for i, citation in enumerate(citations, 1):
                title = citation.get('title', citation.get('text', 'Unknown Source'))
                doc_type = citation.get('doc_type', 'document')
                is_web = doc_type == 'web_result'
                source_label = citation.get('source', doc_type)
                icon = "🌐" if is_web else "📄"
                
                with st.expander(f"{icon} Source {i}: {title}"):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.write(f"**Type:** {doc_type}")
                        if citation.get('doc_id'):
                            st.write(f"**Document ID:** {citation['doc_id']}")
                    with col_b:
                        sim = citation.get('similarity_score', citation.get('score', 0))
                        if sim:
                            st.write(f"**Relevance Score:** {float(sim):.3f}")
                        st.write(f"**Source:** {source_label}")
                    url = citation.get('url', '')
                    if url and url.startswith('http'):
                        st.markdown(f"[Open Source Link]({url})")
                    content = citation.get('content', citation.get('snippet', ''))
                    if content:
                        st.markdown(f"**Excerpt:**")
                        st.caption(str(content)[:400])
    
    # Verification Results
    if hasattr(st.session_state, 'current_result') and st.session_state.current_result:
        result = st.session_state.current_result
        v_score = result.get('verification_score')
        claims_verified = result.get('claims_verified', 0)
        total_claims = result.get('total_claims', 0)
        v_issues = result.get('verification_issues', [])
        
        if v_score is not None and total_claims > 0:
            st.header("Verification Results")
            v_col1, v_col2, v_col3 = st.columns(3)
            with v_col1:
                st.metric("Verification Score", f"{float(v_score):.1%}")
            with v_col2:
                st.metric("Claims Verified", f"{claims_verified}/{total_claims}")
            with v_col3:
                ratio = claims_verified / total_claims if total_claims > 0 else 0
                status = "Verified" if ratio >= 0.7 else ("Partial" if ratio >= 0.4 else "Low")
                st.metric("Status", status)
            
            if v_issues:
                with st.expander("Verification Issues"):
                    for issue in v_issues:
                        st.warning(str(issue))

    # Agent Reasoning Traces (ReAct)
    if hasattr(st.session_state, 'current_result') and st.session_state.current_result:
        traces = st.session_state.current_result.get('reasoning_traces', {})
        if traces:
            st.header("Agent Reasoning (ReAct Traces)")
            for agent_name, steps in traces.items():
                with st.expander(f"{agent_name} ({len(steps)} steps)", expanded=False):
                    for i, step in enumerate(steps, 1):
                        st.markdown(f"**Step {i}**")
                        st.markdown(f"**Thought:** {step.get('thought', 'N/A')}")
                        st.markdown(f"**Action:** {step.get('action', 'N/A')}")
                        action_input = step.get('action_input', {})
                        if isinstance(action_input, dict):
                            input_str = ', '.join(f"{k}={v}" for k, v in action_input.items())
                        else:
                            input_str = str(action_input)
                        st.markdown(f"**Input:** {input_str}")
                        obs = step.get('observation', '')
                        if len(str(obs)) > 300:
                            obs = str(obs)[:300] + '...'
                        st.markdown(f"**Observation:** {obs}")
                        st.divider()

    # Query history
    if st.session_state.query_history:
        st.header("Query History")
        
        for i, history_item in enumerate(reversed(st.session_state.query_history[-5:]), 1):
            with st.expander(f"Query {i}: {history_item['query'][:50]}..."):
                st.write(f"**Time:** {history_item['timestamp']}")
                result = history_item.get('result', {})
                answer = result.get('answer', 'No answer')
                st.write(f"**Answer:** {answer[:200]}...")
                st.write(f"**Citations:** {len(result.get('citations', []))}")
                st.write(f"**Confidence:** {result.get('confidence', 0.0):.2%}")
    
    # System information
    with st.expander("System Information"):
        st.markdown("""
        **SLM Orchestration Legal RAG System**
        
        This system uses a **Small Language Model (Flan-T5-small) Orchestrator** to intelligently control multiple agents:
        
        - **SLM Orchestrator (Flan-T5-small 80M)**: Analyzes queries and decides which agents to use
          - Cost: $0.00 (vs $0.02+ for GPT-4)
          - Latency: ~15ms (vs 500ms+ for GPT-4)
        - **Prompt Booster Agent**: Enhances vague queries using Flan-T5-small
        - Legal document retrieval from Indian legal database
        - **Answering Agent**: Generates answers using Groq LLM (Llama-3.1-8b-instant)
        - **Citation Verifier**: Verifies citations and ensures source attribution
        - **Multilingual Agent**: Handles language detection and translation
        
        **Key Features:**
        - Multi-agent architecture with intelligent orchestration
        - Cost-effective SLM orchestration (500x cheaper than GPT-4)
        - Fast response times
        - Legal document retrieval from Indian legal database
        - Comprehensive citation verification
        - Real-time answer generation
        
        **Research Contribution:**
        - Novel SLM orchestration approach for multi-agent systems
        - Cost-performance analysis of SLM vs LLM orchestration
        - Evaluation framework for orchestrator comparison
        """)

if __name__ == "__main__":
    main()







