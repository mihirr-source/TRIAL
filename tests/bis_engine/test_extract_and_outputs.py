"""Tests for document extraction, spec-clause generation and report export."""

from __future__ import annotations

import io

import pytest


# ------------------------------------------------------------------ extraction
def _make_pdf(text: str) -> bytes:
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    for i, line in enumerate(text.splitlines()):
        c.drawString(72, 750 - 14 * i, line)
    c.save()
    return buf.getvalue()


def _make_docx(text: str) -> bytes:
    import docx as docx_lib

    d = docx_lib.Document()
    d.add_paragraph(text)
    buf = io.BytesIO()
    d.save(buf)
    return buf.getvalue()


SPEC_TEXT = ("Supply and installation of split air conditioners for the office block. "
             "Packaged drinking water in 20 L jars shall be supplied for staff.")


def test_extract_pdf_and_docx():
    from bis_engine.engine.extract import extract_text

    pdf_text, pages = extract_text(_make_pdf(SPEC_TEXT), "tender.pdf")
    assert "air conditioners" in pdf_text and pages == 1
    docx_text, pages2 = extract_text(_make_docx(SPEC_TEXT), "tender.docx")
    assert "air conditioners" in docx_text and pages2 is None


def test_extract_rejects_unsupported_and_empty():
    from bis_engine.engine.extract import extract_text

    with pytest.raises(Exception, match="Unsupported file type"):
        extract_text(b"MZ fake exe", "thing.exe")
    with pytest.raises(Exception, match="empty"):
        extract_text(b"", "tender.pdf")
    with pytest.raises(Exception, match="10 MB"):
        extract_text(b"x" * (10 * 1024 * 1024 + 1), "big.pdf")


def test_extract_flags_scanned_pdf():
    from bis_engine.engine.extract import extract_text

    # A real, valid PDF page with no text at all -> "no text layer" branch.
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.showPage()
    c.save()
    with pytest.raises(Exception, match="scanned|No text layer"):
        extract_text(buf.getvalue(), "scan.pdf")


def test_extract_corrupt_pdf_message():
    from bis_engine.engine.extract import extract_text

    with pytest.raises(Exception, match="Could not read the PDF"):
        extract_text(b"%PDF-1.4\n%%EOF\n", "broken.pdf")


def test_analyze_file_endpoint(client):
    from fastapi.testclient import TestClient  # noqa: F401  (client fixture)

    res = client.post("/api/analyze/file",
                      files={"file": ("tender.docx", _make_docx(SPEC_TEXT),
                                     "application/vnd.openxmlformats-officedocument.wordprocessingml.document")})
    assert res.status_code == 200, res.text
    report = res.json()
    assert report["meta"]["source_file"] == "tender.docx"
    codes = {p["code"] for p in report["primaries"]}
    assert "IS 1391 (Part 2)" in codes or "IS 1391 (Part 1)" in codes


def test_analyze_file_endpoint_rejects_bad_file(client):
    res = client.post("/api/analyze/file",
                      files={"file": ("thing.exe", b"MZ", "application/octet-stream")})
    assert res.status_code == 422


# ----------------------------------------------------------------- spec clauses
def test_spec_clauses_endpoint(client):
    res = client.post("/api/spec-clauses", json={
        "text": "Supply of split type air conditioners and packaged drinking water jars."})
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["clause_count"] >= 1
    ac = next(c for c in data["clauses"] if c["code"].startswith("IS 1391"))
    assert "IS 1391" in ac["clause_text"]
    assert "BEE" in ac["clause_text"]  # certification sentence included
    assert ac["include_allied"], "allied references must be listed in the clause"


def test_spec_clauses_marks_missing_allied(client):
    text = ("Supply of common burnt clay bricks for the boundary wall. "
            "Tests shall be done as required.")
    res = client.post("/api/spec-clauses", json={"text": text})
    data = res.json()
    brick = next(c for c in data["clauses"] if c["code"] == "IS 1077")
    missing = [a for a in brick["include_allied"] if a["was_missing"]]
    assert any(a["code"] == "IS 3495 (Parts 1–4)" for a in missing)


# --------------------------------------------------------------------- export
def test_export_markdown_endpoint(client):
    res = client.post("/api/analyze/export?format=markdown", json={
        "text": "Supply of packaged drinking water in 20 L jars. TMT bars per IS 1786:2008."})
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/markdown")
    body = res.text
    assert "# Specification health report" in body
    assert "IS 1786" in body
    assert "## Mandatory certification requirements" in body


def test_export_json_endpoint(client):
    res = client.post("/api/analyze/export?format=json", json={
        "text": "Supply of packaged drinking water in 20 L jars."})
    assert res.status_code == 200
    assert res.json()["primaries"]


def test_clause_generator_unit():
    from bis_engine.engine.clauses import build_spec_clauses

    from bis_engine.engine.analyzer import TenderAnalyzer

    from bis_engine.engine.retriever import StandardsRetriever

    report = TenderAnalyzer(StandardsRetriever()).analyze(SPEC_TEXT)
    data = build_spec_clauses(report)
    assert data["clause_count"] == len(report["primaries"])
    for clause in data["clauses"]:
        assert clause["code"]
        assert "shall conform to" in clause["clause_text"]
