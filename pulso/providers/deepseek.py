"""DeepSeek provider (P2 implementation)."""
from pulso.providers.base import BaseLLMProvider
from pulso.models.schemas import WorldState


class DeepSeekProvider(BaseLLMProvider):
    """DeepSeek — cheap, good quality. Implemented in P2."""

    async def generate_base_state(self) -> WorldState:
        raise NotImplementedError("DeepSeekProvider: implement in P2")

    async def simulate_event(self, event_text: str) -> WorldState:
        raise NotImplementedError("DeepSeekProvider: implement in P2")

    async def extract_news_sentiment(self, headline: str) -> dict:
        raise NotImplementedError("DeepSeekProvider: implement in P2")

    async def moderate_input(self, text: str) -> dict:
        raise NotImplementedError("DeepSeekProvider: implement in P2")

    async def check_consistency(self, current_state: WorldState, news: list) -> WorldState:
        raise NotImplementedError("DeepSeekProvider: implement in P2")
