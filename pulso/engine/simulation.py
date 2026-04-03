"""
SimulationEngine: Handles user-submitted event simulations.
P2: adds LLM fallback when KeywordSimulator returns no keyword match.
"""
import logging
import time
from typing import Optional

from fastapi import HTTPException

from pulso.models.schemas import WorldState, SimulationResponse
from pulso.providers.base import BaseLLMProvider
from pulso.engine.input_guard import InputGuard
from pulso.engine.cache import SimulationCache
from pulso.engine.keyword_simulator import KeywordSimulator

logger = logging.getLogger(__name__)


class SimulationEngine:
    """
    Runs event simulations:
    InputGuard → Cache → KeywordSimulator → [LLM fallback if no keyword match]
    """

    def __init__(
        self,
        guard: InputGuard | None = None,
        cache: SimulationCache | None = None,
        simulator: KeywordSimulator | None = None,
        provider: Optional[BaseLLMProvider] = None,
    ):
        self.guard = guard or InputGuard()
        self.cache = cache or SimulationCache()
        self.simulator = simulator or KeywordSimulator()
        self.provider = provider  # None → keyword-only (P1 behavior)

    async def simulate(self, event_text: str) -> SimulationResponse:
        """
        Full simulation pipeline:
        InputGuard → Cache check → Keyword simulation → [LLM fallback] → Cache store
        """
        valid, reason = await self.guard.validate(event_text)
        if not valid:
            raise HTTPException(status_code=400, detail=reason)

        # Check cache first
        cached = self.cache.find_similar(event_text)
        if cached is not None:
            varied = self.cache.add_variation(cached)
            return SimulationResponse(
                world_state=varied,
                cached=True,
                processing_time_ms=0,
            )

        # Keyword simulation
        start = time.monotonic()
        world_state = self.simulator.simulate(event_text)

        # LLM fallback: only when no keyword matched AND a provider is configured
        keyword_hits = world_state.metadata.get("keyword_hits", 0)
        matched_rule = world_state.metadata.get("matched_rule", "default")
        logger.info(
            "[Simulate] keyword_hits=%d rule=%r text=%.60r provider=%s",
            keyword_hits, matched_rule, event_text,
            type(self.provider).__name__ if self.provider else "None",
        )

        if keyword_hits == 0 and self.provider is not None:
            logger.info("[Simulate] No keyword match — calling LLM fallback")
            try:
                world_state = await self.provider.simulate_event(event_text)
                world_state = world_state.model_copy(update={
                    "metadata": {**world_state.metadata, "method": "llm_fallback"},
                })
                logger.info("[Simulate] LLM fallback succeeded")
            except Exception as exc:
                logger.warning("[Simulate] LLM fallback failed (%s) — using keyword result", exc)

        elapsed_ms = int((time.monotonic() - start) * 1000)

        # Log top emotion for this simulation
        if world_state.states:
            top = max(world_state.states, key=lambda s: s.intensity)
            logger.info(
                "[Simulate] Result: method=%s top_state=%s emotion=%s intensity=%.2f elapsed=%dms",
                world_state.metadata.get("method", "keyword"),
                top.state_code, top.emotion.value, top.intensity, elapsed_ms,
            )

        # Store in cache
        self.cache.store(event_text, world_state)

        return SimulationResponse(
            world_state=world_state,
            cached=False,
            processing_time_ms=elapsed_ms,
        )
