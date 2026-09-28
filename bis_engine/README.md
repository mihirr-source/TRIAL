# AI-Powered Standards Recommendation Engine (MVP)

An NLP decision-support engine that maps everyday, multilingual procurement
language to **Indian Standards (BIS codes)** — including the allied/normative
standards, latest versions/amendments and mandatory certification alerts that
tender specifications routinely miss. Ships with a FastAPI JSON API **and** a
complete demo website.

> **Data status:** runs on a curated **seed catalogue** (41 standards, 290+
> multilingual aliases) hand-built for the demo. It is *not* a live mirror of
> the BIS catalogue. Every recommendation must be verified against the official
> BIS catalogue before being cited in a tender. See *Upgrade path* below.

## Quick start

```bash
pip install -r requirements.txt
uvicorn main:app --port 8002          # from bis_engine/ (works) or repo root
```

Open http://localhost:8002 — home page with semantic search. Other pages:
`/analyzer` (paste a tender), `/standards`, `/alerts`, `/docs-page`.
Interactive OpenAPI: `/docs`, `/redoc`.

## What it does (problem-statement feature map)

| Expected feature | Where it lives |
| --- | --- |
| Accept descriptions / specifications / tender documents | `POST /api/analyze`, `/analyzer` page |
| Semantic (not keyword) recommendation | char n-gram TF-IDF + alias index — "cooling unit" → IS 1391 (Part 1), "sariya" → IS 1786 |
| Allied / normative / test-method / safety standards | dependency graph per standard; analyzer reports what's missing from your text |
| Latest version + amendments highlighted | every result carries `version` + `amendments`; obsolete citations (e.g. `IS 456:1978`) flagged with the correct citation |
| Mandatory certification suggestions | ISI-mark QCOs, MeitY CRS, BEE star labelling, FSSAI — auto-alerted per product |
| Multilingual input & natural queries | Hindi/Tamil alias vocabulary, script auto-detection, plural-tolerant matching |

## API summary

| Method | Path | Purpose |
| ------ | ---- | ------- |
| GET  | `/api/health` | status, catalogue version, sync mode, index stats |
| GET  | `/api/search?q=…&top_k=6` | hybrid semantic + alias search (multilingual) |
| POST | `/api/analyze` | full tender analysis → primaries, allied gaps, certs, obsolete flags |
| GET  | `/api/standards[?sector=…]` | browse catalogue by sector |
| GET  | `/api/standards/{code}` | one standard (loose match: `IS 13252` → `IS 13252 (Part 1)`) |
| GET  | `/api/certifications` | mandatory schemes grouped, with applicable standards |

## Architecture

```
query / tender text
      │
      ▼
normalize.py  ── NFC + script detection (en/hi/ta/…)
      │
      ▼
retriever.py  ── hybrid scoring
      │   • char_wb 3–5 gram TF-IDF over title+summary+aliases+category
      │   • exact alias index (multilingual, plural-tolerant) as additive bonus
      │   • secondary name-matrix for code-number matching
      ▼
analyzer.py   ── clause split → per-clause retrieval →
                 allied-graph expansion → citation regex check →
                 certification aggregation → PASS/WARN/FAIL report
```

## Tests

```bash
python -m pytest tests/bis_engine/ -v    # 23 tests from repo root
```

## Upgrade path (seed → production)

1. **Live data**: replace `data/catalog.py` with a sync job against the BIS
   catalogue / StandardsPortal-style licensed feed; keep the same record shape.
   The `/api/health` payload already exposes `sync.mode` so the UI can show
   freshness honestly.
2. **Better NLP**: swap the lexical stage for multilingual sentence
   embeddings (e.g. LaBSE/IndicBERT) with this retriever as candidate generator
   (hybrid retrieval), keeping the deterministic alias layer for exact codes.
3. **Document intake**: the MVP analyzes pasted text (≤20k chars); add
   PDF/DOCX extraction upstream of `analyzer.analyze`.
4. **Compliance**: legal review of every alert string before use in real
   procurement; output is decision support, never a compliance guarantee.
