"""BIS Standards Recommendation Engine — FastAPI app.

Serves both the JSON API (under /api) and the static demo website (static/).

Run:  uvicorn main:app --reload --port 8002   (from the bis_engine/ directory)
"""

from __future__ import annotations

import re
import sys
from collections import OrderedDict
from pathlib import Path

# Allow `uvicorn main:app` from inside bis_engine/ (cwd) AND from project root.
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from bis_engine.data.catalog import SECTORS, SYNC_HEALTH, all_standards, CATALOG_VERSION
from bis_engine.engine.analyzer import TenderAnalyzer
from bis_engine.engine.retriever import StandardsRetriever

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="AI-Powered Standards Recommendation Engine",
    description="Maps procurement language to Indian Standards (BIS) with allied-standard "
                "mapping, version checks and mandatory certification alerts. MVP demo — "
                "seed catalogue; verify against the official BIS catalogue.",
    version="0.1.0",
)

retriever = StandardsRetriever()
analyzer = TenderAnalyzer(retriever)

# Static files live at /static; pretty routes below serve the SPA pages.
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# --------------------------------------------------------------------- models
class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=20000,
                      description="Product description, technical specification or tender text")

    @field_validator("text")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("text must not be blank")
        return v


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=500)
    top_k: int = Field(6, ge=1, le=20)


# ------------------------------------------------------------------------ API
@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "engine": "bis-recommendation-engine",
        "version": app.version,
        "catalog_version": CATALOG_VERSION,
        "sync": SYNC_HEALTH,
        "stats": retriever.stats(),
    }


@app.get("/api/search")
def search(q: str = Query(..., min_length=2, max_length=500),
           top_k: int = Query(6, ge=1, le=20)) -> dict:
    """Semantic + alias hybrid search. Multilingual queries supported."""
    return retriever.search(q, top_k=top_k)


@app.get("/api/standards")
def list_standards(sector: str | None = Query(None, description="Filter by sector key")) -> dict:
    if sector and sector not in SECTORS:
        raise HTTPException(status_code=404, detail=f"Unknown sector '{sector}'")
    standards = [s for s in all_standards() if not sector or s["sector"] == sector]
    return {"count": len(standards), "sectors": SECTORS, "standards": standards}


@app.get("/api/standards/{code}")
def get_standard(code: str) -> dict:
    from bis_engine.data.catalog import get_by_code
    std = get_by_code(code)
    if not std:
        raise HTTPException(status_code=404, detail=f"Standard '{code}' not in MVP catalogue")
    return std


@app.post("/api/analyze")
def analyze(req: AnalyzeRequest) -> dict:
    """Full tender analysis: primaries, allied gaps, certifications, obsolete flags."""
    try:
        return analyzer.analyze(req.text)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/certifications")
def certifications() -> dict:
    """Mandatory certification schemes, grouped by base scheme name."""
    groups: "OrderedDict[str, dict]" = {}
    for std in all_standards():
        for cert in std.get("certifications", []):
            base = re.split(r"\s+[—+]\s+", cert["scheme"])[0].strip()
            g = groups.setdefault(base, {"scheme": base, "authority": cert["authority"],
                                         "notes": [], "standards": []})
            if cert["note"] not in g["notes"]:
                g["notes"].append(cert["note"])
            if std["code"] not in g["standards"]:
                g["standards"].append(std["code"])
    schemes = [{**g, "note": " · ".join(g.pop("notes"))} for g in groups.values()]
    return {"count": len(schemes), "schemes": schemes}


# -------------------------------------------------------------------- website
@app.get("/")
def home():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/analyzer")
def analyzer_page():
    return FileResponse(STATIC_DIR / "analyzer.html")


@app.get("/standards")
def standards_page():
    return FileResponse(STATIC_DIR / "standards.html")


@app.get("/standards/{code}")
def standard_detail_page(code: str):
    return FileResponse(STATIC_DIR / "standard.html")


@app.get("/alerts")
def alerts_page():
    return FileResponse(STATIC_DIR / "alerts.html")


@app.get("/docs-page")
def docs_page():
    return FileResponse(STATIC_DIR / "docs.html")
