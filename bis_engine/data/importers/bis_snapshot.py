"""Offline snapshot importer: merge an official/curated BIS catalogue CSV.

The BIS catalogue has no free public API and the full data is licensed, so the
supported production path is an **offline import**: drop a CSV snapshot into
`bis_engine/data/snapshots/` and run this module. It never fetches anything.

CSV template (see `bis_engine/data/snapshots/template.csv`):

    code,title,version,status,sector,category
    IS 9999,Example product specification,2024,active,construction,Example items

Rules:
  * Rows are validated (code format, known sector, non-empty fields); invalid
    rows are collected as rejects and never silently dropped.
  * Seed records remain authoritative: on a code collision the snapshot row is
    skipped (use --force to override the merge-time default).
  * Imported rows carry `provenance: "snapshot"` and only the base fields —
    aliases/allied/certifications stay empty and are enriched by curators later.
  * Output: bis_engine/data/generated/bis_catalog.json (consumed by catalog.py
    at import time) plus a printed summary.

CLI:
    python -m bis_engine.data.importers.bis_snapshot --input <csv> [--force]
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import date
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from bis_engine.data.catalog import SECTORS  # noqa: E402

CODE_RE = re.compile(r"^(IS|IEC)\s*\d{1,5}(\s*\(\s*part\s*\d+\s*\))?$", re.IGNORECASE)
VALID_STATUS = {"active", "superseded-edition", "withdrawn"}

REQUIRED_COLUMNS = ("code", "title", "version", "status", "sector", "category")


# --------------------------------------------------------------------- reading
def read_snapshot(path: str | Path) -> list[dict]:
    """Read the snapshot CSV, returning raw row dicts (str -> str)."""
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        header = [c.strip().lower() for c in (reader.fieldnames or [])]
        missing = [c for c in REQUIRED_COLUMNS if c not in header]
        if missing:
            raise ValueError(f"Snapshot CSV missing columns: {', '.join(missing)}")
        return [{k: (v or "").strip() for k, v in row.items()} for row in reader]


# ------------------------------------------------------------------ validating
def validate_row(row: dict) -> tuple[dict | None, str | None]:
    """Return (record, None) when valid, else (None, reason)."""
    code = re.sub(r"\s+", " ", row.get("code", "")).strip()
    if not code:
        return None, "missing code"
    if not CODE_RE.match(code):
        return None, f"unrecognised code format: '{row.get('code', '')}'"
    if not row.get("title"):
        return None, "missing title"
    if not row.get("version"):
        return None, "missing version"
    status = row.get("status", "").strip().lower() or "active"
    if status not in VALID_STATUS:
        return None, f"unknown status '{row.get('status')}' (use: {', '.join(sorted(VALID_STATUS))})"
    sector = row.get("sector", "").strip().lower()
    if sector not in SECTORS:
        return None, f"unknown sector '{row.get('sector')}'"
    if not row.get("category"):
        return None, "missing category"
    record = {
        "code": code if code.isupper() or not code.startswith("IS") else code.upper(),
        "title": row["title"],
        "version": row["version"],
        "status": status,
        "sector": sector,
        "category": row["category"],
        "provenance": "snapshot",
    }
    return record, None


def _canonical(code: str) -> str:
    return re.sub(r"\s+", " ", code.strip().lower())


def import_snapshot(
    rows: list[dict],
    existing_codes: set[str] | None = None,
    force: bool = False,
) -> dict:
    """Validate + dedupe rows. Returns a summary dict (never raises on rejects)."""
    from bis_engine.data.catalog import normalize_code

    existing_codes = existing_codes if existing_codes is not None else set()
    records: list[dict] = []
    rejects: list[dict] = []
    seen: set[str] = set()
    skipped_existing = 0

    for i, row in enumerate(rows, start=2):  # line 1 is the header
        rec, reason = validate_row(row)
        if rec is None:
            rejects.append({"line": i, "reason": reason, "raw": row})
            continue
        key = normalize_code(rec["code"])
        if key in seen:
            rejects.append({"line": i, "reason": "duplicate code within snapshot", "raw": row})
            continue
        if key in {_canonical(c) for c in existing_codes}:
            if not force:
                skipped_existing += 1
                continue
            rec = {**rec, "force": True}
        seen.add(key)
        records.append(rec)

    return {
        "records": records,
        "rejects": rejects,
        "accepted": len(records),
        "rejected": len(rejects),
        "skipped_existing": skipped_existing,
    }


# --------------------------------------------------------------------- writing
def write_output(records: list[dict], out_path: str | Path) -> Path:
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "imported_on": date.today().isoformat(),
        "count": len(records),
        "records": records,
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import a BIS catalogue snapshot CSV.")
    parser.add_argument("--input", required=True, help="path to the snapshot CSV")
    parser.add_argument("--force", action="store_true",
                        help="allow snapshot rows to shadow seed entries at merge time")
    parser.add_argument("--output", default=None,
                        help="output JSON path (default: bis_engine/data/generated/bis_catalog.json)")
    args = parser.parse_args(argv)

    from bis_engine.data.catalog import STANDARDS

    rows = read_snapshot(args.input)
    summary = import_snapshot(rows, existing_codes={s["code"] for s in STANDARDS},
                              force=args.force)
    if summary["records"]:
        out = write_output(summary["records"], args.output or
                           _ROOT / "bis_engine" / "data" / "generated" / "bis_catalog.json")
        print(f"wrote {out}")
    print(f"accepted={summary['accepted']} rejected={summary['rejected']} "
          f"skipped_existing={summary['skipped_existing']}")
    for rej in summary["rejects"]:
        print(f"  line {rej['line']}: {rej['reason']}")
    return 0 if summary["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
