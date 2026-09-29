"""Embedding backend: multilingual sentence embeddings for hybrid retrieval.

Deliberately optional. If `sentence-transformers` (or its model cache) is not
available — offline demo machines, CI, restricted installs — every function
here degrades gracefully and the retriever runs in lexical-only mode with
identical behaviour to the pre-v0.2 engine.

Model: paraphrase-multilingual-MiniLM-L12-v2 (118 languages incl. Indic,
~470 MB download on first use, cached afterwards). Disable entirely with
BIS_EMBEDDINGS=off.

Test hooks: `set_backend` / `reset_backend` let the test-suite inject a fake
encoder (deterministic, no network) instead of the real model.
"""

from __future__ import annotations

import logging
import os
import threading

log = logging.getLogger("bis_engine.embeddings")

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

_lock = threading.Lock()
_state: dict = {"backend": None, "failed": False, "explicit_off": False}


def _env_disabled() -> bool:
    return os.environ.get("BIS_EMBEDDINGS", "").strip().lower() in {"off", "0", "false", "no"}


class _RealBackend:
    """Lazily-imported sentence-transformers encoder."""

    name = "hybrid"

    def __init__(self) -> None:
        from sentence_transformers import SentenceTransformer  # type: ignore

        self.model = SentenceTransformer(MODEL_NAME)

    def encode(self, texts: list[str]) -> list[list[float]]:
        return [row.tolist() for row in self.model.encode(texts, normalize_embeddings=True)]


def set_backend(backend) -> None:
    """Inject a backend object with `.name` and `.encode(list[str]) -> vectors`."""
    with _lock:
        _state["backend"] = backend
        _state["failed"] = False


def reset_backend() -> None:
    """Drop any injected/test backend so the next use re-probes the real one."""
    with _lock:
        _state["backend"] = None
        _state["failed"] = False


def get_backend():
    """Return the active backend or None (lexical-only mode).

    Probing happens at most once per process; a failed probe (missing package,
    no model cache, import error) is sticky and never retried mid-request.
    """
    with _lock:
        if _state["backend"] is not None:
            return _state["backend"]
        if _state["failed"] or _state["explicit_off"]:
            return None
        if _env_disabled():
            _state["explicit_off"] = True
            return None
        try:
            backend = _RealBackend()
        except Exception as exc:  # ImportError, model download failure, HF hub errors
            log.warning("Embedding backend unavailable (%s); running lexical-only.", exc)
            _state["failed"] = True
            return None
        _state["backend"] = backend
        return backend


def retrieval_mode() -> str:
    backend = get_backend()
    return backend.name if backend is not None else "lexical"


def is_available() -> bool:
    return get_backend() is not None
