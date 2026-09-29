/* Home page: hybrid search with live results */
"use strict";
(function () {
  const form = $("#search-form"), input = $("#q"), results = $("#results");
  const statsEl = $("#stats"), chips = $("#chips");

  function renderResults(data) {
    if (!data.primary) {
      results.innerHTML = `<div class="alert-banner warn">No confident match for
        “${escapeHtml(data.query)}”. Try a product word like <em>cable, pipe, helmet, AC</em>.</div>`;
      return;
    }
    const p = data.primary;
    let html = `<h2 style="margin-top:0">Recommended for “${escapeHtml(data.query)}”</h2>`;

    html += renderStandardCard(p.standard, { confidence: p.score });
    html += `<div class="card"><h3 style="margin-top:0">Bundle these allied standards with the primary</h3>
      ${alliedList(p.standard.allied)}</div>`;

    const certs = p.standard.certifications || [];
    html += certs.length
      ? `<div class="card"><h3 style="margin-top:0">Mandatory certification checks</h3>${certs.map(certAlert).join("")}</div>`
      : "";

    if (data.alternatives.length) {
      html += `<h3>Other possible matches</h3>` +
        data.alternatives.map(a => renderStandardCard(a.standard, { confidence: a.score })).join("");
    }
    results.innerHTML = html;
  }

  async function doSearch(q) {
    setStatus(results, "loading", t("status.searching"));
    results.innerHTML = `<div class="spinner" role="status" aria-label="Searching"></div>`;
    try {
      const data = await fetchJSON(`/api/search?q=${encodeURIComponent(q)}&top_k=6`);
      renderResults(data);
      history.replaceState(null, "", `?q=${encodeURIComponent(q)}`);
    } catch (err) {
      setStatus(results, "error", `Search failed: ${err.message}`);
    }
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    if (input.value.trim().length >= 2) doSearch(input.value.trim());
  });
  chips.addEventListener("click", (e) => {
    const chip = e.target.closest(".chip");
    if (chip) { input.value = chip.textContent; doSearch(chip.textContent); }
  });

  const q = new URLSearchParams(location.search).get("q");
  if (q) { input.value = q; doSearch(q); }

  fetchJSON("/api/health").then(h => {
    statsEl.textContent = `${h.stats.catalogue_size} standards · ${h.stats.alias_count} search aliases · catalogue ${h.catalog_version}`;
  }).catch(() => { statsEl.textContent = "API offline"; });
})();
