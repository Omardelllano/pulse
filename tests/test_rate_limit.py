"""Tests for rate limiting middleware."""
import pytest
from fastapi.testclient import TestClient
from pulso.api.app import app
from pulso.api.middleware import reset_rate_limit, _rate_store


@pytest.fixture(autouse=True)
def clear_rate_limits():
    """Reset rate limits before each test."""
    _rate_store.clear()
    yield
    _rate_store.clear()


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


class TestRateLimitHeaders:
    def test_simulate_returns_200_on_first_request(self, client):
        response = client.post(
            "/api/simulate",
            json={"event_text": "el dólar sube mucho en México"},
        )
        assert response.status_code == 200

    def test_simulate_returns_429_after_limit(self, client):
        """After max requests, the next must return 429."""
        from pulso.config import settings
        limit = settings.max_simulations_per_hour
        payload = {"event_text": "el dólar sube mucho en México"}
        for i in range(limit):
            resp = client.post("/api/simulate", json=payload)
            assert resp.status_code == 200, f"Request {i+1} failed: {resp.status_code}"

        resp = client.post("/api/simulate", json=payload)
        assert resp.status_code == 429

    def test_rate_limit_message_in_spanish(self, client):
        from pulso.config import settings
        limit = settings.max_simulations_per_hour
        payload = {"event_text": "el dólar sube mucho en México"}
        for _ in range(limit):
            client.post("/api/simulate", json=payload)

        resp = client.post("/api/simulate", json=payload)
        assert resp.status_code == 429
        detail = resp.json()["detail"]
        assert "solicitudes" in detail.lower() or "requests" in detail.lower()

    def test_health_endpoint_not_rate_limited(self, client):
        """Health endpoint should never be rate limited."""
        for _ in range(20):
            resp = client.get("/api/health")
            assert resp.status_code == 200

    def test_state_endpoint_not_rate_limited(self, client):
        """GET /api/state should not be rate limited."""
        for _ in range(5):
            resp = client.get("/api/state")
            assert resp.status_code == 200


class TestRateLimitReset:
    def test_rate_limit_reset_clears_counter(self):
        reset_rate_limit("127.0.0.1")
        assert "127.0.0.1" not in _rate_store
