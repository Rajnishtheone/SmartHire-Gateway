from __future__ import annotations

import logging
from typing import Iterable, List, Optional, Tuple

from ..core.config import Settings, get_settings
from ..models.response_models import CandidateBoardResponse, CandidateRecord, CandidateStatus
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
        record.status = CandidateStatus.NEW
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
        return self.sheets_repository.list_candidates(limit=limit)

    def list_candidates(
        self,
        status: CandidateStatus | None = None,
        limit: int | None = None,
    ) -> List[CandidateRecord]:
        return self.sheets_repository.list_candidates(status=status, limit=limit)

    def get_candidate_board(self) -> CandidateBoardResponse:
        records = self.sheets_repository.list_candidates()
        board = CandidateBoardResponse()
        for record in records:
            if record.status == CandidateStatus.NEW:
                board.new.append(record)
            elif record.status == CandidateStatus.APPROVED:
                board.approved.append(record)
            elif record.status == CandidateStatus.INTERVIEW:
                board.interview.append(record)
            elif record.status == CandidateStatus.SELECTED:
                board.selected.append(record)
            elif record.status == CandidateStatus.REJECTED:
                board.rejected.append(record)
        return board

    def update_candidate_status(self, candidate_id: str, status: CandidateStatus) -> CandidateRecord:
        record = self.sheets_repository.update_status(candidate_id, status)
        self.audit_repository.record(
            action="candidate_status_updated",
            metadata={"candidate_id": candidate_id, "status": status.value},
        )
        return record

    def delete_candidate(self, candidate_id: str) -> CandidateRecord:
        record = self.sheets_repository.delete_candidate(candidate_id)
        self.audit_repository.record(
            action="candidate_deleted",
            metadata={"candidate_id": candidate_id, "email": record.email or ""},
        )
        return record

    def delete_candidates_by_status(self, status: CandidateStatus) -> int:
        removed = self.sheets_repository.delete_by_status(status)
        if removed:
            self.audit_repository.record(
                action="candidate_bulk_delete",
                metadata={"status": status.value, "count": removed},
            )
        return removed
