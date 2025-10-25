from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List

try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:  # pragma: no cover - optional dependency for dev mode
    gspread = None  # type: ignore
    Credentials = None  # type: ignore

from ..core.config import Settings, get_settings
from ..models.response_models import CandidateRecord

logger = logging.getLogger("smarthire.sheets")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]


class SheetsRepository:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        base_dir = Path(__file__).resolve().parents[3]
        self._worksheet = self._bootstrap_google_sheet()
        self._local_path = base_dir / "data" / "dev" / "candidates.json"
        if not self._worksheet:
            self._ensure_local_store()

    def _bootstrap_google_sheet(self):
        if not (self.settings.google_service_account_json and self.settings.google_sheets_id):
            logger.debug("Google Sheets credentials not configured; using local storage.")
            return None
        if gspread is None or Credentials is None:
            logger.warning("gspread not installed; falling back to local storage.")
            return None
        try:
            service_info = self._load_service_account_info(self.settings.google_service_account_json)
        except (ValueError, FileNotFoundError) as exc:
            logger.warning("Failed to load Google credentials (%s); falling back to local storage.", exc)
            return None
        credentials = Credentials.from_service_account_info(service_info, scopes=SCOPES)
        client = gspread.authorize(credentials)
        spreadsheet = client.open_by_key(self.settings.google_sheets_id)
        worksheet = spreadsheet.sheet1
        self._ensure_header_row(worksheet)
        return worksheet

    def _load_service_account_info(self, raw: str) -> dict:
        if not raw or not raw.strip():
            raise ValueError("Empty Google service account configuration")
        path = Path(raw)
        try:
            if path.exists():
                return json.loads(path.read_text())
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("Invalid Google service account JSON") from exc

    def _ensure_header_row(self, worksheet) -> None:
        header = worksheet.row_values(1)
        expected = [
            "Timestamp",
            "Full Name",
            "Email",
            "Phone",
            "Location",
            "Skills",
            "Education",
            "Experience",
            "Last Job Title",
            "Source",
            "Confidence",
        ]
        if header != expected:
            worksheet.update("A1:K1", [expected])

    def _ensure_local_store(self) -> None:
        self._local_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._local_path.exists():
            self._local_path.write_text(json.dumps([], indent=2))

    def append_candidate(self, record: CandidateRecord) -> None:
        row = [
            record.received_at.isoformat(),
            record.full_name or "",
            record.email or "",
            record.phone or "",
            record.location or "",
            ", ".join(record.skills),
            record.education or "",
            record.experience or "",
            record.last_job_title or "",
            record.source,
            record.confidence or 0,
        ]
        if self._worksheet:
            self._worksheet.append_row(row, value_input_option="USER_ENTERED")
            return
        data = json.loads(self._local_path.read_text())
        data.append(
            {
                "timestamp": record.received_at.isoformat(),
                "full_name": record.full_name,
                "email": record.email,
                "phone": record.phone,
                "location": record.location,
                "skills": record.skills,
                "education": record.education,
                "experience": record.experience,
                "last_job_title": record.last_job_title,
                "source": record.source,
                "confidence": record.confidence,
            }
        )
        self._local_path.write_text(json.dumps(data, indent=2))

    def list_recent(self, limit: int = 20) -> List[CandidateRecord]:
        if self._worksheet:
            records = self._worksheet.get_all_records()
            sliced = records[-limit:]
            return [self._from_sheet_row(row) for row in reversed(sliced)]
        data = json.loads(self._local_path.read_text())
        sliced = data[-limit:]
        return [self._from_local_row(row) for row in reversed(sliced)]

    def _from_sheet_row(self, row: dict) -> CandidateRecord:
        skills = [skill.strip() for skill in row.get("Skills", "").split(",") if skill.strip()]
        return CandidateRecord(
            full_name=row.get("Full Name") or None,
            email=row.get("Email") or None,
            phone=row.get("Phone") or None,
            location=row.get("Location") or None,
            skills=skills,
            education=row.get("Education") or None,
            experience=row.get("Experience") or None,
            last_job_title=row.get("Last Job Title") or None,
            source=row.get("Source") or "unknown",
            received_at=self._parse_timestamp(row.get("Timestamp")),
            confidence=float(row.get("Confidence") or 0),
        )

    def _from_local_row(self, row: dict) -> CandidateRecord:
        return CandidateRecord(
            full_name=row.get("full_name"),
            email=row.get("email"),
            phone=row.get("phone"),
            location=row.get("location"),
            skills=row.get("skills", []),
            education=row.get("education"),
            experience=row.get("experience"),
            last_job_title=row.get("last_job_title"),
            source=row.get("source", "unknown"),
            received_at=self._parse_timestamp(row.get("timestamp")),
            confidence=float(row.get("confidence") or 0),
        )

    @staticmethod
    def _parse_timestamp(value) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                pass
        return datetime.utcnow()
