from __future__ import annotations

import re
from typing import Iterable, List, Optional

EMAIL_REGEX = re.compile(r"(?i)([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})")
PHONE_REGEX = re.compile(r"(\+?\d[\d\s\-().]{7,}\d)")


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

def strip_non_printable(text: str) -> str:
    return "".join(char if char.isprintable() else " " for char in text)

def sanitize_text(text: str) -> str:
    return normalize_whitespace(strip_non_printable(text))

def extract_email(text: str) -> Optional[str]:
    match = EMAIL_REGEX.search(text)
    return match.group(1) if match else None


def extract_phone(text: str) -> Optional[str]:
    match = PHONE_REGEX.search(text)
    return normalize_whitespace(match.group(1)) if match else None


def lines(text: str) -> List[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def find_keywords(text: str, keywords: Iterable[str]) -> List[str]:
    text_lower = text.lower()
    return sorted({keyword for keyword in keywords if keyword.lower() in text_lower})

def has_meaningful_content(text: str, min_alpha: int = 40, min_ratio: float = 0.05) -> bool:
    if not text:
        return False
    alpha_count = sum(char.isalpha() for char in text)
    return alpha_count >= min_alpha and (alpha_count / max(len(text), 1)) >= min_ratio
