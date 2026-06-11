"""API-layer configuration.

Domain configuration (DATABASE_URL, GEMINI_*, CHROMA_DIR…) stays in
`app.config` — this module only adds the HTTP-layer knobs on top.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="BACKEND_", extra="ignore")

    title: str = "Finverse API"
    description: str = (
        "REST layer over the Finverse NSE intelligence engine: signals, "
        "stock analytics, peer comparison, portfolio intelligence, AI reports "
        "and RAG document Q&A."
    )
    version: str = "1.0.0"
    api_prefix: str = "/api"

    # Comma-separated in env: BACKEND_CORS_ORIGINS=http://localhost:5173,https://finverse.app
    cors_origins: str = "http://localhost:5173,http://localhost:4173"

    default_page_size: int = 12
    max_page_size: int = 100

    # Embedded news-ingestion engine (set BACKEND_ENGINE_ENABLED=false when
    # running `python -m app.main_nse` as a separate process instead).
    engine_enabled: bool = True
    engine_interval: int = 60  # seconds between ingestion sweeps

    # Daily data refresh (prices top-up after market close; financials +
    # company master weekly on Sundays). Disable with BACKEND_ETL_ENABLED=false.
    etl_enabled: bool = True
    etl_hour_ist: int = 18    # run at 18:30 IST daily
    etl_minute_ist: int = 30

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
