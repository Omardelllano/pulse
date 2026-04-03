"""Tests for SimulationCache."""
import pytest
from datetime import datetime
from pulso.engine.cache import SimulationCache
from pulso.models.schemas import WorldState, StateEmotion, Emotion, EmotionSpread


@pytest.fixture
def cache():
    return SimulationCache()


def make_world_state():
    state = StateEmotion(
        state_code="CDMX", state_name="Ciudad de México",
        emotion=Emotion.FEAR, intensity=0.7,
        description="Descripción de prueba.",
        wave_order=0, latitude=19.4326, longitude=-99.1332,
        population_weight=1.0,
    )
    return WorldState(
        timestamp=datetime.utcnow(),
        states=[state],
        spread_matrix={"CDMX": EmotionSpread(anger=0.15, joy=0.03, fear=0.55, hope=0.07, sadness=0.20)},
    )


class TestCacheNormalize:
    def test_lowercase(self, cache):
        assert cache.normalize("EL DÓLAR SUBE") == "el dólar sube"

    def test_strips_punctuation(self, cache):
        result = cache.normalize("¡El dólar sube!")
        assert "¡" not in result
        assert "!" not in result

    def test_strips_extra_whitespace(self, cache):
        result = cache.normalize("  el   dolar  ")
        assert result.strip() == result


class TestCacheKeywords:
    def test_extracts_keywords(self, cache):
        kw = cache.extract_keywords("El dólar sube a 22 pesos en México")
        assert "dólar" in kw
        assert "sube" in kw

    def test_removes_stopwords(self, cache):
        kw = cache.extract_keywords("El dólar sube a 22 pesos en México")
        assert "el" not in kw
        assert "en" not in kw
        assert "a" not in kw

    def test_returns_set(self, cache):
        kw = cache.extract_keywords("dólar sube dólar")
        assert isinstance(kw, set)

    def test_removes_short_words(self, cache):
        kw = cache.extract_keywords("yo lo vi")
        # "yo", "lo", "vi" are all <= 2 chars
        for w in kw:
            assert len(w) > 2


class TestCacheOperations:
    def test_find_similar_returns_none_when_empty(self, cache):
        result = cache.find_similar("El dólar sube a 22 pesos")
        assert result is None

    def test_add_variation_keeps_bounds(self, cache):
        ws = make_world_state()
        varied = cache.add_variation(ws)
        for s in varied.states:
            assert 0.0 <= s.intensity <= 1.0

    def test_add_variation_returns_world_state(self, cache):
        ws = make_world_state()
        varied = cache.add_variation(ws)
        assert isinstance(varied, WorldState)

    def test_add_variation_does_not_mutate_original(self, cache):
        ws = make_world_state()
        original_intensity = ws.states[0].intensity
        cache.add_variation(ws)
        assert ws.states[0].intensity == original_intensity
