"""Tender Analyzer: turns free-text specifications into a red/amber/green report.

Pipeline:
  1. Chunk the document into sentences/clauses.
  2. Retrieve candidate standards per clause; keep confident hits.
  3. Expand each confirmed primary standard into its allied (normative) cluster.
  4. Detect IS-code citations in the text and check them against the catalogue.
  5. Collect certification alerts for every relevant standard.
Report structure mirrors how an official reads a tender:
  primary standards found -> allied standards missing -> certifications
  required -> obsolete/unknown references flagged.
"""

from __future__ import annotations

import re
from collections import OrderedDict

from bis_engine.data.catalog import SYNC_HEALTH, get_by_code
from bis_engine.engine.normalize import detect_script, script_name
from bis_engine.engine.retriever import StandardsRetriever

# A clause needs at least this retrieval score to be treated as a real hit.
PRIMARY_THRESHOLD = 0.30
# Maximum primary standards reported per document (keeps reports actionable).
MAX_PRIMARY = 6

_CODE_RE = re.compile(r"\bis\s*\d{2,5}(?:\s*\(?\s*part\s*\d+\s*\)?)?", re.IGNORECASE)
_YEAR_RE = re.compile(r"(1[89]\d{2}|20[0-4]\d)")


def _split_clauses(text: str) -> list[str]:
    """Split into sentence-ish clauses, dropping short fragments."""
    parts = re.split(r"(?<=[.;])\s+|\n+", text)
    return [p.strip() for p in parts if len(p.strip()) >= 8]


def _unknown_standard(code: str) -> dict:
    """Stub entry for cited codes missing from the seed catalogue."""
    return {
        "code": re.sub(r"\s+", " ", code.upper()),
        "title": "Not in MVP catalogue — verify manually",
        "version": "unknown",
        "amendments": [],
        "status": "unknown",
        "aliases": {}, "allied": [], "certifications": [],
        "examples": [], "last_reviewed": None, "sector": None,
        "category": None, "summary": None,
    }


class TenderAnalyzer:
    def __init__(self, retriever: StandardsRetriever | None = None):
        self.retriever = retriever or StandardsRetriever()

    # ------------------------------------------------------------------ public
    def analyze(self, text: str, top_k: int = 6) -> dict:
        text = str(text or "").strip()
        if len(text) < 10:
            raise ValueError("Provide a product description or specification (min 10 characters).")
        if len(text) > 20000:
            raise ValueError("Document too long for the MVP analyzer (max 20,000 characters).")

        lang_key = detect_script(text)

        # 1. Per-clause retrieval for topical standards.
        hits: "OrderedDict[str, dict]" = OrderedDict()
        for clause in _split_clauses(text) or [text]:
            for cand in self._collect_hits(clause, top_k):
                code = cand["standard"]["code"]
                if code not in hits:
                    hits[code] = cand

        # 2. Direct code citations (including codes unknown to the catalogue).
        cited = self._detect_codes(text)

        # 3. Certification alerts from confirmed standards + citations.
        cert_map: "OrderedDict[str, dict]" = OrderedDict()
        for cand in list(hits.values()) + [{"standard": s} for s in cited]:
            for cert in cand["standard"].get("certifications", []):
                cert_map.setdefault(cert["scheme"], cert)

        primaries = [self._serialize(c) for c in list(hits.values())[:MAX_PRIMARY]]
        allied_missing = self._allied_missing(
            text, [{"standard": p} for p in primaries] + [{"standard": s} for s in cited])
        obsolete = self._obsolete_codes(cited)

        checks = [
            {"check": "primary_standards", "status": "pass" if primaries else "fail",
             "detail": f"{len(primaries)} relevant standard(s) identified"
                       if primaries else "No relevant Indian Standards identified from this text"},
            {"check": "allied_standards", "status": "warn" if allied_missing else "pass",
             "detail": f"{len(allied_missing)} allied/normative standard(s) not found in the text"
                       if allied_missing else "No missing allied standards detected"},
            {"check": "certifications", "status": "warn" if cert_map else "pass",
             "detail": f"{len(cert_map)} mandatory certification scheme(s) apply"
                       if cert_map else "No mandatory certification scheme matched"},
            {"check": "obsolete_references", "status": "fail" if obsolete else "pass",
             "detail": f"{len(obsolete)} outdated/unknown code reference(s) flagged"
                       if obsolete else "No outdated code references detected"},
        ]

        return {
            "meta": {
                "engine": "bis-recommendation-engine MVP",
                "disclaimer": ("Demo seed catalogue — verify every recommendation against the "
                               "official BIS catalogue before citing in a tender."),
                "detected_language": lang_key,
                "detected_language_label": script_name(lang_key),
                "sync": SYNC_HEALTH,
            },
            "primaries": primaries,
            "allied_missing": allied_missing,
            "certifications": list(cert_map.values()),
            "obsolete_flags": obsolete,
            "checks": checks,
        }

    # ----------------------------------------------------------------- helpers
    def _collect_hits(self, clause: str, top_k: int) -> list[dict]:
        out: list[dict] = []
        seen: set[str] = set()
        for res in self.retriever.search_all(clause, top_k=top_k):
            code = res["standard"]["code"]
            if code in seen or res["score"] < PRIMARY_THRESHOLD:
                continue
            seen.add(code)
            out.append(res)
        return out

    def _detect_codes(self, text: str) -> list[dict]:
        codes = set(m.group(0) for m in _CODE_RE.finditer(text.lower()))
        out: list[dict] = []
        for code in codes:
            std = get_by_code(code)
            out.append(std if std else _unknown_standard(code))
        return out

    def _allied_missing(self, text: str, confirmed: list[dict]) -> list[dict]:
        text_norm = " " + " ".join((text or "").lower().split()) + " "
        seen: set[str] = set()
        out: list[dict] = []
        for cand in confirmed:
            std = cand["standard"]
            if std.get("status") == "unknown":
                continue
            for allied in std.get("allied", []):
                code = allied["code"]
                if code in seen:
                    continue
                seen.add(code)
                if not self._code_mentioned(text_norm, code):
                    ref = get_by_code(code)
                    out.append({
                        "required_by": std["code"],
                        "code": code,
                        "title": ref["title"] if ref else allied.get("relation", ""),
                        "relation": allied.get("relation", "related standard"),
                    })
        return out

    @staticmethod
    def _code_mentioned(text_norm: str, code: str) -> bool:
        m = re.match(r"^(is|iec)\s*(.+)$", code.lower())
        if not m:
            return code.lower() in text_norm
        prefix, body = m.group(1), m.group(2)
        if "(part" in body:
            base, part = body.split("(part", 1)
            part_num = re.sub(r"\D", "", part)
            pat = rf"{prefix}\s*{base.strip()}\s*\(\s*part\s*{part_num}\s*\)"
            return bool(re.search(pat, text_norm))
        pat = rf"{prefix}\s*{body.strip()}\b"
        return bool(re.search(pat, text_norm))

    @staticmethod
    def _obsolete_codes(cited: list[dict]) -> list[dict]:
        """Flag unknown codes and citations of outdated editions (via known pitfalls)."""
        flags: list[dict] = []
        for std in cited:
            if std.get("status") == "unknown":
                flags.append({"code": std["code"],
                              "reason": "Code not found in MVP catalogue — verify current status manually"})
                continue
            current_years = {int(y) for y in _YEAR_RE.findall(std.get("version", "") or "")}
            for ex in std.get("examples", []):
                for y in _YEAR_RE.findall(ex.get("bad", "")):
                    if current_years and int(y) not in current_years:
                        flags.append({"code": std["code"],
                                      "reason": ex.get("note", "Outdated edition cited"),
                                      "bad": ex.get("bad", ""),
                                      "good": ex.get("good", "")})
                        break
        return flags

    # ----------------------------------------------------------------- output
    def _serialize(self, cand: dict) -> dict:
        std = cand["standard"]
        return {
            "code": std["code"],
            "title": std["title"],
            "version": std["version"],
            "amendments": std["amendments"],
            "status": std["status"],
            "sector": std.get("sector"),
            "category": std.get("category"),
            "summary": std.get("summary"),
            "confidence": cand["score"],
            "matched_aliases": cand.get("matched_aliases", []),
            "allied": std.get("allied", []),
            "certifications": std.get("certifications", []),
            "examples": std.get("examples", []),
        }
