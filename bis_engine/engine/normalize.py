"""Input normalization: script detection + query text normalization.

Multilingual search works through the alias vocabulary regardless of the
detected script; detection exists to label results honestly in the UI.
"""

from __future__ import annotations

import re
import unicodedata

# Unicode block ranges for Indic scripts we label in the UI.
_SCRIPT_RANGES: tuple[tuple[tuple[int, int], str], ...] = (
    ((0x0900, 0x097F), "hi"),   # Devanagari (Hindi/Marathi)
    ((0x0980, 0x09FF), "bn"),   # Bengali
    ((0x0A00, 0x0A7F), "pa"),   # Gurmukhi
    ((0x0A80, 0x0AFF), "gu"),   # Gujarati
    ((0x0B00, 0x0B7F), "or"),   # Odia
    ((0x0B80, 0x0BFF), "ta"),   # Tamil
    ((0x0C00, 0x0C7F), "te"),   # Telugu
    ((0x0C80, 0x0CFF), "kn"),   # Kannada
    ((0x0D00, 0x0D7F), "ml"),   # Malayalam
)

_SCRIPT_NAMES = {
    "en": "English (Latin)",
    "hi": "Hindi (Devanagari)",
    "ta": "Tamil",
    "bn": "Bengali",
    "pa": "Punjabi",
    "gu": "Gujarati",
    "or": "Odia",
    "te": "Telugu",
    "kn": "Kannada",
    "ml": "Malayalam",
    "unknown": "Unknown",
}


def detect_script(text: str) -> str:
    """Return a coarse language key based on dominant unicode block."""
    counts: dict[str, int] = {}
    for ch in text or "":
        cp = ord(ch)
        for (lo, hi), lang in _SCRIPT_RANGES:
            if lo <= cp <= hi:
                counts[lang] = counts.get(lang, 0) + 1
                break
    if counts:
        return max(counts, key=counts.get)
    if re.search(r"[A-Za-z]", text or ""):
        return "en"
    return "unknown"


def script_name(key: str) -> str:
    return _SCRIPT_NAMES.get(key, key)


def normalize_text(text: str) -> str:
    """Lowercase, NFC-normalize, strip zero-width chars, unify separators.

    Keeps hyphens (relevant for codes like 'socket-outlets'); converts
    pipes/slashes/semicolons/commas to spaces so phrase aliases can span them.
    """
    text = unicodedata.normalize("NFC", str(text or ""))
    text = text.replace("\u200b", "").replace("\u00ad", "")
    text = text.replace("\r\n", "\n")
    text = re.sub(r"[|/;,]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()
