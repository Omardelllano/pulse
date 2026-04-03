"""Tests for CurrentStateStore (in-memory SQLite — no real file I/O)."""
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from pulso.models.db import Base
from pulso.models.database import CurrentStateStore
from pulso.models.schemas import WorldState, StateEmotion, Emotion, EmotionSpread
from pulso.data.mexico_states import MEXICO_STATES


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def db_session():
    """Create in-memory SQLite session for isolated tests."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def store(db_session):
    return CurrentStateStore(db_session)


def make_world_state(event_source: str = "base") -> WorldState:
    states = [
        StateEmotion(
            state_code=s["state_code"],
            state_name=s["state_name"],
            emotion=Emotion.HOPE,
            intensity=0.50,
            description="Test state.",
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
        event_source=event_source,
    )


# ── Tests ──────────────────────────────────────────────────────────────────────

class TestCurrentStateStore:
    def test_load_returns_none_when_empty(self, store):
        result = store.load()
        assert result is None

    def test_save_then_load_round_trip(self, store):
        ws = make_world_state()
        store.save(ws)
        loaded = store.load()
        assert loaded is not None
        assert isinstance(loaded, WorldState)

    def test_loaded_state_has_32_states(self, store):
        store.save(make_world_state())
        loaded = store.load()
        assert len(loaded.states) == 32

    def test_source_saved_and_retrievable(self, store):
        ws = make_world_state(event_source="base")
        store.save(ws, source="base")
        # Source is on the DB row; loaded WorldState carries event_source from JSON
        from pulso.models.db import CurrentState
        row = store._db.query(CurrentState).filter(CurrentState.id == 1).first()
        assert row.source == "base"

    def test_save_twice_overwrites(self, store):
        ws1 = make_world_state()
        ws2 = make_world_state()
        store.save(ws1)
        store.save(ws2)
        # Should still be a single row
        from pulso.models.db import CurrentState
        count = store._db.query(CurrentState).count()
        assert count == 1

    def test_loaded_state_preserves_emotion(self, store):
        ws = make_world_state()
        store.save(ws)
        loaded = store.load()
        cdmx = next(s for s in loaded.states if s.state_code == "CDMX")
        assert cdmx.emotion == Emotion.HOPE

    def test_loaded_state_preserves_intensity(self, store):
        ws = make_world_state()
        store.save(ws)
        loaded = store.load()
        cdmx = next(s for s in loaded.states if s.state_code == "CDMX")
        assert abs(cdmx.intensity - 0.50) < 0.001
