# Social Media Safety Demo — Backend

FastAPI backend powering the **AI Shield** demo: text toxicity analysis +
NSFW image classification (via the locally-hosted open-source
[opennsfw2](https://github.com/bhky/opennsfw2) model — no external APIs),
plus the API consumed by the cross-site browser extension in `../extension/`.

## Setup

```bash
pip install -r requirements.txt
```

Run the server (from this `backend/` folder):

```bash
uvicorn main:app --reload --port 8000
```

> First image analysis downloads the opennsfw2 weights (~58 MB) automatically;
> subsequent calls are pure inference. Interactive docs: http://localhost:8000/docs

## Endpoints

| Method | Path                  | Body / Params                     | Returns |
| ------ | --------------------- | --------------------------------- | ------- |
| GET    | `/health`             | —                                 | `{"status", "model_loaded"}` |
| GET    | `/feed`               | —                                 | 10 mock posts, each with `toxicity_score` and precomputed `nsfw_score` / `is_nsfw` |
| POST   | `/analyze`            | `{"text": "..."}`                 | `{"text", "toxicity_score", "is_toxic"}` (threshold 0.7) |
| POST   | `/analyze-image`      | multipart `file` (image ≤ 10 MB)  | `{"nsfw_score", "is_nsfw"}` (threshold 0.7) |
| POST   | `/analyze-image-urls` | `{"urls": ["https://...", ...]}` (1–20) | `{"results": [{"url", "nsfw_score", "is_nsfw", "error"}]}` |

## Testing with curl

```bash
# health
curl http://localhost:8000/health

# text toxicity
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "delete your account loser nobody likes you"}'

# image upload (safe example)
curl -X POST http://localhost:8000/analyze-image -F "file=@nsfw/demo_images/feed_1.jpg"

# batch URL scoring
curl -X POST http://localhost:8000/analyze-image-urls \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://picsum.photos/600/400?random=1", "https://picsum.photos/600/400?random=2"]}'
```

For the explicit side of the test, upload any explicit image via /docs or:

```bash
curl -X POST http://localhost:8000/analyze-image -F "file=@path/to/explicit.jpg"
```

## Notes

- `model.py` — `predict_toxicity(text) -> float`; swap in your own model.
- `nsfw/` — opennsfw2 wrapper. `predict_nsfw(path) -> float`, loaded once
  (lazy singleton) and reused for every request.
- Feed NSFW scores were precomputed once with
  `python -m nsfw.precompute_feed_scores` and hardcoded into `/feed`.
- CORS is open (`*` + `http://localhost:3000`) for local development; the
  extension talks to `http://localhost:8000` via its `host_permissions`.
