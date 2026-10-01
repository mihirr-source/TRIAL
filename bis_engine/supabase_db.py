"""
Supabase REST API client for persistent tenders & bids storage.
Replaces the ephemeral SQLite approach that breaks on Vercel serverless.
"""
import json
import urllib.request
import urllib.error
import urllib.parse
from typing import Any

SUPABASE_URL = "https://aczptmsfeueejysaajod.supabase.co"
SUPABASE_KEY = "sb_publishable_MB41QV4o2-yrVWvfIwvPeA_-VV7_YRJ"
REST_BASE = f"{SUPABASE_URL}/rest/v1"


def _req(method: str, path: str, data: Any = None) -> Any:
    """Execute a Supabase REST request."""
    url = f"{REST_BASE}/{path}"
    body = json.dumps(data).encode("utf-8") if data is not None else None
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw.strip() else []
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8")
        raise Exception(f"Supabase {e.code}: {err}")
    except Exception as exc:
        raise Exception(f"Supabase request failed: {exc}")


# ── Tenders ─────────────────────────────────────────────────────────────────

def create_tender(title: str, description: str, customer_email: str) -> dict:
    rows = _req("POST", "tenders", {
        "title": title,
        "description": description,
        "customer_email": customer_email,
    })
    return rows[0] if isinstance(rows, list) and rows else {}


def get_all_tenders() -> list:
    return _req("GET", "tenders?order=id.desc") or []


def get_tenders_by_customer(email: str) -> list:
    enc = urllib.parse.quote(email, safe="")
    return _req("GET", f"tenders?customer_email=eq.{enc}&order=id.desc") or []


# ── Bids ─────────────────────────────────────────────────────────────────────

def create_bid(
    tender_id: int,
    vendor_email: str,
    vendor_name: str,
    spec_text: str,
    score: int,
    report_json: str,
) -> dict:
    rows = _req("POST", "bids", {
        "tender_id": tender_id,
        "vendor_email": vendor_email,
        "vendor_name": vendor_name,
        "spec_text": spec_text,
        "compliance_score": score,
        "compliance_report": report_json,
    })
    return rows[0] if isinstance(rows, list) and rows else {}


def get_bids_for_tender(tender_id: int) -> list:
    return _req("GET", f"bids?tender_id=eq.{tender_id}&order=compliance_score.desc") or []


def get_bids_by_vendor(vendor_email: str) -> list:
    enc = urllib.parse.quote(vendor_email, safe="")
    return _req("GET", f"bids?vendor_email=eq.{enc}&order=id.desc") or []


def has_bid(tender_id: int, vendor_email: str) -> bool:
    enc = urllib.parse.quote(vendor_email, safe="")
    rows = _req("GET", f"bids?tender_id=eq.{tender_id}&vendor_email=eq.{enc}&select=id") or []
    return len(rows) > 0


def get_vendor_vault(vendor_email: str) -> list:
    """Return vendor's submitted bids with joined tender info."""
    enc = urllib.parse.quote(vendor_email, safe="")
    # PostgREST embedded resource syntax - uses FK relationship
    rows = _req(
        "GET",
        f"bids?vendor_email=eq.{enc}&order=id.desc&select=*,tenders(id,title,description)"
    ) or []
    result = []
    for row in rows:
        item = dict(row)
        nested = item.pop("tenders", {}) or {}
        item["tender_title"] = nested.get("title", "Unknown Tender")
        item["tender_description"] = nested.get("description", "")
        result.append(item)
    return result


# ── Demo seed ────────────────────────────────────────────────────────────────

def seed_demo_if_needed(customer_email: str, demo_data: list) -> None:
    """Insert demo tenders+bids once per customer email. Safe to call repeatedly."""
    try:
        existing = get_tenders_by_customer(customer_email)
        if existing:
            return  # Already seeded for this email
        for item in demo_data:
            t_args = item["tender"]
            tender = create_tender(t_args[0], t_args[1], t_args[2])
            tid = tender.get("id")
            if not tid:
                continue
            b = item["bid"]
            create_bid(tid, b[0], b[1], b[2], b[3], b[4])
    except Exception as e:
        # Log but don't crash — the page still works without demo data
        print(f"[supabase_db] seed_demo_if_needed error: {e}")
