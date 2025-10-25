from __future__ import annotations

import base64
import tempfile
from pathlib import Path
from typing import Optional

import requests


class FileDownloadError(Exception):
    pass


def download_to_temp(url: str, filename_hint: str | None = None) -> Path:
    response = requests.get(url, timeout=30)
    if response.status_code >= 400:
        raise FileDownloadError(f"Failed to download file: {response.status_code}")

    suffix = Path(filename_hint or "").suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(response.content)
        temp_path = Path(tmp.name)
    return temp_path


def write_base64_to_temp(content: str, filename_hint: str | None = None) -> Path:
    decoded = base64.b64decode(content.encode("utf-8"))
    suffix = Path(filename_hint or "").suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(decoded)
        temp_path = Path(tmp.name)
    return temp_path


def ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def archive_local_copy(data: bytes, destination: Path) -> Path:
    ensure_directory(destination.parent)
    destination.write_bytes(data)
    return destination
