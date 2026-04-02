# PEARL Multi-Agent System: Complete Reference

This document explains **what each agent does**, **how they communicate**, **the end-to-end flow**, **how each agent is built**, **capabilities**, **resources**, and **what each function does**.

---

## 1. High-Level Architecture

User Query -> ORCHESTRATOR (analyze_query, route_to_agents) -> agent_sequence
-> _execute_agent_workflow: for each agent, adapter.process(...), update shared context
-> Answer + citations + confidence

Orchestrator decides WHICH agents run and in what order. Adapters wrap each agent with async process(...). One shared context dict (query, documents, answer, citations) is updated after each agent.

---

## 2. Agent Communication and Flow

- No direct agent-to-agent calls. The APP holds shared context and runs the orchestrator, then runs the agent sequence in order.
- Each agent is invoked via its ADAPTER (agent_adapters.py). The app passes the right inputs from context and writes adapter outputs back into context.
- Flow is linear: query -> (optional booster) -> retriever -> (optional multilingual) -> answering -> (optional verifier).

**Per-agent:** booster: query -> enhanced_query. retriever: (enhanced_)query -> documents. answering: query, documents -> answer, citations, confidence. verifier: answer, citations -> verified_answer, verification_score. multilingual: query -> language, translated_query.

---

## 3. Each Agent in Detail

### 3.1 Booster (booster_agent.py, PromptBooster)
**Role:** Improves vague/short legal queries for better retrieval.
**Main:** generate_decision(query) -> BoosterDecision (need_boost, boosted_query, retrieval_mode, top_k, require_human_review). Uses Flan-T5 JSON generation or rule-based fallback. _create_boosted_query has Indian law patterns (377, privacy, murder, IPC, etc.).
**Resources:** Flan-T5-small (optional), config BOOSTER_MODEL_NAME, BOOSTER_FORCE_RULE_BASED.
**Adapter:** Expects enhance_query(query); booster has generate_decision only -> adapter fallback returns query as boosted_query.

### 3.2 Retriever (retriever_agent.py, RetrieverAgent)
**Role:** Vector search over ChromaDB; classifies statute vs judgment; extracts citations; cross-links statutes-judgments.
**Main:** retrieve(query, k=5, filters) -> RetrievalResult (statutes, judgments, cross_links). CitationExtractor (regex), CrossLinker (citation overlap).
**Resources:** ChromaDB (langchain collection), OpenAI or HuggingFace embeddings, config CHROMA_DB_PATH, USE_LOCAL_EMBEDDINGS.
**Adapter:** Calls retrieve(query, k=5), merges statutes+judgments to documents list, returns dict with documents, scores, metadata.

### 3.3 Answering (answering_agent.py, AnsweringAgent)
**Role:** LLM-based legal answer with citations; claim extraction; confidence and human_review flag.
**Main:** generate_answer(user_query, enhanced_query, retrieved_docs) -> answer_text, claims, sources, confidence_score, human_review_required. Uses Groq (e.g. llama-3.1-8b-instant), system+user prompt, _extract_claims_from_response, _extract_sources, _calculate_confidence_score.
**Resources:** config GROQ_API_KEY, LLM_ANSWERING_MODEL.
**Adapter:** Calls generate_answer(query, query, documents), returns answer, citations (sources), confidence.

### 3.4 Citation Verifier (citation_verifier.py, CitationVerifier)
**Role:** Verifies claims against retrieved docs via semantic (and keyword fallback) similarity.
**Main:** verify(claims, retrieved_docs) -> list of verified claims (supported, confidence, best_doc, supporting_docs). _compute_document_embeddings, _verify_single_claim (cosine similarity), _verify_with_keywords. If no claims, _verify_document_quality.
**Resources:** SentenceTransformer (preferred) or OpenAI embeddings, config CITATION_THRESHOLD, CITATION_VERIFICATION_MODEL.
**Adapter:** Converts citations to claims, calls verify(claims, citations as docs), returns verified_answer, verification_score, claims_verified, total_claims, issues.

### 3.5 Multilingual (multilingual_agent.py, MultilingualAgent)
**Role:** Language detection (Indian scripts) and translation to English (design); translation not wired.
**Main:** process_query(query, user_language) -> processed_query, detected_language, etc. detect_language (_detect_script Unicode ranges), translate_text (_fallback_translation placeholder).
**Resources:** Translation model names in config but not loaded; script-based detection only.
**Adapter:** Expects detect_and_translate(query); agent has process_query -> adapter fallback returns language=en, translated_query=query.

---

## 4. Adapter summary (agent_adapters.py)
BoosterAdapter: enhance_query -> boosted_query (else query). RetrieverAdapter: retrieve -> documents. AnsweringAdapter: generate_answer -> answer, citations, confidence. VerifierAdapter: verify -> verified_answer, verification_score. MultilingualAdapter: detect_and_translate -> language, translated_query (else en, query). All expose async process(...) and initialize().

---

## 5. Orchestrator
analyze_query(query) -> complexity, reasoning_type, confidence. route_to_agents(query, analysis) -> agent_sequence. Implementations: iterative SLM (step-wise, context-aware allowed actions), rule, none, flan_t5, gpt4, gpt35.

---

## 6. Config (config.py)
ModelConfig, DatabaseConfig, RetrievalConfig, APIConfig, etc. Agents read these; each initializes its own clients (Chroma, embeddings, LLM).
