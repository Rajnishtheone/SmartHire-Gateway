from __future__ import annotations

import json
import logging
from pathlib import Path

try:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload
    from google.oauth2.service_account import Credentials
except ImportError:  # pragma: no cover - optional dependency
    build = None  # type: ignore
    MediaIoBaseUpload = None  # type: ignore
    Credentials = None  # type: ignore

from ..core.config import Settings, get_settings

logger = logging.getLogger("smarthire.drive")


class DriveRepository:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._service = self._build_drive_service()
        self._local_dir = Path("data/dev/uploads")
        if not self._service:
            self._local_dir.mkdir(parents=True, exist_ok=True)

    def _build_drive_service(self):
        if not (self.settings.google_service_account_json and self.settings.google_drive_folder_id):
            return None
        if build is None or Credentials is None:
            logger.warning("googleapiclient not installed; using local archive.")
            return None

        info = self._load_service_account_info(self.settings.google_service_account_json)
        credentials = Credentials.from_service_account_info(
            info,
            scopes=["https://www.googleapis.com/auth/drive.file"],
        )
        return build("drive", "v3", credentials=credentials)

    def _load_service_account_info(self, raw: str) -> dict:
        path = Path(raw)
        if path.exists():
            return json.loads(path.read_text())
        return json.loads(raw)

    def archive_bytes(self, filename: str, data: bytes, mime_type: str = "application/octet-stream") -> str:
        if self._service:
            from io import BytesIO

            media = MediaIoBaseUpload(BytesIO(data), mimetype=mime_type)
            file_metadata = {"name": filename, "parents": [self.settings.google_drive_folder_id]}
            file = (
                self._service.files()
                .create(body=file_metadata, media_body=media, fields="id,webViewLink")
                .execute()
            )
            return file.get("webViewLink") or file.get("id")

        destination = self._local_dir / filename
        destination.write_bytes(data)
        return str(destination)
