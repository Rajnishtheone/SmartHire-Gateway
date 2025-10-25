from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:  # pragma: no cover - optional dependency for dev mode
    gspread = None  # type: ignore
    Credentials = None  # type: ignore

from ..core.config import Settings, get_settings
from ..models.response_models import CandidateRecord, CandidateStatus

logger = logging.getLogger("smarthire.sheets")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

SHEET_HEADER = [
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
    "Candidate ID",
    "Status",
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

        try:
            credentials = Credentials.from_service_account_info(service_info, scopes=SCOPES)
            client = gspread.authorize(credentials)
            spreadsheet = client.open_by_key(self.settings.google_sheets_id)
            worksheet = spreadsheet.sheet1
            self._ensure_header_row(worksheet)
            return worksheet
        except Exception as exc:  # pragma: no cover - runtime protection
            logger.warning("Unable to connect to Google Sheet (%s); using local storage.", exc)
            return None

    def _load_service_account_info(self, raw: str) -> dict:
        if not raw or not raw.strip():
            raise ValueError("Empty Google service account configuration")

        cleaned = raw.strip().strip('"').strip("'")

        if cleaned.startswith("{") or cleaned.startswith("["):
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                logger.debug("Service account string is not valid JSON; attempting to resolve as a path.")

        candidates: list[Path] = []
        raw_path = Path(cleaned)
        if raw_path.is_absolute():
            candidates.append(raw_path)
        else:
            candidates.append(raw_path)
            base_dir = Path(__file__).resolve().parents[3]
            candidates.append(Path.cwd() / raw_path)
            candidates.append(base_dir / raw_path)
            candidates.append(base_dir / raw_path.name)

        seen: set[Path] = set()
        for candidate in candidates:
            try:
                resolved = candidate.resolve(strict=False)
            except FileNotFoundError:
                resolved = candidate
            if resolved in seen:
                continue
            seen.add(resolved)
            if resolved.exists():
                try:
                    return json.loads(resolved.read_text())
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSON in {resolved}") from exc

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ValueError("Invalid Google service account JSON or path") from exc

    def _ensure_header_row(self, worksheet) -> None:
        header = worksheet.row_values(1)
        if header != SHEET_HEADER:
            worksheet.update("A1:M1", [SHEET_HEADER])

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
            record.candidate_id,
            record.status.value,
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
                "candidate_id": record.candidate_id,
                "status": record.status.value,
            }
        )
        self._local_path.write_text(json.dumps(data, indent=2))

    def list_recent(self, limit: int = 20) -> List[CandidateRecord]:
        return self.list_candidates(limit=limit)

    def list_candidates(
        self,
        status: CandidateStatus | None = None,
        limit: int | None = None,
    ) -> List[CandidateRecord]:
        records = self._list_from_sheet() if self._worksheet else self._list_from_local()
        if status:
            records = [record for record in records if record.status == status]
        if limit is not None:
            records = records[:limit]
        return records

    def get_candidate(self, candidate_id: str) -> Optional[CandidateRecord]:
        for record in self.list_candidates():
            if record.candidate_id == candidate_id:
                return record
        return None

    def update_status(self, candidate_id: str, status: CandidateStatus) -> CandidateRecord:
        record = self.get_candidate(candidate_id)
        if record is None:
            raise KeyError(candidate_id)
        if self._worksheet and record.sheet_row:
            header_index = self._header_index()
            status_col = header_index.get("Status")
            if status_col is not None:
                self._worksheet.update_cell(record.sheet_row, status_col + 1, status.value)
        else:
            data = json.loads(self._local_path.read_text())
            for item in data:
                if item.get("candidate_id") == candidate_id:
                    item["status"] = status.value
                    break
            self._local_path.write_text(json.dumps(data, indent=2))
        record.status = status
        return record

    def delete_candidate(self, candidate_id: str) -> CandidateRecord:
        record = self.get_candidate(candidate_id)
        if record is None:
            raise KeyError(candidate_id)
        if self._worksheet and record.sheet_row:
            self._worksheet.delete_rows(record.sheet_row)
        else:
            data = json.loads(self._local_path.read_text())
            data = [item for item in data if item.get("candidate_id") != candidate_id]
            self._local_path.write_text(json.dumps(data, indent=2))
        return record

    def delete_by_status(self, status: CandidateStatus) -> int:
        records = self.list_candidates()
        targets = [record for record in records if record.status == status]
        if not targets:
            return 0
        if self._worksheet:
            for record in sorted((rec for rec in targets if rec.sheet_row), key=lambda r: r.sheet_row or 0, reverse=True):
                self._worksheet.delete_rows(record.sheet_row)
        else:
            data = json.loads(self._local_path.read_text())
            data = [item for item in data if item.get("status") != status.value]
            self._local_path.write_text(json.dumps(data, indent=2))
        return len(targets)

    def _list_from_sheet(self) -> List[CandidateRecord]:
        values = self._worksheet.get_all_values()
        if not values:
            return []
        header = values[0]
        header_index = {name: idx for idx, name in enumerate(header)}
        records: List[CandidateRecord] = []
        updates: List[Tuple[int, str, str]] = []
        for row_number, row_values in enumerate(values[1:], start=2):
            row_dict = self._row_dict_from_values(row_values, header)
            record = self._from_sheet_row(row_dict, row_number)
            if record is None:
                continue
            if not row_dict.get("Candidate ID") or not row_dict.get("Status"):
                updates.append((row_number, record.candidate_id, record.status.value))
            records.append(record)
        if updates:
            self._fill_missing_metadata(updates, header_index)
        records.sort(key=lambda item: item.received_at, reverse=True)
        return records

    def _list_from_local(self) -> List[CandidateRecord]:
        data = json.loads(self._local_path.read_text())
        updated = False
        records: List[CandidateRecord] = []
        for entry in data:
            record, changed = self._from_local_row(entry)
            updated = updated or changed
            records.append(record)
        if updated:
            self._local_path.write_text(json.dumps(data, indent=2))
        records.sort(key=lambda item: item.received_at, reverse=True)
        return records

    def _row_dict_from_values(self, row: List[str], header: List[str]) -> Dict[str, str]:
        normalized_row = row + [""] * (len(header) - len(row))
        return {header[idx]: normalized_row[idx] for idx in range(len(header))}

    def _fill_missing_metadata(
        self,
        updates: List[Tuple[int, str, str]],
        header_index: Dict[str, int],
    ) -> None:
        if not self._worksheet:
            return
        for row_index, candidate_id, status_value in updates:
            if candidate_id and "Candidate ID" in header_index:
                self._worksheet.update_cell(row_index, header_index["Candidate ID"] + 1, candidate_id)
            if status_value and "Status" in header_index:
                self._worksheet.update_cell(row_index, header_index["Status"] + 1, status_value)

    def _from_sheet_row(self, row: Dict[str, str], row_index: int) -> Optional[CandidateRecord]:
        timestamp = self._parse_timestamp(row.get("Timestamp"))
        candidate_id = row.get("Candidate ID") or uuid4().hex
        status_value = row.get("Status") or CandidateStatus.NEW.value
        try:
            status = CandidateStatus(status_value)
        except ValueError:
            status = CandidateStatus.NEW
        skills = [skill.strip() for skill in row.get("Skills", "").split(",") if skill.strip()]
        confidence_raw = row.get("Confidence") or ""
        try:
            confidence = float(confidence_raw) if confidence_raw != "" else None
        except ValueError:
            confidence = None
        return CandidateRecord(
            candidate_id=candidate_id,
            full_name=row.get("Full Name") or None,
            email=row.get("Email") or None,
            phone=row.get("Phone") or None,
            location=row.get("Location") or None,
            skills=skills,
            education=row.get("Education") or None,
            experience=row.get("Experience") or None,
            last_job_title=row.get("Last Job Title") or None,
            source=row.get("Source") or "unknown",
            received_at=timestamp,
            confidence=confidence,
            status=status,
            sheet_row=row_index,
        )

    def _from_local_row(self, row: dict) -> Tuple[CandidateRecord, bool]:
        updated = False
        candidate_id = row.get("candidate_id")
        if not candidate_id:
            candidate_id = uuid4().hex
            row["candidate_id"] = candidate_id
            updated = True
        status_value = row.get("status") or CandidateStatus.NEW.value
        try:
            status = CandidateStatus(status_value)
        except ValueError:
            status = CandidateStatus.NEW
            row["status"] = status.value
            updated = True
        record = CandidateRecord(
            candidate_id=candidate_id,
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
            confidence=float(row.get("confidence") or 0) if row.get("confidence") not in {None, ""} else None,
            status=status,
        )
        return record, updated

    def _header_index(self) -> Dict[str, int]:
        if not self._worksheet:
            return {name: idx for idx, name in enumerate(SHEET_HEADER)}
        header = self._worksheet.row_values(1)
        return {name: idx for idx, name in enumerate(header)}

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
