"""SQLAlchemy database models for PULSO."""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime


class Base(DeclarativeBase):
    pass


class CachedSimulation(Base):
    """Cached keyword simulation result."""
    __tablename__ = "simulation_cache"

    id = Column(Integer, primary_key=True)
    event_text_normalized = Column(String(500), index=True, unique=True)
    event_keywords = Column(Text)       # JSON-serialized list of keywords
    response_json = Column(Text)        # JSON-serialized WorldState
    hit_count = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)


class StateHistory(Base):
    """Historical record of emotional states."""
    __tablename__ = "state_history"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    event_text = Column(String(500))
    event_source = Column(String(50))
    state_json = Column(Text)          # JSON-serialized WorldState


class CurrentState(Base):
    """Current emotional state of Mexico (always exactly 1 row, id=1)."""
    __tablename__ = "current_state"

    id = Column(Integer, primary_key=True, default=1)
    state_json = Column(Text, nullable=False)   # JSON-serialized WorldState
    updated_at = Column(DateTime, default=datetime.utcnow)
    source = Column(String(50), default="base") # "base" | "news" | "consistency"


class RateLimit(Base):
    """Rate limit tracking per IP per endpoint."""
    __tablename__ = "rate_limits"

    ip_address = Column(String(45), primary_key=True)   # IPv4 or IPv6
    endpoint = Column(String(100), primary_key=True)
    request_count = Column(Integer, default=1)
    window_start = Column(DateTime, default=datetime.utcnow)
