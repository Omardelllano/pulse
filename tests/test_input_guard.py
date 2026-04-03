"""Tests for InputGuard content moderation layers."""
import pytest
from pulso.engine.input_guard import InputGuard
from pulso.providers.mock import MockProvider


@pytest.fixture
def guard():
    return InputGuard()


@pytest.fixture
def guard_with_provider():
    return InputGuard(provider=MockProvider())


class TestInputGuardLayer1Blocklist:
    @pytest.mark.asyncio
    async def test_blocks_sex(self, guard):
        valid, reason = await guard.validate("sex videos en México")
        assert valid is False

    @pytest.mark.asyncio
    async def test_blocks_porn(self, guard):
        valid, reason = await guard.validate("porn sites en México hoy")
        assert valid is False

    @pytest.mark.asyncio
    async def test_blocks_kill(self, guard):
        valid, reason = await guard.validate("they will kill the president")
        assert valid is False

    @pytest.mark.asyncio
    async def test_blocks_bomb(self, guard):
        valid, reason = await guard.validate("a bomb exploded in Mexico City")
        assert valid is False

    @pytest.mark.asyncio
    async def test_blocks_repeated_chars(self, guard):
        valid, reason = await guard.validate("aaaaaaa esto es spam aquí")
        assert valid is False


class TestInputGuardLayer2Heuristics:
    @pytest.mark.asyncio
    async def test_too_few_words(self, guard):
        # MIN_WORDS is 2; single word should fail
        valid, reason = await guard.validate("dolar")
        assert valid is False
        assert reason != ""

    @pytest.mark.asyncio
    async def test_too_many_words(self, guard):
        text = " ".join(["palabra"] * 51)
        valid, reason = await guard.validate(text)
        assert valid is False

    @pytest.mark.asyncio
    async def test_exactly_three_words_valid(self, guard):
        valid, reason = await guard.validate("sube el dolar")
        assert valid is True

    @pytest.mark.asyncio
    async def test_accepts_valid_economic_event(self, guard):
        valid, reason = await guard.validate("El dólar sube a 22 pesos en México")
        assert valid is True

    @pytest.mark.asyncio
    async def test_accepts_valid_political_event(self, guard):
        valid, reason = await guard.validate("Nuevo presidente toma posesión en México")
        assert valid is True

    @pytest.mark.asyncio
    async def test_accepts_valid_sports_event(self, guard):
        valid, reason = await guard.validate("México gana medalla de oro en los Juegos Olímpicos")
        assert valid is True

    @pytest.mark.asyncio
    async def test_accepts_valid_disaster_event(self, guard):
        valid, reason = await guard.validate("Huracán categoría cinco impacta costas de Veracruz")
        assert valid is True


class TestInputGuardReturnFormat:
    @pytest.mark.asyncio
    async def test_returns_tuple(self, guard):
        result = await guard.validate("El dólar sube a 22 pesos")
        assert isinstance(result, tuple)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_valid_returns_empty_reason(self, guard):
        valid, reason = await guard.validate("El dólar sube a 22 pesos")
        assert valid is True
        assert reason == ""

    @pytest.mark.asyncio
    async def test_invalid_returns_nonempty_reason(self, guard):
        valid, reason = await guard.validate("ab")
        assert valid is False
        assert len(reason) > 0
