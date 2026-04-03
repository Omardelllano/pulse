"""Abstract base class for all LLM providers."""
from abc import ABC, abstractmethod
from pulso.models.schemas import WorldState


class BaseLLMProvider(ABC):
    """All LLM calls go through this interface."""

    @abstractmethod
    async def generate_base_state(self) -> WorldState:
        """Generate the daily base emotional state of Mexico."""

    @abstractmethod
    async def simulate_event(self, event_text: str) -> WorldState:
        """Simulate Mexico's reaction to a user-submitted event."""

    @abstractmethod
    async def extract_news_sentiment(self, headline: str) -> dict:
        """Extract emotion, affected states, intensity from a single headline."""

    async def extract_news_bulk(self, headlines: list[str]) -> list[dict]:
        """
        Extract sentiment for multiple headlines.
        Default implementation: call extract_news_sentiment for each.
        Providers can override for a single batched LLM call.
        """
        results = []
        for h in headlines:
            try:
                result = await self.extract_news_sentiment(h)
                results.append(result)
            except Exception:
                results.append({
                    "emotion": "fear", "affected_states": [], "intensity": 0.3, "decay_hours": 6.0
                })
        return results

    @abstractmethod
    async def moderate_input(self, text: str) -> dict:
        """Check if user input is appropriate. Returns {valid, reason}."""

    @abstractmethod
    async def check_consistency(self, current_state: WorldState, news: list) -> WorldState:
        """Verify emotional state is consistent with reality."""
