/* Tender Analyzer page logic */
"use strict";
(function () {
  const btn = $("#analyze-btn"), spec = $("#spec"), report = $("#report"), statusEl = $("#status");

  const SAMPLE = `Supply and installation of room air conditioners for the new office block.
Units shall be window type, 1.5 ton capacity, with copper condenser. All units must be
energy efficient. TMT bars Fe 500 shall be used for the plinth as per IS 1786:2008.
Concrete work generally as per IS 456:1978. Supply of packaged drinking water in 20 L
jars for staff. Electrical items like sockets and plugs should conform to applicable
BIS standards. Fire extinguishers shall be provided on each floor.`;

  $("#demo-btn").addEventListener("click", () => { spec.value = SAMPLE; });

  const ICONS = { pass: "✓", warn: "▲", fail: "✗" };

  function checkRow(c) {
    return `<div class="check-row">
      <span class="status-${c.status}" aria-hidden="true">${ICONS[c.status] || "•"}</span>
      <span><strong class="status-${c.status}">${c.status.toUpperCase()}</strong>
      <span class="small muted">${escapeHtml(c.check)}</span> — ${escapeHtml(c.detail)}</span>
    </div>`;
  }

  function renderReport(r) {
    const m = r.meta;
    let html = `
      <div class="card">
        <h2 style="margin-top:0">Specification health check</h2>
        ${r.checks.map(checkRow).join("")}
        <p class="small muted" style="margin-bottom:0">
          Detected language: <strong>${escapeHtml(m.detected_language_label)}</strong> ·
          ${escapeHtml(m.sync.source_note)}
        </p>
      </div>`;

    if (r.primaries.length) {
      html += `<h2>Relevant standards identified</h2>` +
        r.primaries.map(p => renderStandardCard(p, { confidence: p.confidence })).join("");
    } else {
      html += `<div class="alert-banner fail"><strong>No standards could be matched.</strong>
        Rephrase with product words (e.g. "cables", "pipes", "helmets").</div>`;
    }

    if (r.allied_missing.length) {
      html += `<div class="card"><h2 style="margin-top:0">⚠ Missing allied / normative standards</h2>
        <p class="small muted">These are cross-referenced by the standards above but never appear in your text.</p>
        <table><thead><tr><th>Code</th><th>Title</th><th>Required by</th><th>Relation</th></tr></thead>
        <tbody>${r.allied_missing.map(a => `
          <tr><td><a href="/standards/${encodeURIComponent(a.code)}">${escapeHtml(a.code)}</a></td>
          <td>${escapeHtml(a.title)}</td>
          <td>${escapeHtml(a.required_by)}</td>
          <td class="small muted">${escapeHtml(a.relation)}</td></tr>`).join("")}
        </tbody></table></div>`;
    }

    if (r.certifications.length) {
      html += `<div class="card"><h2 style="margin-top:0">Mandatory certification requirements</h2>` +
        r.certifications.map(certAlert).join("") + `</div>`;
    }

    if (r.obsolete_flags.length) {
      html += `<div class="card"><h2 style="margin-top:0">✗ Outdated / unverified references</h2>` +
        r.obsolete_flags.map(f => `
          <div class="alert-banner fail">
            <strong>${escapeHtml(f.code)}</strong> — ${escapeHtml(f.reason)}
            ${f.bad ? `<div class="small">Found: ${escapeHtml(f.bad)} → Use: <strong>${escapeHtml(f.good)}</strong></div>` : ""}
          </div>`).join("") + `</div>`;
    }

    html += `<p class="small muted no-print">${escapeHtml(m.disclaimer)}
      <button class="btn secondary no-print" onclick="window.print()" style="margin-left:.5rem">Print report</button></p>`;

    report.innerHTML = html;
  }

  btn.addEventListener("click", async () => {
    const text = spec.value.trim();
    if (text.length < 10) { setStatus(statusEl, "error", "Please enter at least 10 characters."); return; }
    if (text.length > 20000) { setStatus(statusEl, "error", "Text exceeds 20,000 characters."); return; }
    btn.disabled = true;
    setStatus(statusEl, "loading", "Analyzing…");
    report.innerHTML = `<div class="spinner" role="status" aria-label="Analyzing"></div>`;
    try {
      const r = await fetchJSON("/api/analyze", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      setStatus(statusEl, "ok", "Analysis complete.");
      renderReport(r);
    } catch (err) {
      setStatus(statusEl, "error", `Analysis failed: ${err.message}`);
      report.innerHTML = "";
    } finally {
      btn.disabled = false;
    }
  });
})();
