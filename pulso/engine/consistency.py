"""ConsistencyChecker: Prevents emotional drift (P3 implementation)."""
from pulso.models.schemas import WorldState
from pulso.providers.base import BaseLLMProvider

CONSISTENCY_CHECK_INTERVAL_HOURS = 6
CONSISTENCY_MAX_ADJUSTMENT = 0.2


class ConsistencyChecker:
    """Verifies emotional state is realistic given current news (P3)."""

    def __init__(self, provider: BaseLLMProvider):
        self.provider = provider

    async def check(self, current_state: WorldState, news: list) -> WorldState:
        """Run consistency check and apply gradual adjustments if needed."""
        return await self.provider.check_consistency(current_state, news)
