from __future__ import annotations

import datetime as dt

from fastapi import APIRouter

router = APIRouter(prefix="/health")


@router.get("/live", summary="Liveness probe")
async def health_live() -> dict[str, str]:
    return {"status": "ok", "timestamp": dt.datetime.utcnow().isoformat()}


@router.get("/ready", summary="Readiness probe")
async def health_ready() -> dict[str, str]:
    return {"status": "ready"}
