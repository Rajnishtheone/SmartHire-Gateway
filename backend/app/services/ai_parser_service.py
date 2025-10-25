from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - optional dependency
    OpenAI = None  # type: ignore

from ..core.config import Settings, get_settings

logger = logging.getLogger("smarthire.ai_parser")

DEFAULT_MODEL = "gpt-4o-mini"


@dataclass
class AIParseResult:
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    skills: Optional[list[str]] = None
    education: Optional[str] = None
    experience: Optional[str] = None
    last_job_title: Optional[str] = None


class AIParsingService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._client = None
        if self.settings.openai_api_key and OpenAI is not None:
            try:
                self._client = OpenAI(api_key=self.settings.openai_api_key)
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Unable to initialise OpenAI client: %s", exc)
        if self._client is None:
            logger.debug("AI parsing disabled (missing client or API key).")

    def is_enabled(self) -> bool:
        return self._client is not None

    def enrich(self, text: str, draft: Dict[str, Any]) -> Optional[AIParseResult]:
        if not self.is_enabled():
            return None
        if not text.strip():
            return None
        trimmed = text[:8000]
        hint_json = json.dumps(draft, ensure_ascii=False)
        prompt = (
            "You are assisting with automation for a recruiting team. "
            "Given a resume's raw text, extract the candidate details as JSON with the following keys: "
            "full_name, email, phone, location, skills (array of distinct skills), education (string), "
            "experience (string summary), and last_job_title. "
            "Always respond with valid JSON only. Use the provided draft values when confident, otherwise refine them. "
            "If a field is unknown, use null."
        )
        messages = [
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": (
                    "Known draft values:\n"
                    f"{hint_json}\n\n"
                    "Resume text:\n"
                    f"{trimmed}"
                ),
            },
        ]
        try:
            response = self._client.chat.completions.create(
                model=getattr(self.settings, "openai_model", DEFAULT_MODEL) or DEFAULT_MODEL,
                messages=messages,
                temperature=0.0,
                max_tokens=600,
            )
            content = response.choices[0].message.content if response.choices else ""
            data = json.loads(content or "{}")
            return AIParseResult(
                full_name=self._extract_str(data, "full_name"),
                email=self._extract_str(data, "email"),
                phone=self._extract_str(data, "phone"),
                location=self._extract_str(data, "location"),
                skills=self._extract_list(data, "skills"),
                education=self._extract_str(data, "education"),
                experience=self._extract_str(data, "experience"),
                last_job_title=self._extract_str(data, "last_job_title"),
            )
        except Exception as exc:  # pragma: no cover - network dependent
            logger.warning("AI parsing failed: %s", exc)
            return None

    @staticmethod
    def _extract_str(data: Dict[str, Any], key: str) -> Optional[str]:
        value = data.get(key)
        if not value:
            return None
        if isinstance(value, str):
            cleaned = value.strip()
            return cleaned or None
        return None

    @staticmethod
    def _extract_list(data: Dict[str, Any], key: str) -> Optional[list[str]]:
        value = data.get(key)
        if isinstance(value, list):
            cleaned = [str(item).strip() for item in value if str(item).strip()]
            return cleaned or None
        if isinstance(value, str):
            cleaned = [item.strip() for item in value.split(",") if item.strip()]
            return cleaned or None
        return None
