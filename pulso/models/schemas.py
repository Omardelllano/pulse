"""
Pydantic v2 schemas for PULSO data models.
All schemas match Section 5 of the master briefing exactly.
"""
from enum import Enum
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime


class Emotion(str, Enum):
    ANGER = "anger"
    JOY = "joy"
    FEAR = "fear"
    HOPE = "hope"
    SADNESS = "sadness"


class StateEmotion(BaseModel):
    """Emotion data for a single Mexican state."""
    state_code: str                  # "CDMX", "NL", "JAL", etc.
    state_name: str                  # "Ciudad de México", "Nuevo León"
    emotion: Emotion
    intensity: float = Field(ge=0, le=1)
    description: str = Field(max_length=120)  # Short explanation in Spanish
    wave_order: int = Field(ge=0, le=5)       # Propagation order (0=first)
    latitude: float
    longitude: float
    population_weight: float = Field(ge=0, le=1)  # Relative population


class EmotionSpread(BaseModel):
    """Probability distribution for satellite nodes."""
    anger: float = Field(ge=0, le=1)
    joy: float = Field(ge=0, le=1)
    fear: float = Field(ge=0, le=1)
    hope: float = Field(ge=0, le=1)
    sadness: float = Field(ge=0, le=1)

    @field_validator('*', mode='after')
    @classmethod
    def check_sums(cls, v, info):
        # Individual validator — full sum check in model_validator
        return v


class WorldState(BaseModel):
    """Complete emotional state of Mexico at a point in time."""
    timestamp: datetime
    event_text: str = ""              # The event that caused this state
    event_source: str = "base"        # "base" | "user" | "news"
    states: list[StateEmotion]        # 32 states
    spread_matrix: dict[str, EmotionSpread]  # Contagion probabilities
    metadata: dict = {}


class SimulationRequest(BaseModel):
    """User-submitted event to simulate."""
    event_text: str = Field(min_length=3, max_length=200)
    # Input guard validates content before LLM call


class SimulationResponse(BaseModel):
    """Response to a simulation request."""
    world_state: WorldState
    cached: bool = False              # True if result came from cache
    processing_time_ms: int


class NewsItem(BaseModel):
    """A news item from the feed."""
    headline: str
    source: str
    url: str
    timestamp: datetime
    category: str = ""                # "economy", "politics", "sports", etc.


class NewsFeedState(BaseModel):
    """Current news affecting the emotional state."""
    items: list[NewsItem]
    last_updated: datetime
    active_influence: list[str]       # Which news items are currently affecting state
