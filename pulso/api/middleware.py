"""
Rate limiting middleware for PULSO API.
Max 10 requests/hour per IP, tracked in memory with SQLite fallback.
"""
import time
from collections import defaultdict
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from pulso.config import settings


# In-memory rate limit store: { ip: { "count": int, "window_start": float } }
_rate_store: dict[str, dict] = defaultdict(lambda: {"count": 0, "window_start": time.time()})

WINDOW_SECONDS = 3600  # 1 hour
RATE_LIMITED_PATHS = {"/api/simulate"}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Per-IP rate limiting for simulation endpoint.
    Returns 429 when limit exceeded.
    """

    async def dispatch(self, request: Request, call_next):
        if request.url.path in RATE_LIMITED_PATHS:
            ip = _get_client_ip(request)
            result = _check_rate_limit(ip)
            if result is not None:
                return result

        response = await call_next(request)
        return response


def _get_client_ip(request: Request) -> str:
    """Extract real client IP, respecting X-Forwarded-For."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _check_rate_limit(ip: str):
    """
    Check and increment rate limit counter.
    Returns JSONResponse 429 if over limit, None if allowed.
    Resets counter when hour window expires.
    """
    now = time.time()
    entry = _rate_store[ip]

    if now - entry["window_start"] >= WINDOW_SECONDS:
        entry["count"] = 0
        entry["window_start"] = now

    if entry["count"] >= settings.max_simulations_per_hour:
        return JSONResponse(
            status_code=429,
            content={"detail": f"Demasiadas solicitudes. Máximo {settings.max_simulations_per_hour} por hora."},
        )

    entry["count"] += 1
    return None


def get_rate_limit_count(ip: str) -> int:
    """Return current request count for an IP (for testing)."""
    now = time.time()
    entry = _rate_store[ip]
    if now - entry["window_start"] >= WINDOW_SECONDS:
        return 0
    return entry["count"]


def reset_rate_limit(ip: str) -> None:
    """Reset rate limit counter for an IP (for testing)."""
    if ip in _rate_store:
        del _rate_store[ip]
