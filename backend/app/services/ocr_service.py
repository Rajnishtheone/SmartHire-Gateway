from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from pdf2image import convert_from_path
from PIL import Image
import pytesseract

from ..core.config import Settings, get_settings
from ..models.request_models import AttachmentPayload
from ..utils import file_utils, resume_extractors, text_cleaning

logger = logging.getLogger("smarthire.ocr")


@dataclass
class AttachmentResult:
    filename: str
    text: str
    confidence: float
    content_type: Optional[str] = None


class OCRService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def extract_from_attachments(self, attachments: List[AttachmentPayload]) -> List[AttachmentResult]:
        results: List[AttachmentResult] = []
        for attachment in attachments:
            if not (attachment.url or attachment.content):
                continue
            path = self._materialize_attachment(attachment)
            try:
                text = self._extract_text(path, attachment.content_type)
                sanitized_text = text_cleaning.sanitize_text(text)
                confidence = self._score_confidence(sanitized_text)
                results.append(
                    AttachmentResult(
                        filename=attachment.filename or path.name,
                        text=sanitized_text,
                        confidence=confidence,
                        content_type=attachment.content_type,
                    )
                )
            finally:
                try:
                    path.unlink(missing_ok=True)
                except Exception:  # pragma: no cover - cleanup best effort
                    logger.debug("Failed to remove temp file %s", path)
        return results

    def _materialize_attachment(self, attachment: AttachmentPayload) -> Path:
        if attachment.content:
            return file_utils.write_base64_to_temp(attachment.content, attachment.filename)
        if attachment.url:
            return file_utils.download_to_temp(attachment.url, attachment.filename)
        raise ValueError("Attachment payload missing both url and content")

    def _extract_text(self, path: Path, content_type: Optional[str]) -> str:
        suffix = path.suffix.lower()
        if suffix in {".txt", ".md", ".csv"}:
            return resume_extractors.extract_text_from_plain(path)
        if suffix in {".docx"}:
            return resume_extractors.extract_text_from_docx(path)
        if suffix in {".pdf"}:
            return self._extract_from_pdf(path)
        if suffix in {".png", ".jpg", ".jpeg", ".tiff", ".bmp"} or (content_type and "image" in content_type):
            return self._extract_from_image(path)
        # fallback: treat as docx or binary text
        try:
            return resume_extractors.extract_text_from_docx(path)
        except Exception:
            return resume_extractors.extract_text_from_plain(path)

    def _extract_from_pdf(self, path: Path) -> str:
        try:
            text = resume_extractors.extract_text_from_pdf(path)
            cleaned = text_cleaning.strip_non_printable(text)
            if text_cleaning.has_meaningful_content(cleaned) and not text_cleaning.looks_like_pdf_metadata(cleaned):
                return cleaned
            logger.info(
                "Structured PDF extract produced low quality output (len=%s); switching to OCR for %s",
                len(cleaned),
                path.name,
            )
        except Exception as exc:
            logger.warning("Structured PDF extraction failed: %s", exc)

        images = convert_from_path(path, dpi=300)
        text_chunks = [text_cleaning.strip_non_printable(pytesseract.image_to_string(image)) for image in images]
        return "\n".join(text_chunks)

    def _extract_from_image(self, path: Path) -> str:
        with Image.open(path) as image:
            return text_cleaning.strip_non_printable(pytesseract.image_to_string(image))

    @staticmethod
    def _score_confidence(text: str) -> float:
        length = len(text_cleaning.lines(text))
        return min(1.0, 0.2 + (length / 200.0))
