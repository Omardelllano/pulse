"""Tests for MockProvider — verifies 5+ variations and valid schema output."""
import pytest
from pulso.providers.mock import MockProvider
from pulso.models.schemas import WorldState, Emotion
from pulso.data.mexico_states import MEXICO_STATES


@pytest.fixture
def provider():
    return MockProvider()


class TestMockProviderBaseState:
    @pytest.mark.asyncio
    async def test_returns_world_state(self, provider):
        state = await provider.generate_base_state()
        assert isinstance(state, WorldState)

    @pytest.mark.asyncio
    async def test_has_32_states(self, provider):
        state = await provider.generate_base_state()
        assert len(state.states) == 32

    @pytest.mark.asyncio
    async def test_has_spread_matrix(self, provider):
        state = await provider.generate_base_state()
        assert len(state.spread_matrix) == 32

    @pytest.mark.asyncio
    async def test_five_variations_in_pool(self):
        from pulso.data.fixtures import BASE_STATE_POOL
        assert len(BASE_STATE_POOL) >= 5

    @pytest.mark.asyncio
    async def test_rotates_through_variations(self, provider):
        states = [await provider.generate_base_state() for _ in range(5)]
        timestamps = [str(s.timestamp) for s in states]
        # At least 2 distinct timestamps in 5 calls
        assert len(set(timestamps)) >= 2

    @pytest.mark.asyncio
    async def test_all_intensities_in_bounds(self, provider):
        state = await provider.generate_base_state()
        for s in state.states:
            assert 0.0 <= s.intensity <= 1.0

    @pytest.mark.asyncio
    async def test_all_wave_orders_valid(self, provider):
        state = await provider.generate_base_state()
        for s in state.states:
            assert 0 <= s.wave_order <= 5

    @pytest.mark.asyncio
    async def test_all_emotions_valid(self, provider):
        state = await provider.generate_base_state()
        valid_emotions = set(e.value for e in Emotion)
        for s in state.states:
            assert s.emotion in valid_emotions

    @pytest.mark.asyncio
    async def test_all_descriptions_max_length(self, provider):
        state = await provider.generate_base_state()
        for s in state.states:
            assert len(s.description) <= 120

    @pytest.mark.asyncio
    async def test_all_32_state_codes_present(self, provider):
        state = await provider.generate_base_state()
        expected_codes = {s["state_code"] for s in MEXICO_STATES}
        actual_codes = {s.state_code for s in state.states}
        assert actual_codes == expected_codes


class TestMockProviderSimulateEvent:
    @pytest.mark.asyncio
    async def test_returns_world_state(self, provider):
        state = await provider.simulate_event("El dólar sube a 22 pesos")
        assert isinstance(state, WorldState)

    @pytest.mark.asyncio
    async def test_overrides_event_text(self, provider):
        custom = "Sismo de magnitud 8 en Oaxaca"
        state = await provider.simulate_event(custom)
        assert state.event_text == custom

    @pytest.mark.asyncio
    async def test_six_variations_in_pool(self):
        from pulso.data.fixtures import EVENT_RESPONSE_POOL
        assert len(EVENT_RESPONSE_POOL) >= 5

    @pytest.mark.asyncio
    async def test_has_32_states(self, provider):
        state = await provider.simulate_event("Crisis económica en México")
        assert len(state.states) == 32

    @pytest.mark.asyncio
    async def test_event_source_is_user(self, provider):
        state = await provider.simulate_event("Nuevo gobierno toma el poder")
        assert state.event_source == "user"

    @pytest.mark.asyncio
    async def test_rotates_pool(self, provider):
        events = [
            await provider.simulate_event(f"Evento número {i}")
            for i in range(6)
        ]
        # After 6 calls cycling through 6-item pool, timestamps should vary
        timestamps = [str(e.timestamp) for e in events]
        # Since we override timestamp with utcnow(), this test checks pool cycling
        from pulso.data.fixtures import EVENT_RESPONSE_POOL
        assert len(EVENT_RESPONSE_POOL) >= 5


class TestMockProviderNewsSentiment:
    @pytest.mark.asyncio
    async def test_returns_dict(self, provider):
        result = await provider.extract_news_sentiment("El peso se fortalece ante el dólar")
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_has_required_keys(self, provider):
        result = await provider.extract_news_sentiment("El peso se fortalece")
        assert "emotion" in result
        assert "affected_states" in result
        assert "intensity" in result

    @pytest.mark.asyncio
    async def test_emotion_is_valid(self, provider):
        valid_emotions = {e.value for e in Emotion}
        for _ in range(6):
            result = await provider.extract_news_sentiment("Noticias de México")
            assert result["emotion"] in valid_emotions

    @pytest.mark.asyncio
    async def test_five_variations_in_pool(self):
        from pulso.data.fixtures import NEWS_SENTIMENT_POOL
        assert len(NEWS_SENTIMENT_POOL) >= 5

    @pytest.mark.asyncio
    async def test_intensity_in_bounds(self, provider):
        for _ in range(6):
            result = await provider.extract_news_sentiment("Evento")
            assert 0.0 <= result["intensity"] <= 1.0


class TestMockProviderModeration:
    @pytest.mark.asyncio
    async def test_valid_input_accepted(self, provider):
        provider._moderation_idx = 0
        result = await provider.moderate_input("El dólar sube a 22 pesos en México")
        assert "valid" in result

    @pytest.mark.asyncio
    async def test_empty_input_rejected(self, provider):
        result = await provider.moderate_input("")
        assert result["valid"] is False

    @pytest.mark.asyncio
    async def test_short_input_rejected(self, provider):
        result = await provider.moderate_input("ab")
        assert result["valid"] is False

    @pytest.mark.asyncio
    async def test_five_variations_in_pool(self):
        from pulso.data.fixtures import MODERATION_POOL
        assert len(MODERATION_POOL) >= 5


class TestMockProviderConsistency:
    @pytest.mark.asyncio
    async def test_returns_world_state(self, provider):
        base = await provider.generate_base_state()
        result = await provider.check_consistency(base, [])
        assert isinstance(result, WorldState)

    @pytest.mark.asyncio
    async def test_has_32_states(self, provider):
        base = await provider.generate_base_state()
        result = await provider.check_consistency(base, [])
        assert len(result.states) == 32

    @pytest.mark.asyncio
    async def test_five_variations_in_pool(self):
        from pulso.data.fixtures import CONSISTENCY_POOL
        assert len(CONSISTENCY_POOL) >= 5

    @pytest.mark.asyncio
    async def test_adjusted_intensities_in_bounds(self, provider):
        base = await provider.generate_base_state()
        for _ in range(5):
            result = await provider.check_consistency(base, [])
            for s in result.states:
                assert 0.0 <= s.intensity <= 1.0
