from __future__ import annotations

import re
import unicodedata
from typing import Iterable, List, Optional

EMAIL_REGEX = re.compile(r"(?i)([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})")
PHONE_REGEX = re.compile(r"(\+?\d[\d\s\-().]{7,}\d)")


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

def strip_non_printable(text: str) -> str:
    return "".join(char if char.isprintable() else " " for char in text)

def replace_ligatures(text: str) -> str:
    ligatures = {
        "\ufb00": "ff",
        "\ufb01": "fi",
        "\ufb02": "fl",
        "\ufb03": "ffi",
        "\ufb04": "ffl",
        "\ufb05": "ft",
        "\ufb06": "st",
    }
    for key, value in ligatures.items():
        text = text.replace(key, value)
    return text

def sanitize_text(text: str) -> str:
    cleaned = replace_ligatures(strip_non_printable(text))
    normalized = unicodedata.normalize("NFKC", cleaned)
    return normalize_whitespace(normalized)


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

def has_meaningful_content(
    text: str,
    min_alpha: int = 40,
    min_ratio: float = 0.05,
    min_space_ratio: float = 0.015,
) -> bool:
    if not text:
        return False
    alpha_count = sum(char.isalpha() for char in text)
    if alpha_count < min_alpha:
        return False
    ratio = alpha_count / max(len(text), 1)
    if ratio < min_ratio:
        return False
    space_ratio = text.count(" ") / max(len(text), 1)
    if space_ratio < min_space_ratio:
        return False
    return True


PDF_NOISE_TOKENS = {
    "/type",
    "/font",
    "/length",
    "/filter",
    "/color",
    "/xobject",
    "/resources",
    "/procset",
    "/device",
    "/pattern",
    "/structparents",
    "/parent",
    "/bpc",
    "/structparents",
    "cid:",
}


def looks_like_pdf_metadata(text: str) -> bool:
    if not text:
        return True
    lowered = text.lower()
    if "cid:" in lowered:
        return True
    slash_count = lowered.count("/")
    if slash_count >= 8:
        return True
    noise_hits = sum(lowered.count(token) for token in PDF_NOISE_TOKENS)
    if noise_hits >= 3:
        return True
    non_word_ratio = sum(1 for ch in lowered if not ch.isalnum() and ch not in {" ", ",", ".", "-", "\n"}) / max(len(lowered), 1)
    return non_word_ratio > 0.2
