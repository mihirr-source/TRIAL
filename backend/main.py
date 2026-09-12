import os
import tempfile
import urllib.request

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from model import predict_toxicity
from nsfw import is_model_loaded, predict_nsfw

app = FastAPI(title="Social Media Safety Demo API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# GET /health — extension/popup status check
# ---------------------------------------------------------------------------


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_loaded": is_model_loaded(),
    }


# ---------------------------------------------------------------------------
# GET /feed — hardcoded mock Instagram-style posts
# (nsfw_score values were precomputed once with:
#   python -m nsfw.precompute_feed_scores
# and then baked in here so the demo feed needs no live image analysis.)
# ---------------------------------------------------------------------------

MOCK_POSTS = [
    {
        "id": 1,
        "author": "sunny_travels",
        "avatar_url": "https://i.pravatar.cc/150?img=1",
        "image_url": "https://picsum.photos/600/400?random=1",
        "text": "Golden hour on the coast. No filter needed. #sunset #travel",
        "toxicity_score": 0.05,
        "nsfw_score": 0.0041,
    },
    {
        "id": 2,
        "author": "coffee_and_code",
        "avatar_url": "https://i.pravatar.cc/150?img=2",
        "image_url": "https://picsum.photos/600/400?random=2",
        "text": "Shipped a tiny side project today. Small wins add up!",
        "toxicity_score": 0.08,
        "nsfw_score": 0.0839,
    },
    {
        "id": 3,
        "author": "plant_parent_92",
        "avatar_url": "https://i.pravatar.cc/150?img=3",
        "image_url": "https://picsum.photos/600/400?random=3",
        "text": "My monstera finally has a new leaf 🌿 Reacting slowly but surely.",
        "toxicity_score": 0.12,
        "nsfw_score": 0.0128,
    },
    {
        "id": 4,
        "author": "weekend_baker",
        "avatar_url": "https://i.pravatar.cc/150?img=4",
        "image_url": "https://picsum.photos/600/400?random=4",
        "text": "Sourdough attempt #7. Crumb is getting better!",
        "toxicity_score": 0.15,
        "nsfw_score": 0.0034,
    },
    {
        "id": 5,
        "author": "city_wanderer",
        "avatar_url": "https://i.pravatar.cc/150?img=5",
        "image_url": "https://picsum.photos/600/400?random=5",
        "text": "Some people have zero taste. This street art deserves better.",
        "toxicity_score": 0.35,
        "nsfw_score": 0.0779,
    },
    {
        "id": 6,
        "author": "gymrat_dan",
        "avatar_url": "https://i.pravatar.cc/150?img=6",
        "image_url": "https://picsum.photos/600/400?random=6",
        "text": "If you can't keep up, stay out of my way. Weak effort everywhere.",
        "toxicity_score": 0.55,
        "nsfw_score": 0.0224,
    },
    {
        "id": 7,
        "author": "anon_rants",
        "avatar_url": "https://i.pravatar.cc/150?img=7",
        "image_url": "https://picsum.photos/600/400?random=7",
        "text": "Imagine being this clueless. Total embarrassment.",
        "toxicity_score": 0.72,
        "nsfw_score": 0.0001,
    },
    {
        "id": 8,
        "author": "troll_account_x",
        "avatar_url": "https://i.pravatar.cc/150?img=8",
        "image_url": "https://picsum.photos/600/400?random=8",
        "text": "Nobody likes your posts. Delete your account, loser.",
        "toxicity_score": 0.88,
        "nsfw_score": 0.0001,
    },
    {
        "id": 9,
        "author": "flame_war_404",
        "avatar_url": "https://i.pravatar.cc/150?img=9",
        "image_url": "https://picsum.photos/600/400?random=9",
        "text": "You're absolutely worthless at this. Everyone is laughing at you.",
        "toxicity_score": 0.95,
        "nsfw_score": 0.0023,
    },
    {
        "id": 10,
        "author": "chaos_poster",
        "avatar_url": "https://i.pravatar.cc/150?img=10",
        "image_url": "https://picsum.photos/600/400?random=10",
        "text": "Block me if this offends you. Your feelings are not my problem.",
        "toxicity_score": 0.90,
        "nsfw_score": 0.0006,
    },
]


@app.get("/feed")
def get_feed():
    """Return the mock feed with toxicity and precomputed NSFW scores."""
    return MOCK_POSTS


# ---------------------------------------------------------------------------
# POST /analyze — text toxicity
# ---------------------------------------------------------------------------


class AnalyzeRequest(BaseModel):
    text: str


@app.post("/analyze")
def analyze(payload: AnalyzeRequest):
    """Analyze text and return its toxicity score."""
    score = predict_toxicity(payload.text)
    return {
        "text": payload.text,
        "toxicity_score": score,
        "is_toxic": score > 0.7,
    }


# ---------------------------------------------------------------------------
# POST /analyze-batch — toxicity for many texts in one call (web extension)
# ---------------------------------------------------------------------------


class AnalyzeBatchRequest(BaseModel):
    texts: list[str] = Field(..., min_length=1, max_length=40)


@app.post("/analyze-batch")
def analyze_batch(payload: AnalyzeBatchRequest):
    """Score up to 40 texts in a single request."""
    results = []
    for text in payload.texts:
        score = predict_toxicity(text)
        results.append(
            {
                "text": text,
                "toxicity_score": score,
                "is_toxic": score > 0.7,
            }
        )
    return {"results": results}


# ---------------------------------------------------------------------------
# POST /analyze-image — NSFW classification of an uploaded image
# ---------------------------------------------------------------------------

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB


@app.post("/analyze-image")
def analyze_image(file: UploadFile = File(...)):
    """Score an uploaded image for NSFW content (threshold 0.7)."""
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=415, detail="File must be an image")

    suffix = os.path.splitext(file.filename or "upload.jpg")[1] or ".jpg"
    fd, temp_path = tempfile.mkstemp(prefix="ai_shield_", suffix=suffix)
    os.close(fd)

    size = 0
    try:
        with open(temp_path, "wb") as buffer:
            while chunk := file.file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=413, detail="Image exceeds 10 MB limit"
                    )
                buffer.write(chunk)

        try:
            score = predict_nsfw(temp_path)
        except Exception:
            raise HTTPException(
                status_code=422,
                detail="Could not read the file as an image",
            )

        return {"nsfw_score": score, "is_nsfw": score > 0.7}
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# POST /analyze-image-urls — batch NSFW scoring of remote image URLs
# (this is what the web extension uses so users never upload anything)
# ---------------------------------------------------------------------------


class AnalyzeImageUrlsRequest(BaseModel):
    urls: list[str] = Field(..., min_length=1, max_length=20)


@app.post("/analyze-image-urls")
def analyze_image_urls(payload: AnalyzeImageUrlsRequest):
    """Download and NSFW-score a batch of image URLs (max 20 per call)."""
    results = []
    for url in payload.urls:
        item = {"url": url, "nsfw_score": None, "is_nsfw": False, "error": None}
        fd, temp_path = tempfile.mkstemp(prefix="ai_shield_url_", suffix=".img")
        os.close(fd)
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (AI Shield demo)",
                },
            )
            with urllib.request.urlopen(req, timeout=15) as resp, open(
                temp_path, "wb"
            ) as out:
                out.write(resp.read(11 * 1024 * 1024))  # cap ~10 MB
            score = predict_nsfw(temp_path)
            item["nsfw_score"] = score
            item["is_nsfw"] = score > 0.7
        except Exception as exc:
            item["error"] = f"{type(exc).__name__}: {exc}"
        finally:
            try:
                os.remove(temp_path)
            except OSError:
                pass
        results.append(item)
    return {"results": results}
