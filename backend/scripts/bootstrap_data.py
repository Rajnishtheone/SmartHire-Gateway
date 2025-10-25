from __future__ import annotations

from datetime import datetime, timezone

from ..app.core.config import get_settings
from ..app.models.response_models import CandidateRecord
from ..app.repositories.audit_repository import AuditRepository
from ..app.repositories.drive_repository import DriveRepository
from ..app.repositories.sheets_repository import SheetsRepository
from ..app.services.storage_service import StorageService


def main() -> None:
    settings = get_settings()
    storage = StorageService(
        sheets_repository=SheetsRepository(settings),
        drive_repository=DriveRepository(settings),
        audit_repository=AuditRepository(),
        settings=settings,
    )
    sample = CandidateRecord(
        full_name="Sample Candidate",
        email="candidate@example.com",
        phone="+91 99999 99999",
        location="Remote",
        skills=["Python", "FastAPI", "NLP"],
        education="B.Tech Computer Science",
        experience="5 years of experience in backend engineering",
        last_job_title="Senior Backend Engineer",
        source="bootstrap",
        received_at=datetime.now(timezone.utc),
        confidence=0.85,
    )
    storage.persist_candidate(sample, attachments=None)


if __name__ == "__main__":
    main()
