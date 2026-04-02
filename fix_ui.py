path = 'projects/api_interfaces/ui/legal_ui.py'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Improve the Sources & Citations section to show URLs for web results
old_sources = '''        # Citations
        citations = result.get('citations', [])
        if citations:
            st.header("Sources & Citations")
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
                        st.write(f"**Excerpt:** {citation['content'][:200]}...")'''

new_sources = '''        # Citations / Retrieved Sources
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
                        st.caption(str(content)[:400])'''

code = code.replace(old_sources, new_sources)

# 2. Add Verification Results section after the Answer
old_after_answer = '''    # Agent Reasoning Traces (ReAct)'''

new_verification_section = '''    # Verification Results
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

    # Agent Reasoning Traces (ReAct)'''

code = code.replace(old_after_answer, new_verification_section)

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)
print('legal_ui.py patched OK')
