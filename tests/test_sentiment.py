"""Tests for the sentiment engine and gradual shift algorithm."""
import pytest
from pulso.engine.sentiment import apply_news_influence, SentimentEngine
from pulso.models.schemas import StateEmotion, Emotion
from pulso.providers.mock import MockProvider


def make_state(emotion="fear", intensity=0.5):
    return StateEmotion(
        state_code="CDMX", state_name="Ciudad de México",
        emotion=Emotion(emotion), intensity=intensity,
        description="Estado de prueba.", wave_order=0,
        latitude=19.4326, longitude=-99.1332,
        population_weight=1.0,
    )


class TestApplyNewsInfluence:
    def test_strong_fresh_influence_can_change_emotion(self):
        state = make_state("fear", 0.3)
        result = apply_news_influence(state, Emotion.JOY, 0.9, 0.0, 6.0)
        # Strong influence (0.9) at time=0 should override fear (0.3)
        assert result.emotion == Emotion.JOY

    def test_weak_stale_influence_keeps_emotion(self):
        state = make_state("fear", 0.9)
        result = apply_news_influence(state, Emotion.JOY, 0.1, 48.0, 6.0)
        # Very weak, very stale — should not override fear
        assert result.emotion == Emotion.FEAR

    def test_fresh_stronger_than_stale(self):
        state = make_state("fear", 0.4)
        fresh = apply_news_influence(state, Emotion.JOY, 0.8, 0.0, 6.0)
        stale = apply_news_influence(state, Emotion.JOY, 0.8, 24.0, 6.0)
        assert fresh.intensity >= stale.intensity

    def test_intensity_never_exceeds_1(self):
        state = make_state("fear", 0.99)
        result = apply_news_influence(state, Emotion.FEAR, 1.0, 0.0, 6.0)
        assert result.intensity <= 1.0

    def test_intensity_never_below_0(self):
        state = make_state("joy", 0.01)
        result = apply_news_influence(state, Emotion.ANGER, 0.5, 0.0, 6.0)
        assert result.intensity >= 0.0

    def test_same_emotion_boosts_intensity(self):
        state = make_state("fear", 0.5)
        result = apply_news_influence(state, Emotion.FEAR, 0.8, 0.0, 6.0)
        assert result.emotion == Emotion.FEAR
        assert result.intensity >= state.intensity

    def test_returns_state_emotion(self):
        state = make_state("fear", 0.5)
        result = apply_news_influence(state, Emotion.JOY, 0.5, 1.0, 6.0)
        assert isinstance(result, StateEmotion)

    def test_intensity_rounded_to_3_decimals(self):
        state = make_state("fear", 0.5)
        result = apply_news_influence(state, Emotion.JOY, 0.7, 0.0, 6.0)
        # Should be rounded to 3 decimal places
        assert result.intensity == round(result.intensity, 3)


class TestSentimentEngine:
    @pytest.mark.asyncio
    async def test_get_base_state_returns_32_states(self):
        engine = SentimentEngine(MockProvider())
        state = await engine.get_base_state()
        assert len(state.states) == 32

    @pytest.mark.asyncio
    async def test_base_state_cached(self):
        engine = SentimentEngine(MockProvider())
        state1 = await engine.get_base_state()
        state2 = await engine.get_base_state()
        # Second call returns same cached object
        assert state1.timestamp == state2.timestamp

    @pytest.mark.asyncio
    async def test_base_state_is_world_state(self):
        from pulso.models.schemas import WorldState
        engine = SentimentEngine(MockProvider())
        state = await engine.get_base_state()
        assert isinstance(state, WorldState)
