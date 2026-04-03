"""Tests for FastAPI application (importability and structure)."""
import pytest
from fastapi.testclient import TestClient
from pulso.api.middleware import _rate_store


@pytest.fixture(autouse=True)
def clear_rate_limits():
    _rate_store.clear()
    yield
    _rate_store.clear()


@pytest.fixture
def client():
    from pulso.api.app import app
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


class TestAppImports:
    def test_app_importable(self):
        from pulso.api.app import app
        assert app is not None

    def test_router_importable(self):
        from pulso.api.routes import router
        assert router is not None

    def test_app_has_routes(self):
        from pulso.api.app import app
        routes = [r.path for r in app.routes]
        assert "/api/health" in routes

    def test_app_has_simulate_route(self):
        from pulso.api.app import app
        routes = [r.path for r in app.routes]
        assert "/api/simulate" in routes

    def test_app_has_state_route(self):
        from pulso.api.app import app
        routes = [r.path for r in app.routes]
        assert "/api/state" in routes


class TestHealthEndpoint:
    def test_health_returns_dict(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict)
        assert data["status"] == "ok"
        assert "provider" in data

    def test_health_provider_matches_settings(self, client):
        from pulso.config import settings
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json()["provider"] == settings.provider

    def test_health_has_cache_size(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert "cache_size" in resp.json()


class TestSimulateEndpoint:
    def test_simulate_returns_world_state(self, client):
        resp = client.post(
            "/api/simulate",
            json={"event_text": "el dólar sube mucho en México"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "world_state" in data
        assert "cached" in data
        assert "processing_time_ms" in data

    def test_simulate_rejects_nsfw(self, client):
        resp = client.post(
            "/api/simulate",
            json={"event_text": "xxx porn site"},
        )
        assert resp.status_code == 400

    def test_simulate_rejects_too_short(self, client):
        resp = client.post(
            "/api/simulate",
            json={"event_text": "hola"},
        )
        # "hola" is 1 word → rejected by InputGuard MIN_WORDS=2
        assert resp.status_code in (400, 422)

    def test_simulate_second_call_cached(self, client):
        payload = {"event_text": "el dólar sube mucho en México"}
        client.post("/api/simulate", json=payload)
        resp2 = client.post("/api/simulate", json=payload)
        assert resp2.status_code == 200
        assert resp2.json()["cached"] is True

    def test_simulate_world_state_has_32_states(self, client):
        resp = client.post(
            "/api/simulate",
            json={"event_text": "sismo en la ciudad de México"},
        )
        assert resp.status_code == 200
        states = resp.json()["world_state"]["states"]
        assert len(states) == 32


class TestAdminEndpoint:
    def test_refresh_without_token_returns_401(self, client):
        resp = client.post("/api/state/refresh")
        assert resp.status_code == 401

    def test_refresh_with_wrong_token_returns_401(self, client):
        resp = client.post(
            "/api/state/refresh",
            headers={"Authorization": "Bearer wrong-token"},
        )
        assert resp.status_code == 401

    def test_refresh_with_correct_token_returns_200(self, client):
        from pulso.config import settings
        resp = client.post(
            "/api/state/refresh",
            headers={"Authorization": f"Bearer {settings.admin_secret}"},
        )
        assert resp.status_code == 200

    def test_app_has_state_refresh_route(self):
        from pulso.api.app import app
        routes = [r.path for r in app.routes]
        assert "/api/state/refresh" in routes


class TestNewsEndpoint:
    def test_news_returns_dict(self, client):
        resp = client.get("/api/news")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "count" in data

    def test_news_count_matches_items(self, client):
        resp = client.get("/api/news")
        data = resp.json()
        assert data["count"] == len(data["items"])

    def test_app_has_news_route(self):
        from pulso.api.app import app
        routes = [r.path for r in app.routes]
        assert "/api/news" in routes
