"""Hybrid retriever: deterministic alias matching + TF-IDF semantic scoring.

MVP design (deliberately dependency-light, no model download):
  1. char_wb n-gram TF-IDF over enriched documents (title + summary + aliases
     + category + sector name). Character n-grams tolerate inflection, missing
     spaces, transliteration drift and typo variants that word tokenizers choke on.
  2. Exact alias hits inject a strong additive bonus (cosine similarity alone
     cannot express "this exact phrase appeared").
  3. A compact secondary matrix over title+aliases boosts code-name matching.

This is the classic lexical stage of a hybrid retrieval stack; an embedding
re-ranker is the natural upgrade path (see README).
"""

from __future__ import annotations

import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from bis_engine.data.catalog import SECTORS, STANDARDS, get_by_code
from bis_engine.engine.normalize import normalize_text

_CODE_RE = re.compile(r"\bis\s*\d{2,5}(?:\s*\(?\s*part\s*\d+\s*\)?)?", re.IGNORECASE)


def _build_enriched_document(std: dict) -> str:
    sector_label = SECTORS.get(std.get("sector", ""), "")
    parts: list[str] = [std["code"], std["title"], std.get("summary", ""),
                        std.get("category", ""), sector_label]
    for lang_words in std.get("aliases", {}).values():
        parts.extend(lang_words)
    return normalize_text(" ".join(parts))


def _build_name_document(std: dict) -> str:
    parts: list[str] = [std["code"], std["title"], std.get("category", "")]
    for lang_words in std.get("aliases", {}).values():
        parts.extend(lang_words)
    return normalize_text(" ".join(parts))


class StandardsRetriever:
    """Retrieves and ranks Indian Standards for a natural-language query."""

    def __init__(self, standards: list[dict] | None = None):
        self.standards = standards if standards is not None else STANDARDS
        self._docs = [_build_enriched_document(s) for s in self.standards]
        self._name_docs = [_build_name_document(s) for s in self.standards]

        self._vectorizer = TfidfVectorizer(
            analyzer="char_wb", ngram_range=(3, 5), min_df=1, sublinear_tf=True,
        )
        self._matrix = self._vectorizer.fit_transform(self._docs)

        self._name_vectorizer = TfidfVectorizer(
            analyzer="char_wb", ngram_range=(3, 5), min_df=1, sublinear_tf=True,
        )
        self._name_matrix = self._name_vectorizer.fit_transform(self._name_docs)

        # Alias index: normalized alias -> [(catalogue index, original alias), ...]
        self._alias_index: dict[str, list[tuple[int, str]]] = {}
        for idx, std in enumerate(self.standards):
            for words in std.get("aliases", {}).values():
                for alias in words:
                    self._alias_index.setdefault(normalize_text(alias), []).append((idx, alias))

    # ------------------------------------------------------------------ public
    def search(self, query: str, top_k: int = 6) -> dict:
        candidates = self.search_all(query, top_k=top_k)
        primary, rest = (candidates[0], candidates[1:]) if candidates else (None, [])
        return {
            "query": query,
            "primary": primary,
            "alternatives": rest,
            "matched_aliases": sorted({a for c in candidates for a in c["matched_aliases"]}),
        }

    def search_all(self, query: str, top_k: int = 6) -> list[dict]:
        """Flat, score-ranked candidate list for a query."""
        norm = normalize_text(query)
        if not norm:
            return []
        sims = cosine_similarity(self._vectorizer.transform([norm]), self._matrix)[0]
        name_sims = cosine_similarity(self._name_vectorizer.transform([norm]), self._name_matrix)[0]

        matched_aliases: dict[int, list[str]] = {}
        for alias_key, hits in self._alias_index.items():
            # Plural tolerance: "air conditioner" also matches "air conditioners".
            if re.search(r"(?<!\w)" + re.escape(alias_key) + r"s?(?!\w)", norm):
                for idx, alias in hits:
                    matched_aliases.setdefault(idx, []).append(alias)

        scored: list[dict] = []
        for idx, std in enumerate(self.standards):
            aliases = matched_aliases.get(idx, [])
            alias_bonus = min(0.45, 0.25 * len(aliases))
            score = float(0.55 * sims[idx] + 0.20 * name_sims[idx] + alias_bonus)
            if score <= 0:
                continue
            scored.append({
                "standard": std,
                "score": round(min(score, 0.99), 4),
                "matched_aliases": aliases,
            })

        scored.sort(key=lambda s: s["score"], reverse=True)
        return scored[:top_k]

    def match_by_code(self, text: str) -> list[dict]:
        """Find IS-code-like tokens in free text (citation verification)."""
        norm = text.lower()
        found: dict[str, dict] = {}
        for m in _CODE_RE.finditer(norm):
            std = get_by_code(m.group(0))
            if std and std["code"].lower() not in found:
                found[std["code"].lower()] = std
        return list(found.values())

    def stats(self) -> dict:
        return {"catalogue_size": len(self.standards),
                "alias_count": sum(len(v) for v in self._alias_index.values())}
