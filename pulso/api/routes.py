"""API route handlers for PULSO."""
from fastapi import APIRouter, Depends, Request

from pulso.models.schemas import SimulationRequest, SimulationResponse, WorldState
from pulso.api.security import require_admin
from pulso.config import settings

router = APIRouter()


@router.get("/health")
async def health(request: Request):
    """Health check endpoint."""
    cache = getattr(request.app.state, "sim_engine", None)
    cache_size = len(getattr(cache, "cache", None)._mem if cache else {}) if cache else 0
    try:
        cache_size = len(request.app.state.sim_engine.cache._mem)
    except Exception:
        cache_size = 0
    return {
        "status": "ok",
        "provider": settings.provider,
        "version": "0.2.0",
        "cache_size": cache_size,
    }


@router.get("/state", response_model=WorldState)
async def get_state(request: Request):
    """Return current emotional state of Mexico."""
    return await request.app.state.sentiment_engine.get_base_state()


@router.post("/simulate", response_model=SimulationResponse)
async def simulate(sim_request: SimulationRequest, request: Request):
    """
    Simulate Mexico's reaction to a user event.
    Rate limited (enforced by middleware). InputGuard validates content.
    Falls back to LLM when no keyword matches (P2).
    """
    return await request.app.state.sim_engine.simulate(sim_request.event_text)


@router.post("/state/refresh", response_model=WorldState)
async def refresh_state(request: Request, _token: str = Depends(require_admin)):
    """
    Admin: force regeneration of base state.
    Requires Authorization: Bearer {PULSO_ADMIN_SECRET}.
    """
    engine = request.app.state.sentiment_engine
    engine._current_state = None
    state = await engine.get_base_state()
    store = getattr(request.app.state, "state_store", None)
    if store is not None:
        store.save(state, source="base")
    return state


@router.get("/news")
async def get_news(request: Request):
    """Return latest news headlines (cosmetic feed)."""
    items = getattr(request.app.state, "latest_news", [])
    return {"items": items, "count": len(items)}
