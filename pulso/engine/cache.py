"""SimulationCache: SQLite-backed cache for keyword simulation results."""
import json
import re
from typing import Optional
from datetime import datetime, timedelta

from pulso.models.schemas import WorldState


class SimulationCache:
    """
    SQLite-backed cache for simulation results.
    48h TTL, max 500 entries, normalized text lookup with exact match.
    """

    CACHE_TTL_HOURS = 48
    MAX_CACHE_SIZE = 500

    def __init__(self, db_session=None):
        self._db = db_session  # SQLAlchemy session; None = in-memory dict (testing)
        self._mem: dict[str, WorldState] = {}

    def normalize(self, text: str) -> str:
        """Lowercase, strip punctuation, collapse whitespace."""
        return re.sub(r'\s+', ' ', re.sub(r'[^\w\s]', '', text.lower())).strip()

    def extract_keywords(self, text: str) -> set:
        """Extract meaningful keywords for similarity matching."""
        stopwords = {
            'el', 'la', 'de', 'en', 'y', 'a', 'que', 'los', 'las',
            'un', 'una', 'por', 'con', 'se', 'su', 'es', 'del', 'al',
            'lo', 'le', 'me', 'mi', 'tu', 'te', 'nos', 'les',
        }
        words = self.normalize(text).split()
        return {w for w in words if w not in stopwords and len(w) > 2}

    def find_similar(self, text: str) -> Optional[WorldState]:
        """Find a cached result for the normalized text."""
        key = self.normalize(text)

        if self._db is None:
            return self._mem.get(key)

        from pulso.models.db import CachedSimulation
        cutoff = datetime.utcnow() - timedelta(hours=self.CACHE_TTL_HOURS)
        row = (
            self._db.query(CachedSimulation)
            .filter(
                CachedSimulation.event_text_normalized == key,
                CachedSimulation.created_at >= cutoff,
            )
            .first()
        )
        if row is None:
            return None

        # Increment hit count
        row.hit_count += 1
        self._db.commit()

        return WorldState.model_validate_json(row.response_json)

    def store(self, text: str, world_state: WorldState) -> None:
        """Store a simulation result in the cache."""
        key = self.normalize(text)
        keywords = list(self.extract_keywords(text))

        if self._db is None:
            self._mem[key] = world_state
            return

        from pulso.models.db import CachedSimulation

        # Upsert: if already exists, update (shouldn't normally happen)
        existing = (
            self._db.query(CachedSimulation)
            .filter(CachedSimulation.event_text_normalized == key)
            .first()
        )
        if existing:
            existing.response_json = world_state.model_dump_json()
            existing.created_at = datetime.utcnow()
            existing.hit_count = 1
        else:
            row = CachedSimulation(
                event_text_normalized=key,
                event_keywords=json.dumps(keywords),
                response_json=world_state.model_dump_json(),
                hit_count=1,
                created_at=datetime.utcnow(),
            )
            self._db.add(row)

        self._db.commit()

    def add_variation(self, cached: WorldState) -> WorldState:
        """Add ±5% random variation to intensities."""
        import random
        states = [
            s.model_copy(update={
                "intensity": round(max(0.0, min(1.0, s.intensity + random.uniform(-0.05, 0.05))), 3)
            })
            for s in cached.states
        ]
        return cached.model_copy(update={"states": states})
