"""Precompute NSFW scores for the demo feed images.

Downloads each feed image once, runs the opennsfw2 model on it, and prints
a ready-to-paste table so the scores can be hardcoded into the mock feed.
Run from backend/:  python -m nsfw.precompute_feed_scores
"""

import os
import sys

import urllib.request

from .predictor import predict_nsfw

FEED_IMAGES = [f"https://picsum.photos/600/400?random={n}" for n in range(1, 11)]

DEMO_DIR = os.path.join(os.path.dirname(__file__), "demo_images")

UA = {"User-Agent": "Mozilla/5.0 (AI Shield demo)"}


def download(url: str, dest: str) -> None:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as resp, open(dest, "wb") as f:
        f.write(resp.read())


def main() -> None:
    os.makedirs(DEMO_DIR, exist_ok=True)
    print(f"{'n':>2}  {'nsfw_score':>10}  file")
    for n, url in enumerate(FEED_IMAGES, start=1):
        dest = os.path.join(DEMO_DIR, f"feed_{n}.jpg")
        if not os.path.exists(dest):
            try:
                download(url, dest)
            except Exception as exc:  # keep going, report at the end
                print(f"{n:>2}  {'ERROR':>10}  {url} ({exc})")
                continue
        try:
            score = predict_nsfw(dest)
        except Exception as exc:
            print(f"{n:>2}  {'ERROR':>10}  {dest} ({exc})")
            continue
        print(f"{n:>2}  {score:>10.4f}  {os.path.basename(dest)}")

    print(
        "\nDone. Paste these into MOCK_POSTS as nsfw_score "
        "(is_nsfw = score > 0.7)."
    )


if __name__ == "__main__":
    sys.exit(main())
