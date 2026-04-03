"""Tests for Pydantic schema validation."""
import pytest
from datetime import datetime
from pulso.models.schemas import (
    Emotion, StateEmotion, EmotionSpread, WorldState,
    SimulationRequest, SimulationResponse, NewsItem, NewsFeedState,
)


class TestEmotion:
    def test_all_values(self):
        assert Emotion.ANGER == "anger"
        assert Emotion.JOY == "joy"
        assert Emotion.FEAR == "fear"
        assert Emotion.HOPE == "hope"
        assert Emotion.SADNESS == "sadness"

    def test_from_string(self):
        assert Emotion("anger") == Emotion.ANGER


class TestStateEmotion:
    def test_valid(self):
        s = StateEmotion(
            state_code="CDMX", state_name="Ciudad de México",
            emotion=Emotion.FEAR, intensity=0.7,
            description="Descripción de prueba.",
            wave_order=0, latitude=19.4326, longitude=-99.1332,
            population_weight=1.0,
        )
        assert s.state_code == "CDMX"
        assert s.intensity == 0.7

    def test_intensity_upper_bound(self):
        with pytest.raises(Exception):
            StateEmotion(
                state_code="X", state_name="X", emotion=Emotion.FEAR,
                intensity=1.5, description="X", wave_order=0,
                latitude=0, longitude=0, population_weight=0.5,
            )

    def test_intensity_lower_bound(self):
        with pytest.raises(Exception):
            StateEmotion(
                state_code="X", state_name="X", emotion=Emotion.FEAR,
                intensity=-0.1, description="X", wave_order=0,
                latitude=0, longitude=0, population_weight=0.5,
            )

    def test_description_max_length(self):
        with pytest.raises(Exception):
            StateEmotion(
                state_code="X", state_name="X", emotion=Emotion.FEAR,
                intensity=0.5, description="A" * 121,
                wave_order=0, latitude=0, longitude=0, population_weight=0.5,
            )

    def test_wave_order_max(self):
        with pytest.raises(Exception):
            StateEmotion(
                state_code="X", state_name="X", emotion=Emotion.FEAR,
                intensity=0.5, description="X", wave_order=6,
                latitude=0, longitude=0, population_weight=0.5,
            )

    def test_wave_order_valid_range(self):
        for order in range(6):
            s = StateEmotion(
                state_code="X", state_name="X", emotion=Emotion.JOY,
                intensity=0.5, description="X", wave_order=order,
                latitude=0, longitude=0, population_weight=0.5,
            )
            assert s.wave_order == order


class TestEmotionSpread:
    def test_valid(self):
        spread = EmotionSpread(anger=0.60, joy=0.05, fear=0.20, hope=0.05, sadness=0.10)
        assert spread.anger == 0.60

    def test_value_out_of_range(self):
        with pytest.raises(Exception):
            EmotionSpread(anger=1.5, joy=0.05, fear=0.20, hope=0.05, sadness=0.10)

    def test_all_emotions_present(self):
        spread = EmotionSpread(anger=0.6, joy=0.05, fear=0.2, hope=0.05, sadness=0.1)
        assert hasattr(spread, "anger")
        assert hasattr(spread, "joy")
        assert hasattr(spread, "fear")
        assert hasattr(spread, "hope")
        assert hasattr(spread, "sadness")


class TestWorldState:
    def _make_state(self, code="CDMX", emotion="fear"):
        return StateEmotion(
            state_code=code, state_name="Test",
            emotion=Emotion(emotion), intensity=0.5,
            description="Descripción corta.",
            wave_order=0, latitude=19.0, longitude=-99.0,
            population_weight=0.5,
        )

    def test_valid(self):
        ws = WorldState(
            timestamp=datetime.utcnow(),
            states=[self._make_state()],
            spread_matrix={"CDMX": EmotionSpread(anger=0.15, joy=0.03, fear=0.55, hope=0.07, sadness=0.20)},
        )
        assert len(ws.states) == 1
        assert ws.event_source == "base"

    def test_defaults(self):
        ws = WorldState(timestamp=datetime.utcnow(), states=[], spread_matrix={})
        assert ws.event_text == ""
        assert ws.metadata == {}
        assert ws.event_source == "base"

    def test_32_states_accepted(self):
        from pulso.data.mexico_states import MEXICO_STATES
        states = [
            StateEmotion(
                state_code=s["state_code"], state_name=s["state_name"],
                emotion=Emotion(s["default_emotion"]),
                intensity=s["default_intensity"],
                description="Estado base.",
                wave_order=0,
                latitude=s["latitude"], longitude=s["longitude"],
                population_weight=s["population_weight"],
            )
            for s in MEXICO_STATES
        ]
        ws = WorldState(timestamp=datetime.utcnow(), states=states, spread_matrix={})
        assert len(ws.states) == 32


class TestSimulationRequest:
    def test_valid(self):
        req = SimulationRequest(event_text="El dólar sube a 22 pesos")
        assert req.event_text == "El dólar sube a 22 pesos"

    def test_min_length(self):
        # 3 chars is valid, 2 chars should fail
        req = SimulationRequest(event_text="abc")
        assert req.event_text == "abc"

    def test_too_short(self):
        with pytest.raises(Exception):
            SimulationRequest(event_text="ab")

    def test_too_long(self):
        with pytest.raises(Exception):
            SimulationRequest(event_text="A" * 201)


class TestSimulationResponse:
    def test_valid(self):
        ws = WorldState(timestamp=datetime.utcnow(), states=[], spread_matrix={})
        resp = SimulationResponse(world_state=ws, cached=False, processing_time_ms=42)
        assert resp.processing_time_ms == 42
        assert resp.cached is False

    def test_default_cached_false(self):
        ws = WorldState(timestamp=datetime.utcnow(), states=[], spread_matrix={})
        resp = SimulationResponse(world_state=ws, processing_time_ms=0)
        assert resp.cached is False


class TestNewsItem:
    def test_valid(self):
        item = NewsItem(
            headline="Test headline",
            source="El Universal",
            url="https://example.com",
            timestamp=datetime.utcnow(),
        )
        assert item.category == ""

    def test_with_category(self):
        item = NewsItem(
            headline="Economía crece",
            source="Reforma",
            url="https://example.com/eco",
            timestamp=datetime.utcnow(),
            category="economy",
        )
        assert item.category == "economy"


class TestNewsFeedState:
    def test_valid(self):
        feed = NewsFeedState(
            items=[],
            last_updated=datetime.utcnow(),
            active_influence=[],
        )
        assert feed.items == []
        assert feed.active_influence == []
