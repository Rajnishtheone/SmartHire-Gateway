from __future__ import annotations

import json
from pathlib import Path
from typing import Dict


class UserRepository:
    """
    Minimal JSON-backed repository for demo user accounts.

    In a production system this would be replaced by a persistent database
    or identity provider integration.
    """

    def __init__(self, storage_path: Path | None = None) -> None:
        base_dir = Path(__file__).resolve().parents[3]
        self.storage_path = storage_path or base_dir / "data" / "dev" / "users.json"
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.storage_path.exists():
            legacy_path = base_dir / "backend" / "data" / "dev" / "users.json"
            if legacy_path.exists():
                self.storage_path.write_text(legacy_path.read_text())
            else:
                self.storage_path.write_text(json.dumps({}, indent=2))

    def load(self) -> Dict[str, dict]:
        raw = json.loads(self.storage_path.read_text())
        return {email.lower(): data for email, data in raw.items()}

    def save(self, users: Dict[str, dict]) -> None:
        self.storage_path.write_text(json.dumps(users, indent=2))

