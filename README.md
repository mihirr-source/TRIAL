# AI Shield — Harmful Content Blur ( toxicity + NSFW )

A hackathon demo with two parts:

- **`backend/`** — FastAPI server exposing a text-toxicity model and an
  NSFW image classifier (locally-hosted open-source [opennsfw2](https://github.com/bhky/opennsfw2);
  no external AI APIs).
- **`extension/`** — Chrome MV3 extension that runs on **any website**, blurs
  toxic text and NSFW images it finds, and offers click-to-reveal.

---

# AI-Powered Standards Recommendation Engine (BIS)

A second, independent app lives in **`bis_engine/`**: an NLP decision-support
engine that maps everyday, multilingual procurement language to Indian
Standards (BIS codes) — with allied/normative-standard mapping, latest-version
highlighting, obsolete-citation flagging and mandatory certification alerts
(ISI mark, MeitY CRS, BEE star labelling). FastAPI + demo website + tests.

```bash
cd bis_engine
pip install -r requirements.txt
uvicorn main:app --port 8002
```

Open http://localhost:8002 · see [`bis_engine/README.md`](bis_engine/README.md).

---

## Quick start

**1. Backend** (from `backend/`):

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

> First image analysis downloads the opennsfw2 weights (~58 MB). Requires
> internet once; all inference is local afterwards.

**2. Extension**:

1. Open `chrome://extensions`
2. Enable **Developer mode** (top-right)
3. Click **Load unpacked** → select the `extension/` folder
4. Pin it, browse any site — harmful content gets blurred automatically

Open the popup to toggle the shield, adjust the flag threshold, and check
backend status. A red badge on the icon shows how many items are blurred on
the current tab.

## How it works

```
any webpage ──content.js──► background.js ──HTTP──► FastAPI :8000
 (DOM scan)    batches        (MV3 service          │ text  → toxicity model
               findings       worker, all HTTP)     │ image → opennsfw2
                                                    ▼
                              blur + "View Harmful Content" reveal ◄── verdicts
```

- **Text**: visible DOM text nodes are batched (≤40/call) to `POST /analyze-batch`.
- **Images**: `src` URLs (≥100px, deduped) go to `POST /analyze-image-urls`;
  the backend downloads and scores them — users never upload anything.
- Both use threshold 0.7 by default; the popup slider re-evaluates live blurs.
- SPA-safe: a MutationObserver re-scans on DOM changes (debounced).
- Fail-safe: if the backend is down, pages render untouched.

## Backend endpoints

| Method | Path                  | Purpose |
| ------ | --------------------- | ------- |
| GET    | `/health`             | status + model-loaded flag |
| GET    | `/feed`               | 10 demo posts (toxicity + precomputed NSFW scores) |
| POST   | `/analyze`            | `{"text"}` → toxicity score + verdict |
| POST   | `/analyze-batch`      | `{"texts":[...]}` (≤40) → per-text verdicts |
| POST   | `/analyze-image`      | multipart image (≤10 MB) → `nsfw_score` + verdict |
| POST   | `/analyze-image-urls` | `{"urls":[...]}` (≤20) → per-URL verdicts |

Interactive docs at http://localhost:8000/docs. See `backend/README.md` for
curl examples.

## Notes

- `/feed` ships as a demo dataset: toxicity scores are hand-assigned; NSFW
  scores were precomputed once with `python -m nsfw.precompute_feed_scores`
  and hardcoded (all demo images score low — they're landscape photos).
- `backend/model.py` — swap in your own toxicity model behind
  `predict_toxicity(text) -> float`.
