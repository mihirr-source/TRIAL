"""opennsfw2-backed NSFW predictor.

opennsfw2's `predict_image` already manages the model as a lazy module-level
singleton: the first call downloads/loads the weights, every later call
reuses them. We hold a lock during inference so concurrent requests
serialize cleanly (avoids TF concurrency issues and memory spikes).
"""

import threading

import opennsfw2 as n2

_inference_lock = threading.Lock()
_loaded = False


def is_model_loaded() -> bool:
    """True once at least one prediction has run (weights are in memory)."""
    return _loaded


def predict_nsfw(image_path: str) -> float:
    """Return the NSFW probability of the image at `image_path` in [0.0, 1.0].

    0.0 = clearly safe, 1.0 = clearly explicit. Raises if the file cannot
    be read as an image (callers are expected to handle that).
    """
    global _loaded
    with _inference_lock:
        score = n2.predict_image(image_path)
        _loaded = True
    return float(score)
