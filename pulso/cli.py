"""Click CLI for PULSO."""
import asyncio
import os
import click


def _build_provider(provider_name: str):
    if provider_name == "gemini-free":
        from pulso.providers.gemini import GeminiFreeProvider
        return GeminiFreeProvider()
    elif provider_name == "deepseek":
        from pulso.providers.deepseek import DeepSeekProvider
        return DeepSeekProvider()
    else:
        from pulso.providers.mock import MockProvider
        return MockProvider()


@click.group()
def cli():
    """PULSO — The living emotional map of Mexico."""


@cli.command()
@click.option("--provider", default="mock", help="LLM provider: mock | gemini-free | deepseek")
@click.option("--port", default=None, type=int, help="Port to listen on (overrides PORT env var)")
@click.option("--host", default="0.0.0.0", help="Host to bind to")
def serve(provider: str, port: int | None, host: str):
    """Start the PULSO API server."""
    import uvicorn
    os.environ["PULSO_PROVIDER"] = provider
    # Railway (and other PaaS) set PORT env var; --port flag takes precedence
    resolved_port = port or int(os.environ.get("PORT", 8000))
    from pulso.api.app import app
    click.echo(f"Starting PULSO server with provider={provider} on {host}:{resolved_port}")
    uvicorn.run(app, host=host, port=resolved_port)


@cli.command()
@click.option("--provider", default="mock", help="LLM provider: mock | gemini-free | deepseek")
def refresh(provider: str):
    """Force-refresh the base emotional state and save to DB."""
    async def _run():
        os.makedirs("output", exist_ok=True)
        from pulso.models.database import init_db, SessionLocal, CurrentStateStore
        init_db()

        p = _build_provider(provider)
        db = SessionLocal()
        try:
            store = CurrentStateStore(db)
            from pulso.engine.sentiment import SentimentEngine
            engine = SentimentEngine(p, store=store)
            engine._current_state = None  # force regeneration
            state = await engine.get_base_state()
            click.echo(f"[PULSO] Refreshed base state: {len(state.states)} states, source={state.event_source}")
            for s in sorted(state.states, key=lambda x: x.intensity, reverse=True)[:5]:
                click.echo(f"  {s.state_code:4s} {s.emotion.value:8s} {s.intensity:.2f}  {s.description[:60]}")
            click.echo(f"  ... (saved to DB)")
        finally:
            db.close()

    asyncio.run(_run())


@cli.command(name="base-state")
@click.option("--provider", default="mock", help="LLM provider to use")
def base_state(provider: str):
    """Generate and display the current base emotional state (no DB save)."""
    async def _run():
        p = _build_provider(provider)
        state = await p.generate_base_state()
        click.echo(f"Base state generated: {len(state.states)} states")
        for s in state.states[:5]:
            click.echo(f"  {s.state_code}: {s.emotion.value} ({s.intensity:.2f})")
        click.echo("  ...")
    asyncio.run(_run())


@cli.command()
@click.argument("event_text")
@click.option("--provider", default="mock", help="LLM provider to use")
def simulate(event_text: str, provider: str):
    """Simulate Mexico's reaction to an event."""
    async def _run():
        p = _build_provider(provider)
        state = await p.simulate_event(event_text)
        click.echo(f"Simulation complete: {len(state.states)} states")
        for s in state.states[:5]:
            click.echo(f"  {s.state_code}: {s.emotion.value} ({s.intensity:.2f}) — {s.description}")
    asyncio.run(_run())
