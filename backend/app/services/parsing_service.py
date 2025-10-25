from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Optional

import spacy
from spacy.language import Language

from ..core.config import Settings, get_settings
from ..core.security import UserRole
from ..models.request_models import AttachmentPayload
from ..models.response_models import CandidateRecord
from ..utils import text_cleaning
from .ocr_service import AttachmentResult, OCRService

logger = logging.getLogger("smarthire.parsing")


class ParsingService:
    def __init__(
        self,
        settings: Settings | None = None,
        ocr_service: OCRService | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.ocr_service = ocr_service or OCRService(settings=self.settings)
        self._nlp = self._load_nlp_model()
        self.skill_library = [
            "python",
            "django",
            "flask",
            "fastapi",
            "aws",
            "azure",
            "docker",
            "kubernetes",
            "sql",
            "pandas",
            "tensorflow",
            "pytorch",
            "javascript",
            "react",
            "node",
        ]

    def parse_payload(
        self,
        body: str,
        attachments: Optional[List[AttachmentPayload]] = None,
        source: str = "whatsapp",
    ) -> CandidateRecord:
        body_text = body or ""
        attachment_results: List[AttachmentResult] = []
        if attachments:
            attachment_results = self.ocr_service.extract_from_attachments(attachments)

        combined_text = self._combine_text(body_text, attachment_results)
        doc = self._nlp(combined_text)

        email = text_cleaning.extract_email(combined_text)
        phone = text_cleaning.extract_phone(combined_text)

        persons = [ent.text.strip() for ent in doc.ents if ent.label_ == "PERSON"]
        locations = [ent.text.strip() for ent in doc.ents if ent.label_ in {"GPE", "LOC"}]
        organizations = [ent.text.strip() for ent in doc.ents if ent.label_ == "ORG"]

        skills = text_cleaning.find_keywords(combined_text, self.skill_library)
        experience_note = self._extract_experience(combined_text)

        confidence = self._score_confidence(body_text, attachment_results)

        return CandidateRecord(
            full_name=persons[0] if persons else None,
            email=email,
            phone=phone,
            location=locations[0] if locations else None,
            skills=skills,
            education=self._extract_education(combined_text),
            experience=experience_note,
            last_job_title=organizations[0] if organizations else None,
            source=source,
            received_at=datetime.now(timezone.utc),
            confidence=confidence,
            notes=f"attachments: {[res.filename for res in attachment_results]}",
        )

    def _combine_text(self, body_text: str, attachments: List[AttachmentResult]) -> str:
        segments = [body_text]
        segments.extend(result.text for result in attachments if result.text)
        return "\n".join(segment for segment in segments if segment).strip()

    @staticmethod
    def _extract_education(text: str) -> Optional[str]:
        keywords = ["Bachelor", "Master", "B.Tech", "BSc", "MSc", "MBA", "PhD"]
        lines = text_cleaning.lines(text)
        for line in lines:
            if any(keyword.lower() in line.lower() for keyword in keywords):
                return line
        return None

    @staticmethod
    def _extract_experience(text: str) -> Optional[str]:
        patterns = ["years of experience", "yr experience", "experience of"]
        lines = text_cleaning.lines(text)
        for line in lines:
            if any(pattern in line.lower() for pattern in patterns):
                return line
        return None

    @staticmethod
    def _score_confidence(body_text: str, attachments: List[AttachmentResult]) -> float:
        base = 0.3 if body_text else 0.1
        attachment_boost = sum(result.confidence for result in attachments) / max(len(attachments), 1) if attachments else 0
        return min(1.0, base + attachment_boost)

    @staticmethod
    def _load_nlp_model() -> Language:
        try:
            return spacy.load("en_core_web_lg")
        except OSError:
            logger.warning("Large spaCy model not available; falling back to en_core_web_sm.")
            return spacy.load("en_core_web_sm")
