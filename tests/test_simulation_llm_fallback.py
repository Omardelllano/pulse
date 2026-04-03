"""Tests for SimulationEngine LLM fallback (P2)."""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from pulso.engine.simulation import SimulationEngine
from pulso.models.schemas import WorldState, StateEmotion, Emotion, SimulationResponse
from pulso.data.mexico_states import MEXICO_STATES


# ── Helpers ────────────────────────────────────────────────────────────────────

def make_full_world_state(method: str = "llm", event_text: str = "test") -> WorldState:
    states = [
        StateEmotion(
            state_code=s["state_code"],
            state_name=s["state_name"],
            emotion=Emotion.FEAR,
            intensity=0.60,
            description="LLM description.",
            wave_order=0,
            latitude=s["latitude"],
            longitude=s["longitude"],
            population_weight=s["population_weight"],
        )
        for s in MEXICO_STATES
    ]
    return WorldState(
        timestamp=datetime.utcnow(),
        states=states,
        spread_matrix={},
        event_text=event_text,
        event_source="user",
        metadata={"method": method, "keyword_hits": 0},
    )


def make_mock_provider(world_state: WorldState | None = None, raises: bool = False):
    provider = MagicMock()
    if raises:
        provider.simulate_event = AsyncMock(side_effect=Exception("LLM error"))
    else:
        ws = world_state or make_full_world_state()
        provider.simulate_event = AsyncMock(return_value=ws)
    return provider


# ── Tests ──────────────────────────────────────────────────────────────────────

class TestLLMFallback:
    @pytest.mark.asyncio
    async def test_llm_called_when_no_keyword_match(self):
        """An event that matches no keywords should trigger LLM fallback."""
        provider = make_mock_provider()
        engine = SimulationEngine(provider=provider)
        # Use a phrase that will NOT match any keyword rule
        await engine.simulate("Un cometa pasó cerca de la luna esta noche")
        provider.simulate_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_llm_not_called_when_keyword_matches(self):
        """An event matching a keyword rule should NOT trigger LLM fallback."""
        provider = make_mock_provider()
        engine = SimulationEngine(provider=provider)
        # "dólar" matches the dollar rule → keyword_hits > 0 → no LLM
        await engine.simulate("El dólar sube a 25 pesos")
        provider.simulate_event.assert_not_called()

    @pytest.mark.asyncio
    async def test_llm_result_used_when_no_keyword_match(self):
        """LLM result replaces keyword result when keyword_hits==0."""
        llm_state = make_full_world_state(method="llm", event_text="astronomia")
        provider = make_mock_provider(world_state=llm_state)
        engine = SimulationEngine(provider=provider)
        resp = await engine.simulate("El telescopio James Webb descubrió un exoplaneta")
        assert resp.world_state.metadata.get("method") == "llm_fallback"

    @pytest.mark.asyncio
    async def test_keyword_result_kept_when_llm_fails(self):
        """If LLM raises, keyword result is preserved."""
        provider = make_mock_provider(raises=True)
        engine = SimulationEngine(provider=provider)
        # Event with no keywords — LLM will be attempted but fail
        resp = await engine.simulate("Una ballena azul apareció en el Golfo de México")
        assert isinstance(resp, SimulationResponse)
        assert isinstance(resp.world_state, WorldState)

    @pytest.mark.asyncio
    async def test_no_llm_call_when_provider_is_none(self):
        """Without a provider, keyword-only mode is used (P1 behavior)."""
        engine = SimulationEngine(provider=None)
        resp = await engine.simulate("Terremoto de magnitud 7 en la Ciudad de México")
        assert isinstance(resp, SimulationResponse)

    @pytest.mark.asyncio
    async def test_llm_fallback_result_has_32_states(self):
        """LLM fallback should still produce 32 states."""
        llm_state = make_full_world_state()
        provider = make_mock_provider(world_state=llm_state)
        engine = SimulationEngine(provider=provider)
        resp = await engine.simulate("Una nueva especie fue descubierta en Yucatán")
        assert len(resp.world_state.states) == 32

    @pytest.mark.asyncio
    async def test_llm_fallback_cached_is_false(self):
        """First call with LLM fallback should not be cached."""
        provider = make_mock_provider()
        engine = SimulationEngine(provider=provider)
        resp = await engine.simulate("El río Grijalva alcanzó niveles históricos")
        assert resp.cached is False

    @pytest.mark.asyncio
    async def test_second_call_uses_cache_not_llm(self):
        """Second identical call should hit cache — LLM called only once."""
        provider = make_mock_provider()
        engine = SimulationEngine(provider=provider)
        # Phrase with no keywords → LLM called on first, cached on second
        text = "Una exposición de arte moderno abrió en Monterrey esta temporada"
        await engine.simulate(text)
        resp2 = await engine.simulate(text)
        assert resp2.cached is True
        assert provider.simulate_event.call_count == 1
