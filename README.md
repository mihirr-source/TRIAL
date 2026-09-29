# AI-Powered Standards Recommendation Engine (BIS)

An NLP decision-support engine that maps everyday, multilingual procurement language to
**Indian Standards (BIS codes)** — with allied/normative-standard mapping, latest-version
highlighting, obsolete-citation flagging, mandatory certification alerts, tender-document
intake (PDF/DOCX), a specification clause generator, and a plain-language assistant.

```bash
cd bis_engine
pip install -r requirements.txt
uvicorn main:app --port 8002
```

Open http://localhost:8002 · full documentation in [`bis_engine/README.md`](bis_engine/README.md).

## Feature map

| Capability | Where |
| --- | --- |
| Semantic (not keyword) search — "cooling unit" → IS 1391 | `bis_engine/engine/retriever.py` |
| Allied / normative / test-method bundling | `bis_engine/engine/analyzer.py` |
| Latest version + amendments; obsolete-citation flagging | catalogue `version`/`amendments` + analyzer |
| Mandatory certification alerts (ISI, CRS, BEE, FSSAI, QCO) | catalogue `certifications` |
| Multilingual queries (en / hi / ta / te aliases) | `bis_engine/engine/normalize.py` |
| UI language switcher (English / हिन्दी / తెలుగు) | `bis_engine/static/js/i18n.js` |
| Tender document intake (PDF/DOCX) | `POST /api/analyze/file` |
| Specification clause generator + report export | `POST /api/spec-clauses`, `POST /api/analyze/export` |
| Plain-language assistant (offline template mode + optional LLM) | `/assistant`, `POST /api/assistant` |
| Offline snapshot import (CSV) | `python -m bis_engine.data.importers.bis_snapshot` |

**Data status:** curated seed catalogue (84 standards across 11 sectors, 600+ multilingual aliases),
hand-built in September 2026 — *not* a live mirror of the BIS catalogue. Every
recommendation must be verified against the official BIS catalogue before being cited
in a tender. See the upgrade path in `bis_engine/README.md`.

> This repo previously hosted a second app ("AI Shield"); it was removed and remains
> recoverable from git history.
