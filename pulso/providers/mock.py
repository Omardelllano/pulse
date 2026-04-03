"""
MockProvider: deterministic LLM provider for development.
Zero API calls. Returns realistic but fixed responses.
Each method has a pool of 5+ response variations that rotate.
"""
import asyncio
from datetime import datetime
from pulso.providers.base import BaseLLMProvider
from pulso.models.schemas import WorldState, StateEmotion, EmotionSpread
from pulso.data.fixtures import (
    BASE_STATE_POOL,
    EVENT_RESPONSE_POOL,
    NEWS_SENTIMENT_POOL,
    MODERATION_POOL,
    CONSISTENCY_POOL,
)


def _build_world_state(fixture: dict) -> WorldState:
    """Convert a fixture dict into a validated WorldState."""
    states = [StateEmotion(**s) for s in fixture["states"]]
    spread = {
        code: EmotionSpread(**probs)
        for code, probs in fixture["spread_matrix"].items()
    }
    return WorldState(
        timestamp=datetime.fromisoformat(fixture["timestamp"]),
        event_text=fixture.get("event_text", ""),
        event_source=fixture.get("event_source", "base"),
        states=states,
        spread_matrix=spread,
        metadata=fixture.get("metadata", {}),
    )


class MockProvider(BaseLLMProvider):
    """
    Deterministic provider for development. Zero API calls.
    Rotates through 5+ response variations per method call.
    """

    def __init__(self):
        self._base_state_idx = 0
        self._event_idx = 0
        self._news_idx = 0
        self._moderation_idx = 0
        self._consistency_idx = 0

    async def generate_base_state(self) -> WorldState:
        """Return next base state from pool of 5 variations."""
        fixture = BASE_STATE_POOL[self._base_state_idx % len(BASE_STATE_POOL)]
        self._base_state_idx += 1
        # Simulate async work
        await asyncio.sleep(0)
        return _build_world_state(fixture)

    async def simulate_event(self, event_text: str) -> WorldState:
        """
        Return next event simulation from pool of 6 variations.
        Rotates regardless of event_text for determinism.
        """
        fixture = EVENT_RESPONSE_POOL[self._event_idx % len(EVENT_RESPONSE_POOL)]
        self._event_idx += 1
        await asyncio.sleep(0)
        result = _build_world_state(fixture)
        # Override event_text to reflect actual user input
        return result.model_copy(update={
            "event_text": event_text,
            "timestamp": datetime.utcnow(),
        })

    async def extract_news_sentiment(self, headline: str) -> dict:
        """Return next news sentiment from pool of 6 variations."""
        result = NEWS_SENTIMENT_POOL[self._news_idx % len(NEWS_SENTIMENT_POOL)]
        self._news_idx += 1
        await asyncio.sleep(0)
        return dict(result)

    async def moderate_input(self, text: str) -> dict:
        """
        Return next moderation result from pool of 5 variations.
        First 3 are valid=True, last 2 are valid=False.
        In mock mode, always returns True unless text is empty.
        """
        if not text or len(text.strip()) < 3:
            return {"valid": False, "reason": "Texto demasiado corto."}
        result = MODERATION_POOL[self._moderation_idx % len(MODERATION_POOL)]
        self._moderation_idx += 1
        await asyncio.sleep(0)
        return dict(result)

    async def check_consistency(self, current_state: WorldState, news: list) -> WorldState:
        """Return next consistency result from pool of 5 variations."""
        result = CONSISTENCY_POOL[self._consistency_idx % len(CONSISTENCY_POOL)]
        self._consistency_idx += 1
        await asyncio.sleep(0)
        # Apply any adjustments from pool
        if result["status"] == "consistent":
            return current_state
        states = list(current_state.states)
        for adj in result["adjustments"]:
            for i, state in enumerate(states):
                if state.state_code == adj["state_code"]:
                    new_intensity = round(
                        max(0.0, min(1.0, state.intensity + adj["intensity_delta"])), 3
                    )
                    states[i] = state.model_copy(update={"intensity": new_intensity})
        return current_state.model_copy(update={"states": states})
