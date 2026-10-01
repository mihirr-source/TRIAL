"""PARAKH — AI-Powered Standards Recommendation Engine — FastAPI app.

Serves both the JSON API (under /api) and the static demo website (static/).

Run:  uvicorn main:app --reload --port 8002   (from the bis_engine/ directory)
"""

from __future__ import annotations

import os
import re
import sys
from collections import OrderedDict
from pathlib import Path

# Allow `uvicorn main:app` from inside bis_engine/ (cwd) AND from project root.
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(_ROOT / ".env")
    load_dotenv()
except ImportError:
    pass

from fastapi import FastAPI, File, HTTPException, Query, Request, Response, UploadFile, status
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from bis_engine.auth import auth_router, get_current_user_optional
from bis_engine.bids_api import bids_router
from bis_engine.data.catalog import SECTORS, SYNC_HEALTH, all_standards, CATALOG_VERSION
from bis_engine.engine.analyzer import TenderAnalyzer
from bis_engine.engine.assistant import StandardsAssistant
from bis_engine.engine.clauses import build_spec_clauses, report_to_markdown
from bis_engine.engine.extract import ExtractionError, extract_text
from bis_engine.engine.retriever import StandardsRetriever

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="PARAKH — AI-Powered Standards Recommendation Engine",
    description="Maps procurement language to Indian Standards (BIS) with allied-standard "
                "mapping, version checks and mandatory certification alerts. MVP demo — "
                "seed catalogue; verify against the official BIS catalogue.",
    version="0.3.0",
)

# Authentication & Bids routers
app.include_router(auth_router)
app.include_router(bids_router)

PROTECTED_PAGES = {"/", "/analyzer", "/standards", "/alerts", "/assistant", "/docs-page", "/customer", "/vendor"}


def _is_auth_enforced() -> bool:
    if os.environ.get("BIS_DISABLE_AUTH") == "1":
        return False
    # Preserve legacy test execution unless explicitly testing auth enforcement
    if os.environ.get("PYTEST_CURRENT_TEST") and not os.environ.get("BIS_ENFORCE_AUTH_TEST"):
        return False
    return True


@app.middleware("http")
async def no_cache_middleware(request: Request, call_next):
    response = await call_next(request)
    path = request.url.path
    if path.startswith("/static") or path in PROTECTED_PAGES or path == "/login":
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


@app.middleware("http")
async def auth_gate_middleware(request: Request, call_next):
    path = request.url.path

    # Unprotected routes & static assets
    if (
        path.startswith("/static")
        or path.startswith("/api/auth")
        or path in {"/login", "/api/health", "/docs", "/redoc", "/openapi.json"}
        or not _is_auth_enforced()
    ):
        return await call_next(request)

    user = get_current_user_optional(request)
    if not user:
        if path in PROTECTED_PAGES or path.startswith("/standards/"):
            return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
        if path.startswith("/api/"):
            return Response(
                content='{"detail":"Authentication required. Please log in."}',
                status_code=status.HTTP_401_UNAUTHORIZED,
                media_type="application/json",
            )

    return await call_next(request)

retriever = StandardsRetriever()
analyzer = TenderAnalyzer(retriever)
assistant = StandardsAssistant(retriever)

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


class AssistantRequest(BaseModel):
    message: str = Field(..., min_length=2, max_length=1000)
    lang: str | None = Field(None, pattern="^(en|hi|te)$")
    history: list[dict] | None = None


# ------------------------------------------------------------------------ API
@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "engine": "bis-recommendation-engine",
        "version": app.version,
        "catalog_version": CATALOG_VERSION,
        "sync": SYNC_HEALTH,
        "retrieval_mode": retriever.stats().get("retrieval_mode", "lexical"),
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


@app.post("/api/analyze/file")
async def analyze_file(file: UploadFile = File(...)) -> dict:
    """Tender-document intake: extract text from a PDF/DOCX upload, then run
    the same analysis pipeline as POST /api/analyze."""
    data = await file.read()
    try:
        text, _pages = extract_text(data, file.filename or "")
    except ExtractionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    try:
        report = analyzer.analyze(text)
    except ValueError as exc:
        detail = str(exc)
        if "20,000" in detail or "20000" in detail:
            detail = ("Document text exceeds the 20,000-character analysis limit — "
                      "upload the relevant specification section.")
        raise HTTPException(status_code=422, detail=detail) from exc
    report["meta"]["source_file"] = file.filename
    return report


@app.post("/api/spec-clauses")
def spec_clauses(req: AnalyzeRequest) -> dict:
    """Draft tender clauses (code + latest version + allied + certification) per primary."""
    try:
        report = analyzer.analyze(req.text)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return build_spec_clauses(report)


@app.post("/api/analyze/export")
def analyze_export(req: AnalyzeRequest, format: str = Query("markdown", pattern="^(markdown|json)$")):
    """Download the analysis report as Markdown (default) or JSON."""
    try:
        report = analyzer.analyze(req.text)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if format == "json":
        return report
    md = report_to_markdown(report)
    return Response(
        content=md,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="specification-report.md"'},
    )


@app.post("/api/assistant")
def assistant_endpoint(req: AssistantRequest) -> dict:
    """Plain-language assistant. Template mode by default; LLM mode activates
    automatically when BIS_LLM_API_KEY is set (falls back on any failure)."""
    try:
        return assistant.answer(req.message, lang=req.lang, history=req.history)
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
@app.get("/login")
def login_page(request: Request):
    if get_current_user_optional(request):
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    return FileResponse(STATIC_DIR / "login.html")


@app.get("/")
def home():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/customer")
def customer_page(request: Request):
    user = get_current_user_optional(request)
    if user:
        is_vendor = user.get("role") == "vendor" or "vendor" in user.get("email", "").lower() or "supplier" in user.get("email", "").lower()
        if is_vendor:
            return RedirectResponse(url="/vendor", status_code=status.HTTP_302_FOUND)
    return FileResponse(STATIC_DIR / "customer.html")


@app.get("/vendor")
def vendor_page(request: Request):
    user = get_current_user_optional(request)
    if user:
        is_vendor = user.get("role") == "vendor" or "vendor" in user.get("email", "").lower() or "supplier" in user.get("email", "").lower()
        if not is_vendor:
            return RedirectResponse(url="/customer", status_code=status.HTTP_302_FOUND)
    return FileResponse(STATIC_DIR / "vendor.html")


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


@app.get("/assistant")
def assistant_page():
    return FileResponse(STATIC_DIR / "assistant.html")


@app.get("/docs-page")
def docs_page():
    return FileResponse(STATIC_DIR / "docs.html")
