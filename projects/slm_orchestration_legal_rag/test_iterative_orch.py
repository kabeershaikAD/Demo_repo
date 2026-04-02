import asyncio, sys
from pathlib import Path
sys.path.insert(0, str(Path(".").resolve()))
from config import config
from orchestrators.iterative_slm_orchestrator import IterativeSLMOrchestrator

async def main():
    base = Path(".").resolve()
    model_path = base / "models" / "iterative_small"
    cfg = {"openai_api_key": getattr(config.api, "OPENAI_API_KEY", "")}
    orch = IterativeSLMOrchestrator(cfg, model_path=str(model_path))
    ok = await orch.initialize()
    print("Initialize:", ok)
    if not ok: return
    for q in ["What is Article 21?", "Compare Article 14 and Article 21", "bail"]:
        a = await orch.analyze_query(q)
        seq = await orch.route_to_agents(q, a)
        print(" ", repr(q), "->", seq)
    print("OK")

asyncio.run(main())
