from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import List


@dataclass
class AuditEvent:
    timestamp: dt.datetime
    action: str
    metadata: dict[str, str]


class AuditRepository:
    """In-memory audit tracking; adequate for demo instrumentation."""

    def __init__(self) -> None:
        self._events: List[AuditEvent] = []

    def record(self, action: str, metadata: dict[str, str]) -> None:
        self._events.append(AuditEvent(timestamp=dt.datetime.utcnow(), action=action, metadata=metadata))

    def recent(self, limit: int = 20) -> List[AuditEvent]:
        return list(reversed(self._events[-limit:]))
