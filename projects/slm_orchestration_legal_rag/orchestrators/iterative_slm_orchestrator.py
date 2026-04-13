"""
Iterative SLM Orchestrator -- TRUE orchestration via step-by-step decisions.

At each step the model sees the query + history of agents already called,
and decides which agent to invoke next (or "done" to stop).  This is a
genuine orchestration loop, not a one-shot classifier.

Decision loop:
  State = {query, history=[]}
  while True:
      next_action = SLM(query, history)
      if next_action == "done" or len(history) >= MAX_STEPS:
          break
      execute(next_action)
      history.append(next_action)
"""

import logging
import os
import time
from typing import Dict, List, Any, Optional

import torch
from transformers import T5Tokenizer, T5ForConditionalGeneration

from core.base_orchestrator import BaseOrchestrator, OrchestrationDecision

logger = logging.getLogger(__name__)

VALID_AGENTS = {"booster", "retriever", "answering", "verifier"}
MAX_STEPS = 6


class IterativeSLMOrchestrator(BaseOrchestrator):
    """
    True iterative orchestrator powered by Flan-T5.

    Unlike the classifier approach (which picks one of N fixed patterns),
    this orchestrator runs a decision loop: at every step it observes the
    current state and chooses the *next* agent to call, or stops.

    Supported model sizes (all share the same architecture):
      - google/flan-t5-small  (80M)
      - google/flan-t5-base   (250M)
      - google/flan-t5-large  (780M)
      - or a local trained checkpoint path
    """

    def __init__(self, config: Dict[str, Any], model_path: Optional[str] = None):
        super().__init__(config)

        if model_path:
            path = os.path.abspath(os.path.expanduser(str(model_path)))
            self.model_name = path if os.path.isdir(path) else str(model_path)
        else:
            self.model_name = str(config.get("model_name", "google/flan-t5-small"))

        self.model: Optional[T5ForConditionalGeneration] = None
        self.tokenizer: Optional[T5Tokenizer] = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.cost_per_1k_tokens = 0.0
        self._step_latencies: List[float] = []

    # ------------------------------------------------------------------ init
    def _base_model_for_path(self, path: str) -> str:
        p = path.lower().replace("\\\\", "/")
        if "iterative_large" in p or "flan-t5-large" in p:
            return "google/flan-t5-large"
        if "iterative_base" in p or "flan-t5-base" in p:
            return "google/flan-t5-base"
        return "google/flan-t5-small"

    async def initialize(self) -> bool:
        try:
            logger.info(f"Loading iterative orchestrator model: {self.model_name}")
            try:
                self.tokenizer = T5Tokenizer.from_pretrained(self.model_name)
            except (TypeError, OSError) as e:
                base_name = self._base_model_for_path(self.model_name)
                logger.info(f"Loading tokenizer from base model {base_name} (local tokenizer load failed: {e})")
                self.tokenizer = T5Tokenizer.from_pretrained(base_name)
            self.model = T5ForConditionalGeneration.from_pretrained(
                self.model_name,
                torch_dtype=torch.float32,
            )
            self.model.to(self.device)
            self.model.eval()
            logger.info(f"Iterative orchestrator ready on {self.device}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialise iterative orchestrator: {e}")
            return False

    # --------------------------------------------------------- query analysis
    async def analyze_query(self, query: str) -> Dict[str, Any]:
        return self._fast_analysis(query)

    # ------------------------------------------------ CORE: iterative routing
    async def route_to_agents(self, query: str, analysis: Dict) -> List[str]:
        if not self.model or not self.tokenizer:
            ok = await self.initialize()
            if not ok or not self.model:
                logger.warning("Iterative orchestrator not loaded; using fallback sequence")
                return ["retriever", "answering"]

        history: List[str] = []
        self._step_latencies = []
        total_start = time.time()

        for step_num in range(1, MAX_STEPS + 1):
            hist_str = ",".join(history) if history else "none"
            prompt = f"orchestrate: {query} | history: {hist_str}"
            allowed_now = self._allowed_actions(history)
            if not allowed_now:
                break

            step_start = time.time()
            next_action = self._predict_next(prompt, allowed_now)
            step_ms = (time.time() - step_start) * 1000
            self._step_latencies.append(step_ms)

            logger.info(
                f"  Step {step_num}: history=[{hist_str}] -> {next_action} ({step_ms:.0f}ms)"
            )

            if next_action == "done":
                break

            if next_action in VALID_AGENTS and next_action not in history:
                history.append(next_action)
            elif next_action in history:
                logger.info(f"  Skipping duplicate agent: {next_action}")
                continue
            else:
                logger.warning(f"  Unknown action '{next_action}', stopping")
                break

        if "retriever" not in history:
            history.insert(0, "retriever")
        if "answering" not in history:
            ans_pos = history.index("retriever") + 1 if "retriever" in history else len(history)
            history.insert(ans_pos, "answering")

        total_ms = (time.time() - total_start) * 1000
        self._record_decision(0.0, total_ms)
        logger.info(f"  Final sequence: {history} (total {total_ms:.0f}ms)")
        return history

    def _allowed_actions(self, history: List[str]) -> List[str]:
        """Restrict allowed actions by workflow state so we never do answering before retriever or done at step 1."""
        if not history:
            return ["booster", "retriever"]
        if "retriever" not in history:
            return ["booster", "retriever"]
        if "answering" not in history:
            return ["answering", "done"]
        return ["verifier", "done"]

    # -------------------------------------------------------- model inference
    def _predict_next(self, prompt: str, allowed: List[str]) -> str:
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            max_length=256,
            truncation=True,
            padding=True,
        ).to(self.device)

        allowed_ids = []
        for a in allowed:
            ids = self.tokenizer.encode(a, add_special_tokens=False)
            if ids:
                allowed_ids.append((a, ids[0]))
        if not allowed_ids:
            return "retriever"

        # T5 is encoder-decoder: need decoder_input_ids for forward. Use one start token.
        dec_start = self.model.config.decoder_start_token_id
        if dec_start is None:
            dec_start = self.tokenizer.pad_token_id if self.tokenizer.pad_token_id is not None else 0
        decoder_input = torch.full((1, 1), dec_start, device=self.device, dtype=torch.long)

        with torch.no_grad():
            out = self.model(
                input_ids=inputs.input_ids,
                attention_mask=inputs.get("attention_mask"),
                decoder_input_ids=decoder_input,
            )
            logits = out.logits
        next_logits = logits[:, -1, :]
        best_action = allowed[0] if allowed else "retriever"
        best_score = -1e9
        for action, tid in allowed_ids:
            if tid < next_logits.shape[1]:
                score = next_logits[0, tid].item()
                if score > best_score:
                    best_score = score
                    best_action = action
        return best_action

    # --------------------------------------------------------- fast analysis
    def _fast_analysis(self, query: str) -> Dict[str, Any]:
        q = query.lower()
        words = query.split()
        n = len(words)
        comparators = ["compare", "difference", "vs", "versus", "distinguish"]
        procedural_kw = ["how to", "procedure", "steps", "process"]
        analytical_kw = ["analyze", "analysis", "implications", "impact"]
        if any(w in q for w in comparators):
            reasoning = "comparative"
        elif any(p in q for p in procedural_kw):
            reasoning = "procedural"
        elif any(a in q for a in analytical_kw):
            reasoning = "analytical"
        else:
            reasoning = "factual"
        complexity = "simple" if n <= 6 else ("moderate" if n <= 15 else "complex")
        return {
            "complexity": complexity,
            "reasoning_type": reasoning,
            "confidence": 0.7,
        }

    # -------------------------------------------------------- interface stubs
    async def execute_workflow(self, query: str, agent_sequence: List[str]) -> Dict:
        return {"query": query, "agent_sequence": agent_sequence, "orchestrator": "IterativeSLM"}

    @property
    def cost_per_decision(self) -> float:
        return 0.0

    @property
    def requires_api(self) -> bool:
        return False

    def get_metrics(self) -> Dict[str, Any]:
        base = super().get_metrics()
        base.update({
            "model_name": self.model_name,
            "device": self.device,
            "orchestration_type": "iterative",
            "avg_steps_per_query": (
                len(self._step_latencies) if self._step_latencies else 0
            ),
            "step_latencies_ms": self._step_latencies,
        })
        return base
