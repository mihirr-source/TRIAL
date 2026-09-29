"""Embedding (hybrid retrieval) tests — deterministic, no network.

A fake backend with a stable rotation vector simulates a semantic encoder:
rows whose document vectors are orthogonal to the fake query get ~0 semantic
similarity, a chosen row gets ~1.0. The lexical stage in these tests is flat,
so any score differences are attributable to the semantic stage alone.
"""

from __future__ import annotations

import numpy as np
import pytest

from bis_engine.data import catalog
from bis_engine.engine import embeddings
from bis_engine.engine.retriever import StandardsRetriever


class FakeBackend:
    """Deterministic encoder: d documents along axis 0, the query along axis 1.

    Query 'force:steel' points at the steel document (index 0); every other
    document is orthogonal to it and receives ~0 semantic similarity.
    """

    name = "hybrid"

    def encode(self, texts: list[str]) -> list[list[float]]:
        out = []
        for t in texts:
            if "force:steel" in t:
                out.append([0.0, 1.0])
            else:
                out.append([1.0, 0.0])
        return out


@pytest.fixture()
def fake_backend():
    embeddings.set_backend(FakeBackend())
    yield
    embeddings.reset_backend()


def _flat_lexical_retriever() -> StandardsRetriever:
    """Two dummy standards whose enriched docs are textually near-identical,
    so lexical scores alone cannot separate them."""
    dummies = [
        {
            "code": "IS 9001", "title": "Generic widget", "version": "2020",
            "amendments": [], "status": "active", "sector": "construction",
            "category": "Widgets", "summary": "generic widget for works",
            "aliases": {"en": ["widget"]}, "allied": [], "certifications": [],
            "examples": [], "last_reviewed": "2026-09-29",
        },
        {
            "code": "IS 9002", "title": "Generic widget junior", "version": "2021",
            "amendments": [], "status": "active", "sector": "steel",
            "category": "Widgets", "summary": "generic widget for works",
            "aliases": {"en": ["widget"]}, "allied": [], "certifications": [],
            "examples": [], "last_reviewed": "2026-09-29",
        },
    ]
    return StandardsRetriever(standards=dummies)


def test_retrieval_mode_lexical_without_backend():
    embeddings.reset_backend()
    assert embeddings.retrieval_mode() == "lexical"


def test_retrieval_mode_hybrid_with_backend(fake_backend):
    assert embeddings.retrieval_mode() == "hybrid"


def test_hybrid_scores_resort_results(fake_backend):
    """With a flat lexical field, the semantic stage must pull IS 9002 to the top."""
    r = _flat_lexical_retriever()
    ranked = r.search_all("widget force:steel", top_k=2)
    assert ranked[0]["standard"]["code"] == "IS 9002"


def test_lexical_mode_is_unaffected_by_backend_state():
    """No backend injected -> identical ranking to the classic engine."""
    embeddings.reset_backend()
    r = _flat_lexical_retriever()
    ranked = r.search_all("widget", top_k=2)
    assert {c["standard"]["code"] for c in ranked} == {"IS 9001", "IS 9002"}
    scores = [c["score"] for c in ranked]
    assert scores[0] == pytest.approx(scores[1], abs=0.2)  # flat lexical field


def test_real_catalogue_search_unchanged_in_lexical_mode():
    """Existing behavioural guarantees hold when embeddings are unavailable."""
    embeddings.reset_backend()
    r = StandardsRetriever()
    res = r.search("cooling unit for the new office block")
    assert res["primary"]["standard"]["code"] == "IS 1391 (Part 1)"


def test_stats_report_retrieval_mode(fake_backend):
    r = _flat_lexical_retriever()
    assert r.stats()["retrieval_mode"] == "hybrid"


def test_env_kill_switch_disables_backend(monkeypatch):
    monkeypatch.setenv("BIS_EMBEDDINGS", "off")
    embeddings.reset_backend()
    try:
        assert embeddings.is_available() is False
        assert embeddings.retrieval_mode() == "lexical"
    finally:
        embeddings.reset_backend()


def test_health_endpoint_reports_retrieval_mode(client):
    data = client.get("/api/health").json()
    assert data["retrieval_mode"] in {"lexical", "hybrid"}


def test_seed_and_snapshot_still_load():
    assert len(catalog.all_standards()) >= 84
