# AI-Powered Standards Recommendation Engine

An NLP decision-support engine that maps everyday, multilingual procurement
language to **Indian Standards (BIS codes)** — including the allied/normative
standards, latest versions/amendments and mandatory certification alerts that
tender specifications routinely miss. Ships with a FastAPI JSON API **and** a
complete multilingual demo website (English / हिन्दी / తెలుగు).

> **Data status:** runs on a curated **seed catalogue** (84 standards across 11
> sectors, 600+ multilingual aliases) hand-built for the demo, optionally
> extended by **offline CSV snapshot imports**. It is *not* a live mirror of
> the BIS catalogue. Every recommendation must be verified against the official
> BIS catalogue before being cited in a tender. See *Upgrade path* below.

## Quick start

```bash
pip install -r requirements.txt
uvicorn main:app --port 8002          # from bis_engine/ (works) or repo root
```

Open http://localhost:8002 — home page with semantic search. Other pages:
`/analyzer` (paste **or upload** a tender), `/standards`, `/alerts`,
`/assistant` (plain-language AI chat), `/docs-page`. Interactive OpenAPI:
`/docs`, `/redoc`.

Use the **language switcher** in the header (English / हिन्दी / తెలుగు) — the
whole UI, the assistant's answers and report labels follow it.

## What it does (problem-statement feature map)

| Expected feature | Where it lives |
| --- | --- |
| Accept descriptions / specifications / **tender documents (PDF/DOCX)** | `POST /api/analyze`, `POST /api/analyze/file`, `/analyzer` page |
| Semantic (not keyword) recommendation | char n-gram TF-IDF + alias index, blended with **multilingual sentence embeddings** when available — "cooling unit" → IS 1391 (Part 1), "sariya" → IS 1786, "monoblock pump" → IS 9079 |
| Allied / normative / test-method / safety standards | dependency graph per standard (now **closed**: every IS reference resolves); analyzer reports what's missing from your text |
| Latest version + amendments highlighted | every result carries `version` + `amendments`; obsolete citations (e.g. `IS 456:1978`) flagged with the correct citation |
| Mandatory certification suggestions | ISI-mark QCOs, MeitY CRS, BEE star labelling, FSSAI, medical-gloves QCO — auto-alerted per product |
| **Specification-ready output** | `POST /api/spec-clauses` draft clauses (code + edition + allied + certification sentence); Markdown/JSON report export |
| Multilingual input, UI and **natural-language Q&A** | en/hi/ta/te aliases; UI switcher; `/assistant` grounded chatbot |
| Honest freshness | `/api/health` reports sync mode, snapshot records and retrieval mode |

## The AI assistant

`/assistant` (or the 💬 widget on every page) answers in simple language:

- **Template mode (default, offline, zero keys):** intent detection (explain a
  code, recommend for a product, certification questions, version questions)
  and replies composed *only from the catalogue*, with hand-written simple
  explainers for the most-searched standards. Structurally cannot invent codes.
- **LLM mode (optional):** set `BIS_LLM_API_KEY` (and optionally
  `BIS_LLM_MODEL`, default `gemini-2.0-flash`) and template answers are
  rephrased by an LLM that is *only* allowed to cite the catalogue sources
  retrieved for the question. Any failure silently falls back to template mode.
  The response always reports `"mode": "template" | "llm"`.
- Replies are delivered in the UI language (en/hi/te).

## Offline catalogue import (snapshot)

The BIS catalogue has no free public API and the full data is licensed, so the
supported production path is an **offline import** — no runtime fetching:

```bash
# 1. Copy the template and fill rows (code,title,version,status,sector,category)
cp bis_engine/data/snapshots/template.csv my_snapshot.csv
# 2. Import
python -m bis_engine.data.importers.bis_snapshot --input my_snapshot.csv
#    add --force to let snapshot rows shadow seed entries of the same code
# 3. Restart the app — /api/health now reports sync.mode = "seed+snapshot"
```

Validation is strict (code format, known sector, status vocabulary); rejects
are reported per line, never silently dropped. Seed records stay authoritative:
aliases/allied/certifications enrich snapshot rows later by curation.

## Retrieval modes

| Mode | When | Behaviour |
| --- | --- | --- |
| `lexical` | sentence-transformers missing, no model cache, or `BIS_EMBEDDINGS=off` | TF-IDF (char 3–5 grams) + alias bonus — the original engine, fully deterministic |
| `hybrid` | `sentence-transformers` installed and model available | adds multilingual embedding similarity (55% lexical / 45% semantic blend) |

Embeddings load lazily on first search; a failed probe is sticky per process so
offline demo machines never stall. The **first** embedded query downloads the model
once (~470 MB, cached afterwards) — set `BIS_EMBEDDINGS=off` for offline demos.
`/api/health` reports the active mode.

## API summary

| Method | Path | Purpose |
| ------ | ---- | ------- |
| GET  | `/api/health` | status, catalogue version, sync + retrieval modes, index stats |
| GET  | `/api/search?q=…&top_k=6` | hybrid semantic + alias search (multilingual) |
| POST | `/api/analyze` | full tender analysis → primaries, allied gaps, certs, obsolete flags |
| POST | `/api/analyze/file` | PDF/DOCX upload → extraction + same analysis |
| POST | `/api/spec-clauses` | draft specification clauses per primary standard |
| POST | `/api/analyze/export?format=markdown\|json` | downloadable report |
| POST | `/api/assistant` | plain-language Q&A (`{message, lang, history?}`) |
| GET  | `/api/standards[?sector=…]` | browse catalogue by sector |
| GET  | `/api/standards/{code}` | one standard (loose match: `IS 13252` → `IS 13252 (Part 1)`) |
| GET  | `/api/certifications` | mandatory schemes grouped, with applicable standards |

## Architecture

```
query / tender text / PDF / DOCX
      │                    └─ extract.py (pdfplumber / python-docx, caps, no OCR)
      ▼
normalize.py  ── NFC + script detection (en/hi/ta/te/…)
      │
retriever.py  ── hybrid scoring
      │   • char_wb 3–5 gram TF-IDF over title+summary+aliases+category
      │   • exact alias index (multilingual, plural-tolerant) as additive bonus
      │   • optional multilingual embeddings (lazy, graceful fallback)
      ▼
analyzer.py   ── clause split → per-clause retrieval →
                 allied-graph expansion → citation regex check →
                 certification aggregation → PASS/WARN/FAIL report
      │
clauses.py    ── specification clauses + Markdown export
assistant.py  ── intent routing → grounded templates (en/hi/te) → optional LLM
```

## Tests

```bash
python -m pytest tests/bis_engine/ -v    # from repo root (84 tests)
```

Covers: catalogue integrity (closed allied graph, required fields, sectors),
semantic/colloquial/multilingual search, analyzer flows, importer validation &
merge, extraction (PDF/DOCX/scanned/corrupt), clauses/export, assistant
intents in three languages, LLM fallback, and the API layer.

## Upgrade path (seed → production)

1. **Live data**: the offline importer's record shape is the contract — point a
   scheduled job at a licensed BIS catalogue/StandardsPortal-style feed and
   import snapshots; keep curator enrichment for aliases/allied/certifications.
2. **Better NLP**: the hybrid stack already accepts any encoder via
   `embeddings.set_backend` — swap in LaBSE/IndicBERT for stronger Indic
   retrieval; the deterministic alias layer stays for exact codes.
3. **OCR intake**: add an OCR stage upstream of `extract.extract_text` for
   scanned tenders (deliberately out of scope in v0.2).
4. **Portal integration**: the JSON API is designed to be embedded into e-
   procurement portals (GeM-style) as an assistive side panel.
5. **Compliance**: legal review of every alert string before use in real
   procurement; output is decision support, never a compliance guarantee.
