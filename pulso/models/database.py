"""
Database engine factory and session management for PULSO.
SQLite with WAL mode for concurrent reads during scheduler writes.
"""
import os
import logging
from datetime import datetime
from typing import Generator, Optional

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session

from pulso.config import settings
from pulso.models.schemas import WorldState

logger = logging.getLogger(__name__)

# ── Engine ────────────────────────────────────────────────────────────────────

def _db_url() -> str:
    path = settings.db_path
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    return f"sqlite:///{path}"


engine = create_engine(
    _db_url(),
    connect_args={"check_same_thread": False},
    echo=False,
)


@event.listens_for(engine, "connect")
def _set_wal_mode(conn, _record):
    """Enable WAL journal mode for concurrent reads + writes."""
    conn.execute("PRAGMA journal_mode=WAL")


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: yields a DB session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables if they don't exist. Safe to call multiple times."""
    from pulso.models.db import Base  # import here to avoid circular imports
    Base.metadata.create_all(bind=engine)
    logger.info("[PULSO] Database initialized at %s", settings.db_path)


# ── CurrentStateStore ─────────────────────────────────────────────────────────

class CurrentStateStore:
    """
    Manages the single-row current_state table.
    Always reads/writes id=1.
    """

    def __init__(self, session: Session):
        self._db = session

    def load(self) -> Optional[WorldState]:
        """Load current state from DB. Returns None if no row exists yet."""
        from pulso.models.db import CurrentState
        row = self._db.query(CurrentState).filter(CurrentState.id == 1).first()
        if row is None:
            return None
        try:
            return WorldState.model_validate_json(row.state_json)
        except Exception as exc:
            logger.warning("[PULSO] CurrentState parse failed: %s", exc)
            return None

    def save(self, state: WorldState, source: str = "base") -> None:
        """Upsert current state (always id=1)."""
        from pulso.models.db import CurrentState
        row = self._db.query(CurrentState).filter(CurrentState.id == 1).first()
        json_str = state.model_dump_json()
        if row is None:
            row = CurrentState(id=1, state_json=json_str, updated_at=datetime.utcnow(), source=source)
            self._db.add(row)
        else:
            row.state_json = json_str
            row.updated_at = datetime.utcnow()
            row.source = source
        self._db.commit()
