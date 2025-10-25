from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ["DEBUG"] = "false"
os.environ["BACKEND_CORS_ORIGINS"] = "http://localhost:5173"
os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"] = ""
os.environ["GOOGLE_SHEETS_ID"] = ""
os.environ["GOOGLE_DRIVE_FOLDER_ID"] = ""
os.environ["TWILIO_ACCOUNT_SID"] = ""
os.environ["TWILIO_AUTH_TOKEN"] = ""
os.environ["TWILIO_WHATSAPP_FROM"] = ""
os.environ["ADMIN_EMAIL"] = "admin@example.com"
os.environ["ADMIN_PASSWORD"] = "admin123"

from backend.app.core.config import Settings
from backend.app.main import create_app


@pytest.fixture
def temp_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    data_dir = tmp_path / "data" / "dev"
    data_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.chdir(tmp_path)
    return data_dir


@pytest.fixture
def test_settings(temp_data_dir: Path) -> Settings:
    return Settings(
        debug=True,
        storage_mode="local",
        google_service_account_json=None,
        google_sheets_id=None,
        allowed_origins=[],
        jwt_secret="test-secret",
        admin_password="admin123",
    )


@pytest.fixture
def api_client(test_settings: Settings) -> TestClient:
    app = create_app(settings=test_settings)
    return TestClient(app)
