"""Configuration management for PULSO. Loads settings from environment / .env file."""
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class Settings:
    provider: str = os.getenv("PULSO_PROVIDER", "mock")
    data_source: str = os.getenv("PULSO_DATA_SOURCE", "mock")
    port: int = int(os.getenv("PULSO_PORT", "8000"))
    host: str = os.getenv("PULSO_HOST", "0.0.0.0")
    db_path: str = os.getenv("PULSO_DB_PATH", "output/pulso.db")
    log_level: str = os.getenv("PULSO_LOG_LEVEL", "info")
    max_simulations_per_hour: int = int(os.getenv("PULSO_MAX_SIMULATIONS_PER_HOUR", "10"))
    admin_secret: str = os.getenv("PULSO_ADMIN_SECRET", "change-me-in-production")
    allowed_origins: list[str] = os.getenv(
        "PULSO_ALLOWED_ORIGINS",
        "*",
    ).split(",")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini/gemini-2.5-flash")
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    news_fetch_interval_minutes: int = int(os.getenv("PULSO_NEWS_FETCH_INTERVAL_MINUTES", "3"))
    news_model_update_minutes: int = int(os.getenv("PULSO_NEWS_MODEL_UPDATE_MINUTES", "60"))
    consistency_check_hours: int = int(os.getenv("PULSO_CONSISTENCY_CHECK_HOURS", "6"))


settings = Settings()
