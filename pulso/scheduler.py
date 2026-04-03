"""
PULSO background scheduler.
Three asyncio loops:
  1. news_refresh_loop      — fetches RSS + runs model update (every 60 min)
  2. consistency_loop       — LLM consistency check (every 6 hours)
  3. daily_base_state_loop  — generates base state once per day (on startup if needed)

All loops are started as asyncio Tasks inside FastAPI's lifespan.
They access shared state via `app.state.*`.
"""
import asyncio
import logging
from datetime import datetime, date, timedelta, timezone

from pulso.config import settings

logger = logging.getLogger(__name__)

# Track the date the base state was last generated (in-process memory)
_last_base_state_date: date | None = None


async def daily_base_state_loop(app) -> None:
    """Generate base state on startup (if not already today) and then daily."""
    global _last_base_state_date

    # On startup: generate if we have no state or it's stale
    await _maybe_refresh_base_state(app)

    while True:
        # Sleep until next UTC midnight
        now = datetime.utcnow()
        tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        seconds_until_midnight = (tomorrow - now).total_seconds()
        logger.info("[Scheduler] Base state refresh in %.0f seconds", seconds_until_midnight)
        await asyncio.sleep(seconds_until_midnight)
        await _maybe_refresh_base_state(app)


async def _maybe_refresh_base_state(app) -> None:
    global _last_base_state_date
    today = date.today()
    if _last_base_state_date == today:
        logger.debug("[Scheduler] Base state already generated today")
        return

    # Check DB: skip LLM call if saved state is < 24 hours old
    store = _get_store(app)
    if store is not None:
        existing = store.load()
        if existing is not None:
            age_hours = (datetime.utcnow() - existing.timestamp).total_seconds() / 3600
            if age_hours < 24 and existing.event_source == "base":
                app.state.sentiment_engine._current_state = existing
                _last_base_state_date = today
                logger.info(
                    "[Scheduler] Loaded base state from DB (%.1f h old)", age_hours
                )
                return

    provider = app.state.provider
    engine = app.state.sentiment_engine
    logger.info("[Scheduler] Generating base state with %s...", type(provider).__name__)
    try:
        # Call provider directly — bypasses engine's DB cache so we get fresh LLM output
        state = await provider.generate_base_state()
        engine._current_state = state
        if store is not None:
            store.save(state, source="base")
        _last_base_state_date = today
        logger.info("[Scheduler] Base state saved (%d states)", len(state.states))
    except Exception as exc:
        logger.error("[Scheduler] Base state generation failed: %s", exc)


async def news_refresh_loop(app) -> None:
    """
    Every PULSO_NEWS_FETCH_INTERVAL_MINUTES: fetch RSS headlines (cosmetic).
    Every PULSO_NEWS_MODEL_UPDATE_MINUTES: run LLM model update.
    """
    fetch_interval = settings.news_fetch_interval_minutes * 60
    model_update_interval = settings.news_model_update_minutes * 60
    seconds_since_model_update = 0.0

    while True:
        await asyncio.sleep(fetch_interval)
        seconds_since_model_update += fetch_interval

        # Always fetch RSS (cosmetic, never raises)
        try:
            items = await app.state.news_fetcher.fetch()
            if items:
                app.state.latest_news = [_news_item_to_dict(n) for n in items]
                logger.debug("[Scheduler] Fetched %d news items", len(items))
            else:
                # All RSS sources failed — keep current or fall back to mock
                if not getattr(app.state, "latest_news", None):
                    from pulso.news.mock_headlines import MOCK_HEADLINES
                    app.state.latest_news = MOCK_HEADLINES
                    logger.info("[Scheduler] RSS empty, using mock headlines")
        except Exception as exc:
            logger.warning("[Scheduler] News fetch error: %s", exc)

        # Model update: every 60 min
        if seconds_since_model_update >= model_update_interval:
            seconds_since_model_update = 0.0
            await _run_news_model_update(app)


async def _run_news_model_update(app) -> None:
    """Apply accumulated news to current state via LLM."""
    try:
        from pulso.news.processor import NewsProcessor
        news_items = getattr(app.state, "latest_news", [])
        if not news_items:
            logger.debug("[Scheduler] No news to process")
            return

        logger.info("[Scheduler] Running news model update with %d items", len(news_items))
        processor = NewsProcessor()
        updated = await processor.process_bulk(
            news_items=news_items,
            provider=app.state.provider,
            sentiment_engine=app.state.sentiment_engine,
        )
        store = _get_store(app)
        if store is not None:
            store.save(updated, source="news")
        logger.info("[Scheduler] News model update applied")
    except Exception as exc:
        logger.error("[Scheduler] News model update failed: %s", exc)


async def consistency_loop(app) -> None:
    """Every PULSO_CONSISTENCY_CHECK_HOURS: LLM consistency check."""
    interval = settings.consistency_check_hours * 3600
    while True:
        await asyncio.sleep(interval)
        await _run_consistency_check(app)


async def _run_consistency_check(app) -> None:
    """Compare current state vs reality and apply small corrections."""
    try:
        logger.info("[Scheduler] Running consistency check...")
        engine = app.state.sentiment_engine
        current = await engine.get_base_state()
        news_items = getattr(app.state, "latest_news", [])
        adjusted = await app.state.provider.check_consistency(current, news_items)
        engine._current_state = adjusted
        store = _get_store(app)
        if store is not None:
            store.save(adjusted, source="consistency")
        logger.info("[Scheduler] Consistency check complete")
    except Exception as exc:
        logger.error("[Scheduler] Consistency check failed: %s", exc)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _get_store(app):
    """Safe access to CurrentStateStore on app.state."""
    return getattr(app.state, "state_store", None)


def _news_item_to_dict(item) -> dict:
    """Convert NewsItem dataclass or dict to plain dict."""
    if isinstance(item, dict):
        return item
    return {
        "headline": item.headline,
        "source": item.source,
        "url": item.url,
        "timestamp": item.timestamp.isoformat(),
        "sentiment": item.sentiment,
    }
