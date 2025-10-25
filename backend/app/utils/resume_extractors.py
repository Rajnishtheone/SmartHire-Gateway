from __future__ import annotations

from pathlib import Path

import pdfplumber
from docx import Document


def extract_text_from_pdf(path: Path) -> str:
    text_chunks: list[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            extracted = page.extract_text() or ""
            text_chunks.append(extracted)
    return "\n".join(text_chunks)


def extract_text_from_docx(path: Path) -> str:
    document = Document(path)
    return "\n".join(paragraph.text for paragraph in document.paragraphs)


def extract_text_from_plain(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")
