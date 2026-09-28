/* Standard detail page logic */
"use strict";
(function () {
  const detail = $("#detail");
  const code = decodeURIComponent(location.pathname.split("/").pop() || "");

  fetchJSON(`/api/standards/${encodeURIComponent(code)}`).then(std => {
    document.title = `${std.code} — BIS Standards Assistant`;
    const sectorName = std.sector ? (std.sector.charAt(0).toUpperCase() + std.sector.slice(1)) : "—";
    const aliasList = Object.entries(std.aliases || {})
      .map(([lang, words]) => `<li><strong>${escapeHtml(lang)}:</strong> ${words.map(escapeHtml).join(", ")}</li>`)
      .join("");

    detail.innerHTML = `
      <h1 style="margin-bottom:.2rem">${escapeHtml(std.code)}</h1>
      <p class="muted" style="margin-top:0">${escapeHtml(std.title)}</p>
      <div style="margin:.6rem 0">${statusPill(std)} ${versionPill(std)}</div>
      <div class="card">
        <h2 style="margin-top:0">Summary</h2>
        <p>${escapeHtml(std.summary || "")}</p>
        <p class="small muted">Sector: ${escapeHtml(sectorName)} · Category: ${escapeHtml(std.category || "—")}
          · Last reviewed in seed data: ${escapeHtml(std.last_reviewed || "—")}</p>
      </div>
      ${std.amendments && std.amendments.length
        ? `<div class="card"><h2 style="margin-top:0">Amendments on record</h2><ul>${std.amendments.map(a => `<li>${escapeHtml(a)}</li>`).join("")}</ul></div>`
        : ""}
      ${certAlertsHTML(std)}
      <div class="card"><h2 style="margin-top:0">Allied & normative standards</h2>${alliedList(std.allied)}</div>
      ${aliasList ? `<div class="card"><h2 style="margin-top:0">Search aliases (multilingual)</h2><ul class="small">${aliasList}</ul></div>` : ""}
      ${examplesHTML(std)}
      <div class="alert-banner warn small">Demo seed data — confirm the current edition, amendments and
        certification scope in the official BIS catalogue before citing this standard in a tender.</div>`;
  }).catch(err => {
    detail.innerHTML = `<div class="alert-banner fail">${escapeHtml(err.message)}
      <br><a href="/standards">Browse the catalogue</a> or use search.</div>`;
  });

  function certAlertsHTML(std) {
    const certs = std.certifications || [];
    return certs.length
      ? `<div class="card"><h2 style="margin-top:0">Mandatory certification requirements</h2>${certs.map(certAlert).join("")}</div>`
      : "";
  }
  function examplesHTML(std) {
    const ex = std.examples || [];
    return ex.length
      ? `<div class="card"><h2 style="margin-top:0">Specification pitfalls</h2>${ex.map(e => `
          <div class="alert-banner warn"><strong>✗ ${escapeHtml(e.bad)}</strong> →
          <strong>✓ ${escapeHtml(e.good)}</strong><div class="small muted">${escapeHtml(e.note)}</div></div>`).join("")}</div>`
      : "";
  }
})();
