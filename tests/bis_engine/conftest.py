"""Shared fixtures for bis_engine tests.

Embeddings are pinned OFF for the whole suite: the behavioural tests must be
deterministic regardless of whether sentence-transformers / the model cache is
present on the machine (a first real probe can trigger a ~470 MB download).
Hybrid scoring is covered separately with an injected fake backend.
"""

import os

os.environ["BIS_EMBEDDINGS"] = "off"  # forced: suite must not depend on model cache state

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from bis_engine.engine.retriever import StandardsRetriever  # noqa: E402
from bis_engine.main import app  # noqa: E402


@pytest.fixture(scope="session")
def retriever():
    return StandardsRetriever()


@pytest.fixture(scope="module")
def client():
    return TestClient(app)
