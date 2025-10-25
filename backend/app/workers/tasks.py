from __future__ import annotations

from typing import List, Optional

from ..models.request_models import AttachmentPayload
from ..services.ingestion_service import IngestionService


def ingest_async(
    ingestion_service: IngestionService,
    source: str,
    body: str,
    attachments: Optional[List[AttachmentPayload]] = None,
) -> None:
    """
    Placeholder worker task.

    In production bind this function to a Celery or RQ worker to process heavy
    OCR workloads outside the request cycle.
    """

    ingestion_service.ingest_payload(source=source, body=body, attachments=attachments)
