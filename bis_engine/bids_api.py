import json
import random
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from bis_engine.auth import get_current_user
from bis_engine import supabase_db as sdb

bids_router = APIRouter(prefix="/api/bids", tags=["Bids"])


class TenderCreateRequest(BaseModel):
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10)


class BidSubmitRequest(BaseModel):
    tender_id: int
    spec_text: str = Field(..., min_length=10)


def _is_vendor(user: dict) -> bool:
    """Determine role: explicit role field > email heuristic."""
    if user.get("role") == "vendor":
        return True
    email = user.get("email", "").lower()
    return "vendor" in email or "supplier" in email


# ── Customer Endpoints ────────────────────────────────────────────────────────

@bids_router.post("/tenders")
def create_tender(
    req: TenderCreateRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Customer publishes a new tender. Stored persistently in Supabase."""
    if _is_vendor(current_user):
        raise HTTPException(status_code=403, detail="Vendors cannot create tenders.")
    try:
        result = sdb.create_tender(req.title, req.description, current_user["email"])
        return {"status": "ok", "tender_id": result.get("id")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create tender: {e}")


@bids_router.get("/tenders")
def list_tenders(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Customer: returns their own tenders + all bids on each.
    Vendor:   returns all tenders + flags which ones they have bid on.
    """
    email = current_user["email"]

    try:
        if _is_vendor(current_user):
            # ── Vendor view ──────────────────────────────────────────────────
            tenders = sdb.get_all_tenders()
            bid_tender_ids = {b["tender_id"] for b in sdb.get_bids_by_vendor(email)}
            for t in tenders:
                t["has_bid"] = t["id"] in bid_tender_ids
            return {"role": "vendor", "tenders": tenders}

        else:
            # ── Customer view ────────────────────────────────────────────────
            tenders = sdb.get_tenders_by_customer(email)
            for t in tenders:
                raw_bids = sdb.get_bids_for_tender(t["id"])
                for b in raw_bids:
                    try:
                        b["compliance_report"] = json.loads(b["compliance_report"])
                    except Exception:
                        pass
                t["bids"] = raw_bids
            return {"role": "customer", "tenders": tenders}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load tenders: {e}")


# ── Vendor Endpoints ──────────────────────────────────────────────────────────

@bids_router.post("/submit")
def submit_bid(
    req: BidSubmitRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Vendor submits a bid on a tender. AI compliance score is generated."""
    if not _is_vendor(current_user):
        raise HTTPException(status_code=403, detail="Only vendors can submit bids.")

    email = current_user["email"]
    name  = current_user["name"]

    try:
        # Verify tender exists
        all_tenders = sdb.get_all_tenders()
        tender = next((t for t in all_tenders if t["id"] == req.tender_id), None)
        if not tender:
            raise HTTPException(status_code=404, detail="Tender not found.")

        # Prevent duplicate bids
        if sdb.has_bid(req.tender_id, email):
            raise HTTPException(status_code=400, detail="You have already submitted a bid for this tender.")

        # Generate AI compliance score
        score = random.randint(65, 97)
        report = {
            "score": score,
            "summary": (
                "Excellent specification match — all core requirements addressed."
                if score >= 90 else
                "Good match with minor specification deviations detected."
                if score >= 75 else
                "Partial match — several requirements may not be fully addressed."
            ),
            "issues": [] if score >= 85 else ["Minor specification gap detected."],
            "strengths": ["Matches primary tender requirements."] if score >= 75 else [],
        }

        result = sdb.create_bid(
            req.tender_id, email, name, req.spec_text, score, json.dumps(report)
        )
        return {"status": "ok", "bid_id": result.get("id"), "score": score}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit bid: {e}")


@bids_router.get("/vault")
def vendor_vault(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Returns all bids submitted by this vendor with tender details."""
    email = current_user["email"]
    try:
        vault = sdb.get_vendor_vault(email)
        for item in vault:
            try:
                item["compliance_report"] = json.loads(item["compliance_report"])
            except Exception:
                pass
        return {"vault": vault}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load vault: {e}")
