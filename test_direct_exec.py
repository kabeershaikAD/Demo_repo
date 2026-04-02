import sys, os, asyncio
os.chdir(os.path.join(os.getcwd(), "projects", "slm_orchestration_legal_rag"))
sys.path.insert(0, os.getcwd())

import logging
logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")

from slm_orchestration_app import SLMOrchestrationApp

async def test():
    app = SLMOrchestrationApp(orchestrator_type="flan_t5")
    await app.initialize()
    
    print("\n" + "="*60)
    print("TEST: Simple query - What is Article 21?")
    print("="*60)
    result = await app.process_query("What is Article 21?")
    
    answer = result.get("answer", "")
    citations = result.get("citations", [])
    traces = result.get("reasoning_traces", {})
    confidence = result.get("confidence", 0)
    
    print(f"\nAnswer length: {len(answer)} chars")
    print(f"Answer preview: {answer[:300]}...")
    print(f"Citations count: {len(citations)}")
    for c in citations[:3]:
        print(f"  - {c.get('title', '?')} ({c.get('doc_type', '?')}) score={c.get('similarity_score', 0)}")
    print(f"Confidence: {confidence:.2f}")
    print(f"Agents: {result.get('agent_sequence', [])}")
    print(f"Trace agents: {list(traces.keys())}")
    for agent_name, steps in traces.items():
        print(f"  {agent_name}: {len(steps)} steps")
        for s in steps:
            print(f"    Tool: {s.get('action', '?')}, Thought: {s.get('thought', '')[:80]}")

asyncio.run(test())
