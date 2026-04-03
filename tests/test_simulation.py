"""Tests for the simulation engine pipeline (P1: keyword-based)."""
import pytest
from fastapi import HTTPException
from pulso.engine.simulation import SimulationEngine
from pulso.models.schemas import SimulationResponse, WorldState


@pytest.fixture
def engine():
    return SimulationEngine()


class TestSimulationEngine:
    @pytest.mark.asyncio
    async def test_valid_event_returns_response(self, engine):
        resp = await engine.simulate("El dólar sube a 22 pesos en México")
        assert isinstance(resp, SimulationResponse)

    @pytest.mark.asyncio
    async def test_response_has_32_states(self, engine):
        resp = await engine.simulate("El dólar sube a 22 pesos en México")
        assert len(resp.world_state.states) == 32

    @pytest.mark.asyncio
    async def test_processing_time_non_negative(self, engine):
        resp = await engine.simulate("Crisis económica en México afecta empleos")
        assert resp.processing_time_ms >= 0

    @pytest.mark.asyncio
    async def test_cached_false_on_first_call(self, engine):
        resp = await engine.simulate("Nuevo desastre natural en el sur del país")
        assert resp.cached is False

    @pytest.mark.asyncio
    async def test_cached_true_on_second_call(self, engine):
        text = "México gana el partido de futbol importante"
        await engine.simulate(text)
        resp2 = await engine.simulate(text)
        assert resp2.cached is True

    @pytest.mark.asyncio
    async def test_event_text_preserved(self, engine):
        event = "México gana el Mundial de Fútbol"
        resp = await engine.simulate(event)
        assert resp.world_state.event_text == event

    @pytest.mark.asyncio
    async def test_too_short_raises_http_400(self, engine):
        with pytest.raises(HTTPException) as exc_info:
            await engine.simulate("hola")
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_blocked_content_raises_http_400(self, engine):
        with pytest.raises(HTTPException) as exc_info:
            await engine.simulate("sex porn spam en México")
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_world_state_type(self, engine):
        resp = await engine.simulate("Sube el precio del combustible en México")
        assert isinstance(resp.world_state, WorldState)

    @pytest.mark.asyncio
    async def test_spread_matrix_present(self, engine):
        resp = await engine.simulate("Elecciones presidenciales en México")
        assert len(resp.world_state.spread_matrix) > 0
