"""NSFW image classification package.

Wraps opennsfw2 (a locally-hosted open-source vision model — no external
API calls, no training required) behind a tiny, stable interface.
"""

from .predictor import is_model_loaded, predict_nsfw

__all__ = ["predict_nsfw", "is_model_loaded"]
