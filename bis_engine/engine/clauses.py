"""Specification-ready outputs: draft tender clauses + Markdown report export.

`build_spec_clauses` turns an analyzer report into copy-paste-ready clauses:
correct code + latest known version + amendments, the allied standards that
must be cited alongside, and the certification sentence where applicable.
`report_to_markdown` renders the whole report as a downloadable Markdown file.

These are drafts for the official to verify and adapt — never a compliance
guarantee (the engine's standing disclaimer applies).
"""

from __future__ import annotations


def _version_phrase(version: str, amendments: list[str]) -> str:
    if not version:
        return ""
    phrase = version
    if amendments:
        phrase += " (with amendments: " + "; ".join(amendments) + ")"
    return phrase


def _clause_for_primary(p: dict) -> dict:
    allied = p.get("allied", []) or []
    include_allied = [
        {"code": a["code"], "title": a.get("relation", ""),
         "title_resolved": _title_of(a["code"]) or a.get("relation", ""),
         "was_missing": None}
        for a in allied
    ]
    missing_lookup = {m["code"]: m for m in p.get("_missing_allied", [])}
    for item in include_allied:
        m = missing_lookup.get(item["code"])
        item["was_missing"] = (m is not None) if missing_lookup else None
        if m:
            item["title_resolved"] = m.get("title") or item["title_resolved"]

    parts = [
        f"All supplies under this item shall conform to {p['code']}"
        + (f" — {p['title']}" if p.get("title") else "")
    ]
    vp = _version_phrase(p.get("version", ""), p.get("amendments", []))
    if vp:
        parts.append(f"in its current edition ({vp})")
    clause = parts[0] + " " + (parts[1] if len(parts) > 1 else "") + "."

    if include_allied:
        refs = "; ".join(f"{a['code']} ({a['title_resolved']})" for a in include_allied)
        clause += f" Associated requirements shall also conform to: {refs}."

    cert = (p.get("certifications") or [None])[0]
    if cert:
        clause += (f" Supplies shall carry a valid {cert['scheme']} "
                   f"({cert['authority']}) as applicable.")

    return {
        "code": p["code"],
        "title": p.get("title", ""),
        "version": p.get("version", ""),
        "amendments": p.get("amendments", []),
        "clause_text": " ".join(clause.split()),
        "include_allied": include_allied,
        "certification": cert,
    }


def _title_of(code: str) -> str | None:
    try:
        from bis_engine.data.catalog import get_by_code
        std = get_by_code(code)
        return std["title"] if std else None
    except Exception:
        return None


def build_spec_clauses(report: dict) -> dict:
    """Build per-primary-standard clauses from an analyzer report."""
    primaries = report.get("primaries", [])
    # Attach the analyzer's missing-allied table so clauses can mark gaps.
    missing_by_primary: dict[str, list[dict]] = {}
    for m in report.get("allied_missing", []):
        missing_by_primary.setdefault(m.get("required_by", ""), []).append(m)

    clauses = []
    for p in primaries:
        p = {**p, "_missing_allied": missing_by_primary.get(p["code"], [])}
        clauses.append(_clause_for_primary(p))
    return {
        "disclaimer": report.get("meta", {}).get(
            "disclaimer", "Verify every clause against the official BIS catalogue."),
        "clause_count": len(clauses),
        "clauses": clauses,
    }


# ------------------------------------------------------------------ markdown
def report_to_markdown(report: dict) -> str:
    """Render an analyzer report as a Markdown tender-review document."""
    meta = report.get("meta", {})
    lines: list[str] = [
        "# Specification health report",
        "",
        f"*Detected language: {meta.get('detected_language_label', '—')} · "
        f"{meta.get('sync', {}).get('source_note', '')}*",
        "",
    ]

    checks = report.get("checks", [])
    if checks:
        lines += ["## Summary", ""]
        for c in checks:
            lines.append(f"- **{c['status'].upper()}** — {c['check']}: {c['detail']}")
        lines.append("")

    primaries = report.get("primaries", [])
    if primaries:
        lines += ["## Relevant standards identified", ""]
        for p in primaries:
            lines.append(f"### {p['code']} — {p['title']}")
            vp = _version_phrase(p.get("version", ""), p.get("amendments", []))
            if vp:
                lines.append(f"- **Version:** {vp}")
            if p.get("summary"):
                lines.append(f"- {p['summary']}")
            if p.get("certifications"):
                for cert in p["certifications"]:
                    lines.append(f"- **Certification:** {cert['scheme']} "
                                 f"({cert['authority']}) — {cert['note']}")
            lines.append("")

    missing = report.get("allied_missing", [])
    if missing:
        lines += ["## Missing allied / normative standards", "",
                  "| Code | Title | Required by | Relation |",
                  "| --- | --- | --- | --- |"]
        for a in missing:
            lines.append(f"| {a['code']} | {a.get('title', '')} | "
                         f"{a.get('required_by', '')} | {a.get('relation', '')} |")
        lines.append("")

    certs: dict[str, dict] = {}
    for p in primaries:
        for cert in p.get("certifications", []):
            certs.setdefault(cert["scheme"], cert)
    for c in report.get("certifications", []):
        certs.setdefault(c["scheme"], c)
    if certs:
        lines += ["## Mandatory certification requirements", ""]
        for cert in certs.values():
            lines.append(f"- **{cert['scheme']}** ({cert['authority']}) — {cert['note']}")
        lines.append("")

    flags = report.get("obsolete_flags", [])
    if flags:
        lines += ["## Outdated / unverified references", ""]
        for f in flags:
            line = f"- **{f['code']}** — {f.get('reason', '')}"
            if f.get("bad"):
                line += f" Found: `{f['bad']}` → Use: **{f['good']}**"
            lines.append(line)
        lines.append("")

    lines += ["---", "",
              f"> {meta.get('disclaimer', 'Decision support only — verify against the official BIS catalogue.')}"]
    return "\n".join(lines) + "\n"
