/* Tender Analyzer page logic: text + file intake, report rendering with
 * copy-as-specification panel and report exports. */
"use strict";
(function () {
  const btn = $("#analyze-btn"), spec = $("#spec"), report = $("#report"), statusEl = $("#status");
  const fileBtn = $("#file-btn"), fileInput = $("#file-input");

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

  function renderReport(r, sourceFile) {
    const m = r.meta;
    let html = `
      <div class="card">
        <h2 style="margin-top:0">${t("report.health")}</h2>
        ${r.checks.map(checkRow).join("")}
        <p class="small muted" style="margin-bottom:0">
          ${t("report.detected")} <strong>${escapeHtml(m.detected_language_label)}</strong>
          ${sourceFile ? ` · 📄 ${escapeHtml(sourceFile)}` : ""} ·
          ${escapeHtml(m.sync.source_note)}
        </p>
      </div>`;

    if (r.primaries.length) {
      html += `<h2>${t("report.primaries")}</h2>` +
        r.primaries.map(p => renderStandardCard(p, { confidence: p.confidence })).join("");
    } else {
      html += `<div class="alert-banner fail"><strong>${t("report.none")}</strong></div>`;
    }

    if (r.allied_missing.length) {
      html += `<div class="card"><h2 style="margin-top:0">${t("report.allied")}</h2>
        <p class="small muted">${t("report.allied.note")}</p>
        <table><thead><tr>
          <th>${t("report.th.code")}</th><th>${t("report.th.title")}</th>
          <th>${t("report.th.reqby")}</th><th>${t("report.th.relation")}</th></tr></thead>
        <tbody>${r.allied_missing.map(a => `
          <tr><td><a href="/standards/${encodeURIComponent(a.code)}">${escapeHtml(a.code)}</a></td>
          <td>${escapeHtml(a.title)}</td>
          <td>${escapeHtml(a.required_by)}</td>
          <td class="small muted">${escapeHtml(a.relation)}</td></tr>`).join("")}
        </tbody></table></div>`;
    } else if (r.primaries.length) {
      html += `<div class="card"><p class="muted small" style="margin:0">${t("report.noallied")}</p></div>`;
    }

    if (r.certifications.length) {
      html += `<div class="card"><h2 style="margin-top:0">${t("report.certs")}</h2>` +
        r.certifications.map(certAlert).join("") + `</div>`;
    }

    if (r.obsolete_flags.length) {
      html += `<div class="card"><h2 style="margin-top:0">${t("report.obsolete")}</h2>` +
        r.obsolete_flags.map(f => `
          <div class="alert-banner fail">
            <strong>${escapeHtml(f.code)}</strong> — ${escapeHtml(f.reason)}
            ${f.bad ? `<div class="small">Found: ${escapeHtml(f.bad)} → Use: <strong>${escapeHtml(f.good)}</strong></div>` : ""}
          </div>`).join("") + `</div>`;
    }

    if (r.primaries.length) {
      html += `
      <div class="card no-print" id="spec-output">
        <h2 style="margin-top:0">${t("report.copy")}</h2>
        <div id="clauses"></div>
        <div style="margin-top:.6rem;display:flex;gap:.5rem;flex-wrap:wrap">
          <button class="btn secondary" id="copy-btn" type="button">${t("report.copy")}</button>
          <a class="btn secondary" id="export-md" href="#">${t("report.export.md")}</a>
          <a class="btn secondary" id="export-json" href="#">${t("report.export.json")}</a>
          <button class="btn secondary" onclick="window.print()" type="button">${t("report.print")}</button>
        </div>
      </div>`;
      loadClauses(r.primaries);
    }

    report.innerHTML = html;

    if (r.primaries.length) {
      $("#copy-btn").addEventListener("click", copyClauses);
      wireExports(r.primaries);
    }
  }

  let lastPrimaries = [];

  async function loadClauses(primaries) {
    lastPrimaries = primaries;
    try {
      const data = await fetchJSON("/api/spec-clauses", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: spec.value.trim() }),
      });
      const box = $("#clauses");
      if (!box) return;
      box.innerHTML = data.clauses.map(c => `
        <div class="clause-item">
          <strong>${escapeHtml(c.code)}</strong>
          <p class="small" style="margin:.2rem 0 .4rem">${escapeHtml(c.clause_text)}</p>
        </div>`).join("");
    } catch {
      const box = $("#clauses");
      if (box) box.innerHTML = `<p class="muted small">Clause generation unavailable.</p>`;
    }
  }

  function copyClauses() {
    const box = $("#clauses");
    const text = box ? Array.from(box.querySelectorAll(".clause-item"))
      .map(el => el.querySelector("p").textContent).join("\n\n") : "";
    navigator.clipboard.writeText(text).then(() => {
      const btnEl = $("#copy-btn");
      const old = btnEl.textContent;
      btnEl.textContent = t("report.copied");
      setTimeout(() => { btnEl.textContent = old; }, 1500);
    });
  }

  function wireExports(primaries) {
    const q = spec.value.trim();
    const md = $("#export-md"), js = $("#export-json");
    if (md) { md.href = "#"; md.onclick = (e) => { e.preventDefault(); exportReport("markdown"); }; }
    if (js) { js.href = "#"; js.onclick = (e) => { e.preventDefault(); exportReport("json"); }; }
  }

  async function exportReport(fmt) {
    try {
      const res = await fetch("/api/analyze/export?format=" + fmt, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: spec.value.trim() }),
      });
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      if (fmt === "json") {
        const blob = new Blob([JSON.stringify(await res.json(), null, 2)],
                              { type: "application/json" });
        triggerDownload(blob, "specification-report.json");
      } else {
        triggerDownload(await res.blob(), "specification-report.md");
      }
    } catch (err) {
      setStatus(statusEl, "error", `Export failed: ${err.message}`);
    }
  }

  function triggerDownload(blob, filename) {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(a.href);
  }

  async function analyzeText(text) {
    setStatus(statusEl, "loading", t("status.analyzing"));
    report.innerHTML = `<div class="spinner" role="status" aria-label="Analyzing"></div>`;
    try {
      const r = await fetchJSON("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      setStatus(statusEl, "ok", "");
      renderReport(r, null);
    } catch (err) {
      report.innerHTML = "";
      setStatus(statusEl, "error", err.message);
    }
  }

  async function analyzeFile(file) {
    setStatus(statusEl, "loading", t("status.uploading"));
    report.innerHTML = `<div class="spinner" role="status" aria-label="Analyzing"></div>`;
    try {
      const fd = new FormData();
      fd.append("file", file);
      const res = await fetch("/api/analyze/file", { method: "POST", body: fd });
      const body = await res.json();
      if (!res.ok) throw new Error(body.detail || `${res.status} ${res.statusText}`);
      setStatus(statusEl, "ok", "");
      renderReport(body, file.name);
    } catch (err) {
      report.innerHTML = "";
      setStatus(statusEl, "error", err.message);
    }
  }

  btn.addEventListener("click", () => {
    const text = spec.value.trim();
    if (text.length < 10) { setStatus(statusEl, "error", t("status.tooshort")); return; }
    if (text.length > 20000) { setStatus(statusEl, "error", t("status.toolong")); return; }
    analyzeText(text);
  });

  fileBtn.addEventListener("click", () => fileInput.click());
  fileInput.addEventListener("change", () => {
    if (fileInput.files && fileInput.files[0]) {
      analyzeFile(fileInput.files[0]);
      fileInput.value = "";
    }
  });

  // Drag & drop onto the whole input card.
  const zone = $("#upload-zone").closest(".card");
  ["dragover", "dragenter"].forEach(ev =>
    zone.addEventListener(ev, (e) => { e.preventDefault(); zone.classList.add("drag"); }));
  ["dragleave", "drop"].forEach(ev =>
    zone.addEventListener(ev, (e) => { e.preventDefault(); zone.classList.remove("drag"); }));
  zone.addEventListener("drop", (e) => {
    const f = e.dataTransfer.files && e.dataTransfer.files[0];
    if (f) analyzeFile(f);
  });

  // Re-render dynamic strings on language switch.
  document.addEventListener("bis:langchange", () => {
    if (lastPrimaries.length) renderReportFromPrimaries();
  });

  function renderReportFromPrimaries() {
    // Lightweight refresh: re-fetch with the stored text so the report stays current.
    if (spec.value.trim().length >= 10) analyzeText(spec.value.trim());
  }
})();
