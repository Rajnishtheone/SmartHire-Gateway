from __future__ import annotations

from fastapi import APIRouter, FastAPI

from ...core.config import Settings
from . import admin_users, auth, candidates, health, whatsapp


def include_all_routers(app: FastAPI, settings: Settings) -> None:
    api_router = APIRouter(prefix="/api")

    api_router.include_router(health.router, tags=["health"])
    api_router.include_router(auth.router, tags=["auth"])
    api_router.include_router(admin_users.router, tags=["admin"])
    api_router.include_router(candidates.router, tags=["candidates"])
    api_router.include_router(whatsapp.router, tags=["whatsapp"])

    app.include_router(api_router)
