from __future__ import annotations

import base64
import logging
from typing import Dict, List, Optional

import requests
from twilio.request_validator import RequestValidator
from twilio.rest import Client

from ..core.config import Settings, get_settings
from ..models.request_models import AttachmentPayload
from ..services.ingestion_service import IngestionService

logger = logging.getLogger("smarthire.whatsapp")


class WhatsAppService:
    def __init__(
        self,
        settings: Settings | None = None,
        ingestion_service: IngestionService | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.ingestion_service = ingestion_service
        self._validator = (
            RequestValidator(self.settings.twilio_auth_token)
            if self.settings.twilio_auth_token
            else None
        )
        self._client = (
            Client(self.settings.twilio_account_sid, self.settings.twilio_auth_token)
            if self.settings.twilio_account_sid and self.settings.twilio_auth_token
            else None
        )

    def validate_request(self, signature: Optional[str], url: str, payload: Dict[str, str]) -> bool:
        if not self._validator:
            logger.warning("Twilio validator not configured; accepting webhook (dev mode).")
            return True
        if not signature:
            return False
        return self._validator.validate(url, payload, signature)

    def process_incoming_message(self, payload: Dict[str, str]) -> None:
        if not self.ingestion_service:
            logger.error("Ingestion service missing; message dropped.")
            return
        body = payload.get("Body", "")
        attachments = self._extract_attachments(payload)
        record = self.ingestion_service.ingest_payload(
            source="whatsapp",
            body=body,
            attachments=attachments,
        )
        if self._client and self.settings.twilio_whatsapp_from:
            to_number = payload.get("From")
            if to_number:
                self._send_auto_reply(to_number, record.full_name or "there")

    def _extract_attachments(self, payload: Dict[str, str]) -> List[AttachmentPayload]:
        count = int(payload.get("NumMedia", "0") or "0")
        attachments: List[AttachmentPayload] = []
        for index in range(count):
            media_url = payload.get(f"MediaUrl{index}")
            content_type = payload.get(f"MediaContentType{index}")
            if not media_url:
                continue
            attachments.append(
                AttachmentPayload(
                    url=media_url,
                    content_type=content_type,
                    filename=f"attachment_{index}",
                    content=self._download_media_base64(media_url),
                )
            )
        return attachments

    def _download_media_base64(self, url: str) -> Optional[str]:
        if not (self.settings.twilio_account_sid and self.settings.twilio_auth_token):
            return None
        response = requests.get(url, auth=(self.settings.twilio_account_sid, self.settings.twilio_auth_token), timeout=30)
        if response.status_code >= 400:
            logger.warning("Failed to fetch media from Twilio: %s", response.status_code)
            return None
        return base64.b64encode(response.content).decode("utf-8")

    def _send_auto_reply(self, to_number: str, name: str) -> None:
        message = (
            f"Hi {name}, we've received your resume! Thank you for your interest in SmartHire Gateway. "
            "Our team is currently reviewing your application and will be in touch about the next steps."
        )
        from_number = self.settings.twilio_whatsapp_from or ""
        if not from_number:
            logger.debug("Twilio sender number not configured; skipping auto reply.")
            return
        if not from_number.startswith("whatsapp:"):
            from_number = f"whatsapp:{from_number}"
        try:
            self._client.messages.create(
                body=message,
                from_=from_number,
                to=to_number,
            )
        except Exception as exc:  # pragma: no cover - network path
            logger.error("Auto reply failed: %s", exc)
