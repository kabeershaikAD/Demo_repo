# Why This Does Not Feel Agentic — and What to Do

## 1. What Is Wrong With the Current Setup

### 1.1 They Are Pipelines, Not Agents

- Real agents: Observe -> Reason -> Choose action/tool -> Act -> Observe again (loop). We have: single call in, single call out. No loop.
- Real agents: Use tools (search, API) by deciding when and how. We have: no tool layer. Retriever IS the search; no "agent calls retrieval tool."
- Real agents: Have a model in the loop (LLM decides next step). We have: only Answering uses an LLM. Booster/Retriever/Verifier/Multilingual are stateless functions.
- Real agents: Can refuse, ask for clarification, branch. We have: one fixed path; orchestrator picks sequence once, then each "agent" runs once.
- So: the system is a fixed pipeline. The "agents" are stages in that pipeline, not decision-making entities with tools and a reasoning loop.

### 1.2 No Tools Attached to Any Agent

- Retriever: ChromaDB is called inside the module. There is no "search" tool that an LLM chooses to call.
- Booster, Answering, Verifier, Multilingual: no tool-calling. They are single functions. So there is no "agent chooses which tool to use."

### 1.3 Only One Place Uses an LLM for Reasoning

- Answering: Groq LLM for final answer. Only open-ended reasoning.
- Orchestrator: SLM/LLM only to route (which modules), not to reason inside each step.
- Booster: Can use Flan-T5 but adapter does not call it (expects enhance_query; we have generate_decision).
- Retriever/Verifier/Multilingual: No LLM. Embeddings, regex, rules. So "intelligence" is only in answering and routing.

### 1.4 Things That Do Not Work Properly

- Booster: Adapter expects enhance_query(); implementation has generate_decision(). Booster logic never used in flow.
- Multilingual: Adapter expects detect_and_translate(); implementation has process_query(). Always fallback.
- Verifier: Gets citations (source dicts), not structured claims. So we verify document quality, not claim-level support.
- No feedback: Even if verifier says low confidence, we never "go back" to answering to refine. Single pass only.

## 2. Why It Is Like This

- Research focus was orchestration (which sequence of modules), not full agent framework. So design is "orchestrator + fixed modules."
- RAG is naturally a pipeline: query -> retrieve -> generate -> verify. Code followed that; one pass, one context.
- Cost/latency: Putting LLM in every step would increase cost. So LLM is only in answering (and optionally orchestrator).
- Evolution: Code grew from "RAG pipeline" to "orchestrator chooses steps." So we have pipeline steps named "agents," not a tool-using agent loop.

Bottom line: it is a pipeline with a learned router, not a multi-agent system with tools and reasoning loops.

## 3. What Can Be Done

### 3.1 Fix the Wiring (Quick)

- Booster adapter: call generate_decision(query), map BoosterDecision to boosted_query (and retrieval_mode, top_k) so booster is actually used.
- Multilingual adapter: call process_query(query), map to language, translated_query.
- Verifier: Have answering output explicit claims (list of {text, cited_doc_ids}); pass to verifier for claim-level verification.

### 3.2 Give Agents Tools

Turn each capability into a TOOL that a reasoning unit (LLM) can call:
- search_legal_docs(query, k, filters) — from Retriever
- rewrite_query(query) — from Booster
- verify_claims(claims, doc_ids) — from Verifier
- detect_language(text), translate(text, from, to) — from Multilingual

Then make the Answering agent an LLM-with-tools: "You have search_legal_docs, verify_claims, rewrite_query. Answer the legal question; you may call tools multiple times (e.g. search, then verify, then search again)." That is a ReAct-style agent: one LLM, multiple tools, loop until done.

### 3.3 Put an LLM in the Loop for Key Steps

- Retriever "agent": Not just "embed and search once." Loop: LLM "Given query and results, do we need another search (different query/filters) or done?" If another search, call search tool and repeat. So retriever becomes "reasoning over retrieval."
- Verifier "agent": LLM "Given verified/unverified claims, should we ask answering to revise?" If yes, loop back to answering with instructions. So verification can trigger refinement.

### 3.4 One "Legal Research" Agent With Tools

Define one main agent: goal = "answer the user legal question with citations." Tools: search_legal_docs, rewrite_query, verify_claims, detect_language, translate. The agent (LLM with tool-calling) can call search multiple times, rewrite then search, generate answer then verify and refine. Orchestrator becomes "invoke this research agent." That feels agentic: one agent, goal, tools, loop.

### 3.5 Orchestrator as Meta-Agent With Tools

Give orchestrator tools: run_booster(query), run_retriever(query), run_answering(query, docs), run_verifier(answer, citations). Orchestrator (LLM) decides by calling these tools in sequence or branching. It can see results (e.g. retriever returned 0 docs) and decide "call booster and retry" or "skip to answering with warning." That is plan-execute-observe.

## 4. Summary Table

| Issue | Why | What to do |
|-------|-----|------------|
| Pipeline not agents | Design was orchestrator + RAG pipeline | Add at least one loop (e.g. Answering + tools in ReAct loop) or one "research agent" with tools |
| No tools | Capabilities are inside modules, no tool layer | Expose search, rewrite, verify, translate as tools; have LLM call them |
| Only answering uses LLM | Cost and orchestration focus | Add LLM-in-loop for retrieval ("search again?") and/or verification ("refine?") |
| Booster/Multilingual broken | Adapter expects different method names | Wire adapters to generate_decision and process_query |
| Single-shot no retry | Pipeline runs each step once | Allow loops: if verification weak -> re-answer; if no docs -> boost and search again |

So: current setup is a pipeline with a learned router. To make it agentic you need: tools, at least one LLM in the loop that uses those tools, and loops (retry/refine/ask).

---
## 5. Implemented (orchestrator-driven flow only)

The app flow is **always**: orchestrator decides sequence → then that sequence is executed. No separate research agent sidelines the orchestrator.

- **BoosterAdapter:** Calls generate_decision(query) and maps to boosted_query, retrieval_mode, top_k; app passes top_k and retrieval_mode to retriever.
- **MultilingualAdapter:** Calls process_query(query) and maps to language, translated_query, confidence.
- **AnsweringAdapter:** Returns explicit claims; app stores claims in context.
- **VerifierAdapter:** Accepts optional claims and etrieved_docs for claim-level verification.
- **App workflow:** Context stores top_k, retrieval_mode after booster; retriever gets k and optional doc_type filter; verifier gets claims and documents when available.
- **CitationVerifier:** Normalizes etrieved_docs so each item is a dict (handles str or object); avoids 'str' object has no attribute get'.
- **agent_tools.py / research_agent.py** exist for possible future use but are **not** in the main flow; the orchestrator is the only driver of which agents run and in what order.

