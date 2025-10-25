from __future__ import annotations

from pathlib import Path

import pdfplumber
from docx import Document

try:
    from pdfminer.high_level import extract_text as pdfminer_extract_text
except ImportError:  # pragma: no cover - optional dependency
    pdfminer_extract_text = None  # type: ignore


def extract_text_from_pdf(path: Path) -> str:
    text_chunks: list[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            extracted = page.extract_text() or ""
            text_chunks.append(extracted)
    return "\n".join(text_chunks)


def extract_text_from_pdfminer(path: Path) -> str:
    if pdfminer_extract_text is None:
        return ""
    try:
        return pdfminer_extract_text(path)
    except Exception:
        return ""


def extract_text_from_docx(path: Path) -> str:
    document = Document(path)
    return "\n".join(paragraph.text for paragraph in document.paragraphs)


def extract_text_from_plain(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")
