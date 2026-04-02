import sys, os, asyncio, time
os.chdir(os.path.join(os.getcwd(), "projects", "slm_orchestration_legal_rag"))
sys.path.insert(0, os.getcwd())

import logging
logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")

from slm_orchestration_app import SLMOrchestrationApp

async def test():
    app = SLMOrchestrationApp(orchestrator_type="flan_t5")
    await app.initialize()
    
    print("\n" + "="*60)
    print("TEST: Full pipeline query")
    print("="*60)
    
    t0 = time.time()
    result = await app.process_query("Analyze the implications of Section 498A IPC on matrimonial disputes")
    elapsed = time.time() - t0
    
    answer = result.get("answer", "")
    citations = result.get("citations", [])
    traces = result.get("reasoning_traces", {})
    v_score = result.get("verification_score")
    v_claims = result.get("claims_verified", 0)
    v_total = result.get("total_claims", 0)
    
    print(f"\nTime: {elapsed:.1f}s")
    print(f"Route: {' -> '.join(result.get('agent_sequence', []))}")
    print(f"Answer length: {len(answer)} chars")
    print(f"Answer preview: {answer[:400]}...")
    print(f"\nCitations count: {len(citations)}")
    for c in citations[:5]:
        print(f"  - {c.get('title', '?')} | type={c.get('doc_type', '?')} | score={c.get('similarity_score', 0)}")
        if c.get('url'):
            print(f"    URL: {c['url']}")
    print(f"\nVerification: {v_claims}/{v_total} claims verified, score={v_score}")
    print(f"Confidence: {result.get('confidence', 0):.2f}")
    print(f"\nAgent traces:")
    for agent_name, steps in traces.items():
        print(f"  {agent_name}: {len(steps)} steps")
        for s in steps:
            print(f"    Tool: {s.get('action', '?')}")

asyncio.run(test())
