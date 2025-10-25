from __future__ import annotations

import json
from pathlib import Path

from google.oauth2.service_account import Credentials

from ..app.core.config import Settings, get_settings


def create_service_account_credentials(settings: Settings | None = None, scopes: list[str] | None = None) -> Credentials:
    cfg = settings or get_settings()
    if not cfg.google_service_account_json:
        raise ValueError("Google service account JSON not configured")
    data = cfg.google_service_account_json
    path = Path(data)
    if path.exists():
        info = json.loads(path.read_text())
    else:
        info = json.loads(data)
    return Credentials.from_service_account_info(info, scopes=scopes or [])
