from __future__ import annotations

import logging
from typing import Iterable, List, Optional, Tuple

from ..core.config import Settings, get_settings
from ..models.response_models import CandidateRecord
from ..repositories.audit_repository import AuditRepository
from ..repositories.drive_repository import DriveRepository
from ..repositories.sheets_repository import SheetsRepository

logger = logging.getLogger("smarthire.storage")


class StorageService:
    def __init__(
        self,
        sheets_repository: SheetsRepository,
        drive_repository: DriveRepository,
        audit_repository: AuditRepository,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.sheets_repository = sheets_repository
        self.drive_repository = drive_repository
        self.audit_repository = audit_repository

    def persist_candidate(
        self,
        record: CandidateRecord,
        attachments: Optional[Iterable[Tuple[str, bytes, str]]] = None,
    ) -> CandidateRecord:
        self.sheets_repository.append_candidate(record)
        stored_locations: List[str] = []
        for attachment in attachments or []:
            filename, data, mime_type = attachment
            try:
                location = self.drive_repository.archive_bytes(filename, data, mime_type)
                stored_locations.append(location)
            except Exception as exc:  # pragma: no cover - safety net
                logger.error("Attachment archive failed for %s: %s", filename, exc)
        self.audit_repository.record(
            action="candidate_ingested",
            metadata={
                "email": record.email or "",
                "source": record.source,
                "attachments": ", ".join(stored_locations),
            },
        )
        return record

    def list_recent_candidates(self, limit: int = 20) -> List[CandidateRecord]:
        return self.sheets_repository.list_recent(limit)
