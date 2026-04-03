"""Tests for GeminiFreeProvider (litellm mocked — no real API calls)."""
import json
from datetime import datetime
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pulso.providers.gemini import GeminiFreeProvider, _extract_json
from pulso.models.schemas import WorldState, StateEmotion, Emotion, EmotionSpread
from pulso.data.mexico_states import MEXICO_STATES


# ── Helper fixtures ────────────────────────────────────────────────────────────

def make_world_state_fixture() -> WorldState:
    """Create a WorldState with all 32 states for testing."""
    states = [
        StateEmotion(
            state_code=s["state_code"],
            state_name=s["state_name"],
            emotion=Emotion.FEAR,
            intensity=0.50,
            description="Descripción de prueba.",
            wave_order=2,
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
    )


def make_valid_states_json() -> str:
    """Generate a valid LLM response with all 32 states."""
    states = [
        {
            "state_code": s["state_code"],
            "emotion": "fear",
            "intensity": 0.50,
            "description": "Descripción de prueba.",
            "wave_order": 2,
        }
        for s in MEXICO_STATES
    ]
    return json.dumps({"states": states})


@pytest.fixture
def provider():
    return GeminiFreeProvider(api_key="test-key")


# ── _extract_json ──────────────────────────────────────────────────────────────

class TestExtractJson:
    def test_extracts_raw_json_object(self):
        text = '{"key": "value"}'
        assert _extract_json(text) == {"key": "value"}

    def test_extracts_from_code_block(self):
        text = '```json\n{"key": "value"}\n```'
        assert _extract_json(text) == {"key": "value"}

    def test_extracts_from_code_block_no_lang(self):
        text = '```\n{"key": "value"}\n```'
        assert _extract_json(text) == {"key": "value"}

    def test_extracts_array(self):
        text = '[{"a": 1}, {"b": 2}]'
        assert _extract_json(text) == [{"a": 1}, {"b": 2}]

    def test_raises_on_no_json(self):
        with pytest.raises(ValueError):
            _extract_json("No JSON here at all")

    def test_ignores_preamble_text(self):
        text = 'Here is the result:\n\n{"states": []}'
        assert _extract_json(text) == {"states": []}


# ── generate_base_state ────────────────────────────────────────────────────────

class TestGenerateBaseState:
    @pytest.mark.asyncio
    async def test_returns_world_state_on_valid_response(self, provider):
        with patch.object(provider, "_llm", new=AsyncMock(return_value=make_valid_states_json())):
            ws = await provider.generate_base_state()
        assert isinstance(ws, WorldState)
        assert len(ws.states) == 32

    @pytest.mark.asyncio
    async def test_falls_back_to_mock_on_llm_error(self, provider):
        with patch.object(provider, "_llm", new=AsyncMock(side_effect=RuntimeError("API error"))):
            ws = await provider.generate_base_state()
        assert isinstance(ws, WorldState)
        assert len(ws.states) > 0

    @pytest.mark.asyncio
    async def test_falls_back_to_mock_on_malformed_json(self, provider):
        with patch.object(provider, "_llm", new=AsyncMock(return_value="not json at all")):
            ws = await provider.generate_base_state()
        assert isinstance(ws, WorldState)

    @pytest.mark.asyncio
    async def test_fills_missing_states_with_defaults(self, provider):
        # LLM returns only 1 state — should be padded to 32
        partial = json.dumps({"states": [
            {"state_code": "CDMX", "emotion": "fear", "intensity": 0.7,
             "description": "Test", "wave_order": 0}
        ]})
        with patch.object(provider, "_llm", new=AsyncMock(return_value=partial)):
            ws = await provider.generate_base_state()
        assert len(ws.states) == 32

    @pytest.mark.asyncio
    async def test_intensity_clamped_to_01(self, provider):
        states = [
            {"state_code": s["state_code"], "emotion": "anger", "intensity": 99.0,
             "description": "test", "wave_order": 0}
            for s in MEXICO_STATES
        ]
        raw = json.dumps({"states": states})
        with patch.object(provider, "_llm", new=AsyncMock(return_value=raw)):
            ws = await provider.generate_base_state()
        for s in ws.states:
            assert 0.0 <= s.intensity <= 1.0

    @pytest.mark.asyncio
    async def test_event_source_is_base(self, provider):
        with patch.object(provider, "_llm", new=AsyncMock(return_value=make_valid_states_json())):
            ws = await provider.generate_base_state()
        assert ws.event_source == "base"


# ── simulate_event ─────────────────────────────────────────────────────────────

class TestSimulateEvent:
    @pytest.mark.asyncio
    async def test_returns_world_state(self, provider):
        with patch.object(provider, "_llm", new=AsyncMock(return_value=make_valid_states_json())):
            ws = await provider.simulate_event("sismo fuerte en CDMX")
        assert isinstance(ws, WorldState)
        assert ws.event_text == "sismo fuerte en CDMX"

    @pytest.mark.asyncio
    async def test_event_source_is_user(self, provider):
        with patch.object(provider, "_llm", new=AsyncMock(return_value=make_valid_states_json())):
            ws = await provider.simulate_event("test event")
        assert ws.event_source == "user"

    @pytest.mark.asyncio
    async def test_fallback_on_error(self, provider):
        with patch.object(provider, "_llm", new=AsyncMock(side_effect=Exception("timeout"))):
            ws = await provider.simulate_event("test event")
        assert isinstance(ws, WorldState)


# ── extract_news_bulk ──────────────────────────────────────────────────────────

class TestExtractNewsBulk:
    @pytest.mark.asyncio
    async def test_returns_list_same_length(self, provider):
        headlines = ["Sismo en CDMX", "Dólar sube", "Victoria México"]
        response = json.dumps([
            {"emotion": "fear", "affected_states": ["CDMX"], "intensity": 0.8, "decay_hours": 6.0},
            {"emotion": "anger", "affected_states": ["NL", "JAL"], "intensity": 0.7, "decay_hours": 6.0},
            {"emotion": "joy", "affected_states": [], "intensity": 0.9, "decay_hours": 4.0},
        ])
        with patch.object(provider, "_llm", new=AsyncMock(return_value=response)):
            results = await provider.extract_news_bulk(headlines)
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_invalid_emotion_replaced_with_fear(self, provider):
        response = json.dumps([
            {"emotion": "INVALID", "affected_states": [], "intensity": 0.5, "decay_hours": 6.0}
        ])
        with patch.object(provider, "_llm", new=AsyncMock(return_value=response)):
            results = await provider.extract_news_bulk(["test headline"])
        assert results[0]["emotion"] == "fear"

    @pytest.mark.asyncio
    async def test_empty_headlines_returns_empty(self, provider):
        results = await provider.extract_news_bulk([])
        assert results == []

    @pytest.mark.asyncio
    async def test_fallback_on_error(self, provider):
        with patch.object(provider, "_llm", new=AsyncMock(side_effect=Exception("err"))):
            results = await provider.extract_news_bulk(["headline"])
        assert len(results) == 1
        assert "emotion" in results[0]


# ── check_consistency ──────────────────────────────────────────────────────────

class TestCheckConsistency:
    @pytest.mark.asyncio
    async def test_returns_unchanged_when_consistent(self, provider):
        ws = make_world_state_fixture()
        response = json.dumps({"consistent": True, "adjustments": [], "reason": "ok"})
        with patch.object(provider, "_llm", new=AsyncMock(return_value=response)):
            result = await provider.check_consistency(ws, [])
        assert result is ws  # same object

    @pytest.mark.asyncio
    async def test_applies_intensity_adjustment(self, provider):
        ws = make_world_state_fixture()
        original_cdmx = next(s for s in ws.states if s.state_code == "CDMX")
        response = json.dumps({
            "consistent": False,
            "adjustments": [{"state_code": "CDMX", "intensity_delta": -0.10}],
            "reason": "test"
        })
        with patch.object(provider, "_llm", new=AsyncMock(return_value=response)):
            result = await provider.check_consistency(ws, [])
        cdmx = next(s for s in result.states if s.state_code == "CDMX")
        assert abs(cdmx.intensity - (original_cdmx.intensity - 0.10)) < 0.01

    @pytest.mark.asyncio
    async def test_caps_adjustment_at_20_percent(self, provider):
        ws = make_world_state_fixture()
        original_cdmx = next(s for s in ws.states if s.state_code == "CDMX")
        # Request delta of 0.50 — should be capped to 0.20
        response = json.dumps({
            "consistent": False,
            "adjustments": [{"state_code": "CDMX", "intensity_delta": 0.50}],
            "reason": "test"
        })
        with patch.object(provider, "_llm", new=AsyncMock(return_value=response)):
            result = await provider.check_consistency(ws, [])
        cdmx = next(s for s in result.states if s.state_code == "CDMX")
        assert cdmx.intensity <= original_cdmx.intensity + 0.20 + 0.001

    @pytest.mark.asyncio
    async def test_fallback_returns_original_on_error(self, provider):
        ws = make_world_state_fixture()
        with patch.object(provider, "_llm", new=AsyncMock(side_effect=Exception("err"))):
            result = await provider.check_consistency(ws, [])
        assert result is ws
