from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routers import include_all_routers
from .core.config import Settings, get_settings
from .core.logging_config import configure_logging


def create_app(settings: Settings | None = None) -> FastAPI:
    """
    Build the FastAPI application.

    Parameters
    ----------
    settings:
        Optional settings object primarily used by tests to inject temporary
        configuration.
    """

    current_settings = settings or get_settings()
    configure_logging(level=current_settings.log_level)

    app = FastAPI(
        title="SmartHire Gateway API",
        description=(
            "AI-assisted resume ingestion platform with WhatsApp automation, "
            "Google Workspace storage, and recruiter tooling."
        ),
        version="0.1.0",
        debug=current_settings.debug,
        docs_url=current_settings.docs_url,
        redoc_url=current_settings.redoc_url,
        openapi_url=current_settings.openapi_url,
    )

    app.logger = logging.getLogger("smarthire.app")  # type: ignore[attr-defined]

    if current_settings.allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=current_settings.allowed_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    include_all_routers(app, current_settings)

    @app.on_event("startup")
    async def on_startup() -> None:
        if current_settings.debug:
            app.logger.info("SmartHire Gateway starting in debug mode.")

    @app.get("/", include_in_schema=False)
    async def root() -> dict[str, str]:
        return {
            "message": "SmartHire Gateway API is running.",
            "docs": current_settings.docs_url or "/docs",
        }

    return app


app = create_app()
