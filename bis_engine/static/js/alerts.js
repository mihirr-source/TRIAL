/* Compliance Alerts page logic */
"use strict";
(function () {
  fetchJSON("/api/certifications").then(data => {
    const el = $("#schemes");
    if (!data.schemes.length) {
      el.innerHTML = `<div class="alert-banner warn">No certification schemes recorded in the catalogue.</div>`;
      return;
    }
    el.innerHTML = `<p class="muted small">${data.count} scheme(s) mapped in the seed catalogue.</p>` +
      data.schemes.map(s => `
        <div class="card">
          <h2 style="margin-top:0">⚠ ${escapeHtml(s.scheme)}</h2>
          <p class="small muted">Administered by: <strong>${escapeHtml(s.authority)}</strong></p>
          <p>${escapeHtml(s.note)}</p>
          <p><strong>Applies to:</strong> ${s.standards.map(c =>
            `<a class="pill version" href="/standards/${encodeURIComponent(c)}">${escapeHtml(c)}</a>`).join(" ")}</p>
        </div>`).join("");
  }).catch(err => {
    $("#schemes").innerHTML = `<div class="alert-banner fail">Could not load alerts: ${escapeHtml(err.message)}</div>`;
  });
})();
