from __future__ import annotations

import logging
from typing import Iterable, List, Optional, Tuple

from ..models.request_models import AttachmentPayload
from ..models.response_models import CandidateRecord
from ..utils import file_utils
from .parsing_service import ParsingService
from .storage_service import StorageService

logger = logging.getLogger("smarthire.ingestion")


class IngestionService:
    def __init__(self, parsing_service: ParsingService, storage_service: StorageService) -> None:
        self.parsing_service = parsing_service
        self.storage_service = storage_service

    def ingest_payload(
        self,
        source: str,
        body: str,
        attachments: Optional[List[AttachmentPayload]] = None,
    ) -> CandidateRecord:
        record = self.parsing_service.parse_payload(body=body, attachments=attachments, source=source)
        attachment_data = list(self._materialize_attachments(attachments or []))
        return self.storage_service.persist_candidate(record, attachments=attachment_data)

    def _materialize_attachments(
        self, attachments: Iterable[AttachmentPayload]
    ) -> Iterable[Tuple[str, bytes, str]]:
        for attachment in attachments:
            if attachment.content:
                path = file_utils.write_base64_to_temp(attachment.content, attachment.filename)
            elif attachment.url:
                path = file_utils.download_to_temp(attachment.url, attachment.filename)
            else:
                continue
            try:
                data = path.read_bytes()
                yield (
                    attachment.filename or path.name,
                    data,
                    attachment.content_type or "application/octet-stream",
                )
            finally:
                try:
                    path.unlink(missing_ok=True)
                except Exception:  # pragma: no cover - best effort cleanup
                    logger.debug("Attachment temp cleanup failed for %s", path)
