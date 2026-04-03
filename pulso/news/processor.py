"""
NewsProcessor: applies news sentiment to the current emotional state.
Calls extract_news_bulk for efficiency (single LLM call per batch).
"""
import logging
from datetime import datetime

from pulso.providers.base import BaseLLMProvider
from pulso.engine.sentiment import SentimentEngine, apply_news_influence
from pulso.models.schemas import WorldState, Emotion

logger = logging.getLogger(__name__)


class NewsProcessor:
    """Processes a batch of news headlines and applies them to the world state."""

    async def process_bulk(
        self,
        news_items: list,  # list of NewsItem (or dicts with "headline")
        provider: BaseLLMProvider,
        sentiment_engine: SentimentEngine,
    ) -> WorldState:
        """
        1. Extract sentiment for all headlines in one LLM call.
        2. Apply gradual shift to each affected state.
        3. Return updated WorldState (does NOT save to DB — caller does that).
        """
        if not news_items:
            return await sentiment_engine.get_base_state()

        headlines = [
            item.headline if hasattr(item, "headline") else item.get("headline", "")
            for item in news_items
        ]

        sentiments = await provider.extract_news_bulk(headlines)

        now = datetime.utcnow()
        state = await sentiment_engine.get_base_state()
        states = list(state.states)

        for i, sentiment in enumerate(sentiments):
            emotion_str = sentiment.get("emotion", "fear")
            try:
                emotion = Emotion(emotion_str)
            except ValueError:
                emotion = Emotion.FEAR
            intensity = float(sentiment.get("intensity", 0.4))
            decay_hours = float(sentiment.get("decay_hours", 6.0))
            affected = sentiment.get("affected_states", [])

            # hours_since_news: assume news just happened → 0.0
            hours_since = 0.0

            for j, s in enumerate(states):
                if not affected or s.state_code in affected:
                    states[j] = apply_news_influence(s, emotion, intensity, hours_since, decay_hours)

        updated_state = state.model_copy(update={
            "states": states,
            "event_source": "news",
            "metadata": {**state.metadata, "news_updated_at": now.isoformat()},
        })

        # Update sentiment engine's in-memory state
        sentiment_engine._current_state = updated_state
        return updated_state
