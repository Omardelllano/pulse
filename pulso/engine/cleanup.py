"""
DB auto-cleanup job for PULSO.
Runs daily: removes expired cache entries, old history, stale rate limits.
Matches Section 9.2 of the master briefing.
"""
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

CLEANUP_RULES = {
    "simulation_cache": {
        "max_age_hours": 48,
        "max_entries": 500,
    },
    "state_history": {
        "max_age_days": 30,
        "max_entries": 1000,
    },
    "rate_limits": {
        "max_age_hours": 2,
    },
}


def run_cleanup(db_session) -> dict:
    """
    Run all cleanup tasks.
    Returns dict with counts of deleted rows per table.
    """
    results = {}
    now = datetime.utcnow()

    results["simulation_cache"] = _cleanup_simulation_cache(db_session, now)
    results["state_history"] = _cleanup_state_history(db_session, now)
    results["rate_limits"] = _cleanup_rate_limits(db_session, now)

    logger.info("[PULSO cleanup] %s", results)
    return results


def _cleanup_simulation_cache(db, now: datetime) -> int:
    from pulso.models.db import CachedSimulation

    deleted = 0
    rules = CLEANUP_RULES["simulation_cache"]

    # Delete entries older than TTL
    cutoff = now - timedelta(hours=rules["max_age_hours"])
    expired = db.query(CachedSimulation).filter(CachedSimulation.created_at < cutoff).all()
    for row in expired:
        db.delete(row)
        deleted += 1

    db.flush()

    # Enforce max entries — keep newest by hit_count then created_at
    count = db.query(CachedSimulation).count()
    if count > rules["max_entries"]:
        excess = count - rules["max_entries"]
        oldest = (
            db.query(CachedSimulation)
            .order_by(CachedSimulation.hit_count.asc(), CachedSimulation.created_at.asc())
            .limit(excess)
            .all()
        )
        for row in oldest:
            db.delete(row)
            deleted += 1

    db.commit()
    return deleted


def _cleanup_state_history(db, now: datetime) -> int:
    from pulso.models.db import StateHistory

    deleted = 0
    rules = CLEANUP_RULES["state_history"]

    # Delete entries older than max age
    cutoff = now - timedelta(days=rules["max_age_days"])
    expired = db.query(StateHistory).filter(StateHistory.timestamp < cutoff).all()
    for row in expired:
        db.delete(row)
        deleted += 1

    db.flush()

    # Enforce max entries
    count = db.query(StateHistory).count()
    if count > rules["max_entries"]:
        excess = count - rules["max_entries"]
        oldest = (
            db.query(StateHistory)
            .order_by(StateHistory.timestamp.asc())
            .limit(excess)
            .all()
        )
        for row in oldest:
            db.delete(row)
            deleted += 1

    db.commit()
    return deleted


def _cleanup_rate_limits(db, now: datetime) -> int:
    from pulso.models.db import RateLimit

    deleted = 0
    rules = CLEANUP_RULES["rate_limits"]
    cutoff = now - timedelta(hours=rules["max_age_hours"])

    old = db.query(RateLimit).filter(RateLimit.window_start < cutoff).all()
    for row in old:
        db.delete(row)
        deleted += 1

    db.commit()
    return deleted
