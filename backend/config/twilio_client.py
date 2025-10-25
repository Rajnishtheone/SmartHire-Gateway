from __future__ import annotations

from twilio.rest import Client

from ..app.core.config import Settings, get_settings


def create_twilio_client(settings: Settings | None = None) -> Client:
    cfg = settings or get_settings()
    if not (cfg.twilio_account_sid and cfg.twilio_auth_token):
        raise ValueError("Twilio credentials not configured")
    return Client(cfg.twilio_account_sid, cfg.twilio_auth_token)
