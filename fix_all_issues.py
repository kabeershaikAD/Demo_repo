import re

# --- Fix 1: answering_agent.py ---
path = 'projects/slm_orchestration_legal_rag/answering_agent.py'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

# Remove time.sleep(2)
code = code.replace('        _time.sleep(2)\n        result = self._agent.generate_answer(query, query, docs)',
                     '        result = self._agent.generate_answer(query, query, docs)')

# Add _build_citations_from_docs method before _extract_final_output
build_citations_method = '''    def _build_citations_from_docs(self):
        """Build citation dicts from retrieved documents for the UI."""
        citations = []
        for d in (self._context_docs or []):
            is_web = d.get("doc_type") == "web_result"
            citations.append({
                "doc_id": d.get("doc_id", ""),
                "title": d.get("title", "Unknown Source"),
                "source": d.get("source", "") if is_web else d.get("doc_type", "database"),
                "doc_type": d.get("doc_type", "document"),
                "similarity_score": d.get("similarity_score", d.get("score", 0.0)),
                "content": d.get("content", d.get("snippet", "")),
                "url": d.get("source", "") if is_web else "",
            })
        return citations

'''

# Insert build_citations before _extract_final_output
code = code.replace(
    '    def _extract_final_output(self, answer_text, context):',
    build_citations_method + '    def _extract_final_output(self, answer_text, context):'
)

# Replace empty citations lists with _build_citations_from_docs() calls
code = code.replace(
    '            "citations": [],\n            "confidence": 0.7,\n            "claims": claims,',
    '            "citations": self._build_citations_from_docs(),\n            "confidence": 0.7,\n            "claims": claims,'
)

code = code.replace(
    '                "citations": [],\n                "confidence": 0.5,\n                "claims": self._current_claims',
    '                "citations": self._build_citations_from_docs(),\n                "confidence": 0.5,\n                "claims": self._current_claims'
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)
print('answering_agent.py patched OK')


# --- Fix 2: slm_orchestration_app.py - Pass verification details ---
path = 'projects/slm_orchestration_legal_rag/slm_orchestration_app.py'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

# Add claims_verified, total_claims, verification_issues to verifier handler
old_verifier = '                    context["verified_answer"] = result.get("verified_answer", context["answer"])\n                    context["verification_score"] = result.get("verification_score", 0.0)'
new_verifier = '                    context["verified_answer"] = result.get("verified_answer", context["answer"])\n                    context["verification_score"] = result.get("verification_score", 0.0)\n                    context["claims_verified"] = result.get("claims_verified", 0)\n                    context["total_claims"] = result.get("total_claims", 0)\n                    context["verification_issues"] = result.get("issues", [])'

code = code.replace(old_verifier, new_verifier)

# Add these fields to the return dict
old_return_end = '            "agent_sequence": agent_sequence,\n            "reasoning_traces": reasoning_traces,'
new_return_end = '            "agent_sequence": agent_sequence,\n            "reasoning_traces": reasoning_traces,\n            "claims_verified": context.get("claims_verified", 0),\n            "total_claims": context.get("total_claims", 0),\n            "verification_issues": context.get("verification_issues", []),'

code = code.replace(old_return_end, new_return_end)

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)
print('slm_orchestration_app.py patched OK')


# --- Fix 3: retriever - update task prompt to avoid unnecessary refine ---
path = 'projects/slm_orchestration_legal_rag/retriever_agent.py'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

old_task = '''        return (
            f"Retrieve relevant legal documents for: \\"{query}\\"\\n"
            f"Preferred doc type: {mode}, number of results: {k}.\\n"
            f"Search the local database first. If results are good (found relevant docs), "
            f"give Final Answer. If NO docs found or scores are very low, use search_web "
            f"to find information online, then give Final Answer."
        )'''

new_task = '''        return (
            f"Retrieve relevant legal documents for: \\"{query}\\"\\n"
            f"Preferred doc type: {mode}, number of results: {k}.\\n"
            f"Search the local database first. If results are good, give Final Answer.\\n"
            f"If NO local docs found, the system will auto-search the web.\\n"
            f"Once you have ANY results (local or web), give Final Answer immediately.\\n"
            f"Do NOT refine if web search already returned results."
        )'''

code = code.replace(old_task, new_task)

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)
print('retriever_agent.py patched OK')

print('\nAll patches applied successfully!')
