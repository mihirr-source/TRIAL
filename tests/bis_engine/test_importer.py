"""Tests for the offline BIS catalogue snapshot importer (v0.2)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bis_engine.data import catalog
from bis_engine.data.importers import bis_snapshot

GOOD_ROW = {
    "code": "IS 7777",
    "title": "Snapshot example product — Specification",
    "version": "2024",
    "status": "active",
    "sector": "construction",
    "category": "Snapshot examples",
}


def _write_csv(tmp_path: Path, rows: list[dict]) -> Path:
    path = tmp_path / "snapshot.csv"
    header = "code,title,version,status,sector,category\n"
    lines = [header] + [
        ",".join(row.get(col, "") for col in
                 ("code", "title", "version", "status", "sector", "category")) + "\n"
        for row in rows
    ]
    path.write_text("".join(lines), encoding="utf-8")
    return path


# ------------------------------------------------------------------ validation
def test_validate_row_accepts_valid_record():
    rec, reason = bis_snapshot.validate_row(GOOD_ROW)
    assert reason is None
    assert rec["code"] == "IS 7777"
    assert rec["provenance"] == "snapshot"
    assert rec["sector"] == "construction"


def test_validate_row_rejects_bad_code_and_sector():
    bad = bis_snapshot.validate_row({**GOOD_ROW, "code": "ABC 12"})
    assert bad == (None, "unrecognised code format: 'ABC 12'")
    bad = bis_snapshot.validate_row({**GOOD_ROW, "sector": "aviation"})
    assert bad[1].startswith("unknown sector")
    bad = bis_snapshot.validate_row({**GOOD_ROW, "title": ""})
    assert bad[1] == "missing title"
    bad = bis_snapshot.validate_row({**GOOD_ROW, "status": "maybe"})
    assert bad[1].startswith("unknown status")


# ------------------------------------------------------------------- importing
def test_import_snapshot_rejects_and_reports_lines():
    rows = [GOOD_ROW, {"code": "", "title": "x"}, {**GOOD_ROW, "code": "IS 7777"}]
    summary = bis_snapshot.import_snapshot(rows)
    assert summary["accepted"] == 1
    assert summary["rejected"] == 2
    assert summary["rejects"][0]["line"] == 3  # row 2 (header is line 1)
    assert summary["rejects"][0]["reason"] == "missing code"
    assert summary["rejects"][1]["reason"] == "duplicate code within snapshot"


def test_import_snapshot_skips_existing_seed_codes_unless_forced():
    seed_rows = [{"code": "IS 456", "title": "dup", "version": "1990",
                  "status": "active", "sector": "construction", "category": "x"}]
    summary = bis_snapshot.import_snapshot(seed_rows, existing_codes={"IS 456"})
    assert summary["accepted"] == 0 and summary["skipped_existing"] == 1

    summary = bis_snapshot.import_snapshot(seed_rows, existing_codes={"IS 456"}, force=True)
    assert summary["accepted"] == 1
    assert summary["records"][0]["force"] is True


def test_template_csv_imports_cleanly():
    rows = bis_snapshot.read_snapshot(
        Path(catalog.__file__).parent / "snapshots" / "template.csv")
    summary = bis_snapshot.import_snapshot(rows, existing_codes=set())
    assert summary["accepted"] == 2
    assert summary["rejected"] == 0


# ----------------------------------------------------------------------- merge
def test_merge_extends_catalogue_and_respects_force(monkeypatch):
    payload = {
        "imported_on": "2026-09-29",
        "records": [
            {"code": "IS 8888", "title": "Merged snapshot entry", "version": "2024",
             "status": "active", "sector": "water", "category": "Merged",
             "provenance": "snapshot"},
            {"code": "IS 456", "title": "Forced snapshot override", "version": "2024",
             "status": "active", "sector": "construction", "category": "Merged",
             "provenance": "snapshot", "force": True},
            {"code": "IS 456", "title": "Non-forced should not shadow", "version": "2001",
             "status": "active", "sector": "construction", "category": "Merged",
             "provenance": "snapshot"},
        ],
    }
    monkeypatch.setattr(catalog, "_load_generated_payload", lambda: payload)
    merged = catalog._merge_snapshot_records(catalog._SEED_STANDARDS)
    assert len(merged) == len(catalog._SEED_STANDARDS) + 1
    assert any(s["code"] == "IS 8888" for s in merged)
    forced = next(s for s in merged if s["code"] == "IS 456")
    assert forced["title"] == "Forced snapshot override"
    assert forced["aliases"]  # seed fields survive the forced override


def test_merge_with_no_payload_is_identity(monkeypatch):
    monkeypatch.setattr(catalog, "_load_generated_payload", lambda: {})
    assert catalog._merge_snapshot_records(catalog._SEED_STANDARDS) == catalog._SEED_STANDARDS


def test_sync_health_reflects_empty_snapshot():
    assert catalog.SYNC_HEALTH["mode"] in {"seed", "seed+snapshot"}
    assert "snapshot_records" in catalog.SYNC_HEALTH


# -------------------------------------------------------------------------- CLI
def test_cli_end_to_end(tmp_path, capsys):
    csv_path = _write_csv(tmp_path, [GOOD_ROW])
    out_path = tmp_path / "out" / "bis_catalog.json"
    rc = bis_snapshot.main(["--input", str(csv_path), "--output", str(out_path)])
    assert rc == 0
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["count"] == 1
    assert payload["records"][0]["provenance"] == "snapshot"


def test_cli_fails_when_all_rows_rejected(tmp_path):
    csv_path = _write_csv(tmp_path, [{"code": "BOGUS", "title": "x"}])
    assert bis_snapshot.main(["--input", str(csv_path),
                              "--output", str(tmp_path / "o.json")]) == 1


# --------------------------------------------------- runtime + health surfacing
def test_health_reports_snapshot_merge(client):
    data = client.get("/api/health").json()
    assert data["sync"]["mode"] in {"seed", "seed+snapshot"}
    assert isinstance(data["sync"].get("snapshot_records"), int)
