import asyncio, sys, os
os.chdir('projects/slm_orchestration_legal_rag')
sys.path.insert(0, os.getcwd())

from slm_orchestration_app import SLMOrchestrationApp

async def test():
    app = SLMOrchestrationApp(orchestrator_type='flan_t5')
    result = await app.process_query('What is Article 21 of Indian Constitution?')
    print('=== RESULT KEYS ===')
    print(list(result.keys()))
    traces = result.get('reasoning_traces', {})
    print('\n=== REASONING TRACES (%d agents) ===' % len(traces))
    for agent, steps in traces.items():
        print('\n--- %s (%d steps) ---' % (agent, len(steps)))
        for i, s in enumerate(steps, 1):
            print('  Step %d:' % i)
            t = s.get('thought', 'N/A')
            print('    Thought: %s' % t[:120])
            print('    Action: %s' % s.get('action', 'N/A'))
            obs = str(s.get('observation', ''))
            print('    Observation: %s' % obs[:120])
    ans = result.get('answer', '')
    print('\n=== ANSWER ===')
    print(ans[:300])
    print('\nConfidence: %.1f%%' % (result.get('confidence', 0) * 100))

asyncio.run(test())
