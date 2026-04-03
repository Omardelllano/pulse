"""
SentimentEngine: Manages the base emotional state of Mexico.
P2: optionally backed by SQLite CurrentStateStore for persistence.
Handles gradual news-driven emotion shifts using exponential decay.
"""
from datetime import datetime
from typing import Optional

from pulso.models.schemas import StateEmotion, Emotion, WorldState
from pulso.providers.base import BaseLLMProvider


CONSISTENCY_CHECK_INTERVAL_HOURS = 6
CONSISTENCY_MAX_ADJUSTMENT = 0.2


def apply_news_influence(
    current: StateEmotion,
    news_emotion: Emotion,
    news_intensity: float,
    hours_since_news: float,
    decay_hours: float = 6.0,
) -> StateEmotion:
    """
    Gradually shift a state's emotion toward the news sentiment.
    Uses exponential decay so influence fades naturally.
    Matches Section 8.1 of the master briefing exactly.
    """
    decay = 2 ** (-hours_since_news / decay_hours)
    influence = news_intensity * decay

    if influence > current.intensity * 0.3:
        new_emotion = news_emotion
        new_intensity = min(1.0, current.intensity * (1 - influence) + influence)
    else:
        new_emotion = current.emotion
        if news_emotion == current.emotion:
            new_intensity = min(1.0, current.intensity + influence * 0.2)
        else:
            new_intensity = max(0.1, current.intensity - influence * 0.1)

    return current.model_copy(update={
        "emotion": new_emotion,
        "intensity": round(new_intensity, 3),
    })


class SentimentEngine:
    """
    Manages base emotional state and applies news influence.
    If a CurrentStateStore is provided, persists to DB.
    """

    def __init__(self, provider: BaseLLMProvider, store=None):
        self.provider = provider
        self._store = store  # Optional[CurrentStateStore]
        self._current_state: Optional[WorldState] = None

    async def get_base_state(self) -> WorldState:
        """
        Get current state:
        1. In-memory cache (fastest)
        2. DB store (persistent across restarts)
        3. Generate fresh from provider (one LLM call or mock)
        """
        if self._current_state is not None:
            return self._current_state

        # Try loading from DB
        if self._store is not None:
            loaded = self._store.load()
            if loaded is not None:
                self._current_state = loaded
                return self._current_state

        # Generate fresh
        self._current_state = await self.provider.generate_base_state()

        # Persist
        if self._store is not None:
            self._store.save(self._current_state, source="base")

        return self._current_state

    async def apply_news_items(self, news_items: list) -> WorldState:
        """Apply multiple news items to the current state using bulk extraction."""
        state = await self.get_base_state()
        now = datetime.utcnow()
        states = list(state.states)

        for news in news_items:
            hours_since = 0.0
            if isinstance(news, dict):
                headline = news.get("headline", "")
                ts_str = news.get("timestamp")
                if ts_str:
                    try:
                        ts = datetime.fromisoformat(ts_str)
                        hours_since = max(0.0, (now - ts).total_seconds() / 3600)
                    except Exception:
                        pass
                sentiment = news.get("sentiment") or {}
            else:
                headline = getattr(news, "headline", "")
                ts = getattr(news, "timestamp", now)
                hours_since = max(0.0, (now - ts).total_seconds() / 3600)
                sentiment = getattr(news, "sentiment", None) or {}

            if not sentiment:
                # Single-item extraction (no bulk available here)
                sentiment = await self.provider.extract_news_sentiment(headline)

            emotion = Emotion(sentiment.get("emotion", "fear"))
            intensity = float(sentiment.get("intensity", 0.4))
            decay_hours = float(sentiment.get("decay_hours", 6.0))
            affected = sentiment.get("affected_states", [])

            states = [
                apply_news_influence(s, emotion, intensity, hours_since, decay_hours)
                if not affected or s.state_code in affected else s
                for s in states
            ]

        self._current_state = state.model_copy(update={"states": states})
        return self._current_state
