"""FastAPI application for PULSO."""
import asyncio
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from pulso.api.routes import router
from pulso.api.middleware import RateLimitMiddleware
from pulso.config import settings

logger = logging.getLogger(__name__)

FRONTEND_DIR = Path(__file__).parent.parent.parent / "frontend"


def _build_provider(provider_name: str):
    """Factory: return the right provider based on config."""
    if provider_name == "gemini-free":
        from pulso.providers.gemini import GeminiFreeProvider
        return GeminiFreeProvider()
    elif provider_name == "deepseek":
        from pulso.providers.deepseek import DeepSeekProvider
        return DeepSeekProvider()
    else:
        from pulso.providers.mock import MockProvider
        return MockProvider()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: init DB, build singletons, start scheduler tasks. Shutdown: cancel tasks."""
    # ── Startup ───────────────────────────────────────────────────────────────
    os.makedirs(os.path.dirname(settings.db_path) or ".", exist_ok=True)

    from pulso.models.database import init_db, SessionLocal, CurrentStateStore
    init_db()

    # Provider
    provider = _build_provider(settings.provider)
    app.state.provider = provider

    # State store + sentiment engine
    db_session = SessionLocal()
    app.state.db_session = db_session
    store = CurrentStateStore(db_session)
    app.state.state_store = store

    from pulso.engine.sentiment import SentimentEngine
    from pulso.engine.input_guard import InputGuard
    from pulso.engine.cache import SimulationCache
    from pulso.engine.keyword_simulator import KeywordSimulator
    from pulso.engine.simulation import SimulationEngine
    from pulso.news.fetcher import NewsFetcher

    sentiment_engine = SentimentEngine(provider, store=store)
    app.state.sentiment_engine = sentiment_engine

    sim_engine = SimulationEngine(
        guard=InputGuard(),
        cache=SimulationCache(),
        simulator=KeywordSimulator(),
        provider=provider,
    )
    app.state.sim_engine = sim_engine

    fetcher = NewsFetcher()
    app.state.news_fetcher = fetcher

    # Initial news fetch — populate sidebar immediately on startup
    from pulso.news.mock_headlines import MOCK_HEADLINES
    from pulso.scheduler import _news_item_to_dict
    try:
        initial_items = await fetcher.fetch()
        app.state.latest_news = [_news_item_to_dict(n) for n in initial_items]
        logger.info("[PULSO] Initial news fetch: %d items", len(initial_items))
    except Exception as exc:
        logger.warning("[PULSO] Initial news fetch failed: %s", exc)
        initial_items = []

    if not app.state.latest_news:
        app.state.latest_news = MOCK_HEADLINES
        logger.info("[PULSO] Using mock headlines as fallback")

    # Pre-cache popular simulations so first user requests are instant
    _POPULAR_EVENTS = [
        "Sismo de magnitud 7.5 sacude Ciudad de México",
        "Huracán categoría 4 amenaza costas de Yucatán",
        "México gana el Mundial de Futbol",
        "Precio del dólar supera los 25 pesos",
        "Elecciones presidenciales en México",
        "Feminicidio en Ecatepec genera protestas masivas",
        "Aumento al salario mínimo en México",
        "Inundaciones severas en Tabasco dejan miles de damnificados",
        "Incendio forestal en Jalisco arrasa miles de hectáreas",
        "México clasifica al Mundial de Futbol",
        "Violencia del crimen organizado azota Sinaloa",
        "Erupción del volcán Popocatépetl obliga evacuaciones",
        "Accidente en metro de Ciudad de México deja víctimas",
        "Economía mexicana entra en recesión",
        "Protestas estudiantiles en universidades de todo el país",
        "Sequía severa en el norte de México afecta agua potable",
        "Apagón masivo deja sin luz a millones de mexicanos",
        "Descubrimiento arqueológico en Teotihuacán",
        "México sede de los Juegos Olímpicos 2036",
        "Crisis de seguridad en Guerrero deja decenas de muertos",
    ]
    pre_cached = 0
    for event_text in _POPULAR_EVENTS:
        try:
            if sim_engine.cache.find_similar(event_text) is None:
                world_state = sim_engine.simulator.simulate(event_text)
                # Only cache events where keywords matched — skip DEFAULT_RULE results
                # so LLM fallback can generate richer responses at runtime
                if world_state.metadata.get("keyword_hits", 0) > 0:
                    sim_engine.cache.store(event_text, world_state)
                    pre_cached += 1
        except Exception:
            pass
    logger.info("[PULSO] Pre-cached %d/%d popular simulations (keyword-match only)",
                pre_cached, len(_POPULAR_EVENTS))

    # Background scheduler tasks
    from pulso.scheduler import daily_base_state_loop, news_refresh_loop, consistency_loop
    tasks = [
        asyncio.create_task(daily_base_state_loop(app)),
        asyncio.create_task(news_refresh_loop(app)),
        asyncio.create_task(consistency_loop(app)),
    ]
    app.state.scheduler_tasks = tasks

    logger.info("[PULSO] Started — provider=%s, rate_limit=%d/hour",
                settings.provider, settings.max_simulations_per_hour)

    yield

    # ── Shutdown ──────────────────────────────────────────────────────────────
    for task in app.state.scheduler_tasks:
        task.cancel()
    await asyncio.gather(*app.state.scheduler_tasks, return_exceptions=True)
    app.state.db_session.close()
    logger.info("[PULSO] Shutdown complete.")


app = FastAPI(title="PULSO API", version="0.2.0", lifespan=lifespan)

# CORS — configured via PULSO_ALLOWED_ORIGINS env var
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Rate limiting
app.add_middleware(RateLimitMiddleware)

# API routes — before static mount
app.include_router(router, prefix="/api")

# Serve frontend
if FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
