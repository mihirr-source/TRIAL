/* Home page: hybrid search with live results */
"use strict";
(function () {
  const form = $("#search-form"), input = $("#q"), results = $("#results");
  const statsEl = $("#stats"), chips = $("#chips");

  function renderResults(data) {
    if (!data.primary) {
      results.innerHTML = `<div class="alert-banner warn animate-fade-in">No confident match for
        “${escapeHtml(data.query)}”. Try a product word like <em>cable, pipe, helmet, AC, cement, LED</em>.</div>`;
      results.scrollIntoView({ behavior: "smooth", block: "nearest" });
      return;
    }
    const p = data.primary;
    let html = `
      <div class="section-header scroll-reveal is-visible" style="margin-top:2rem;">
        <h2 class="section-title">Recommended Standards for “${escapeHtml(data.query)}”</h2>
        <div class="section-accent-line"></div>
        <p class="section-subtitle">Primary match identified by semantic mapping and BIS classification index.</p>
      </div>`;

    html += `<div class="animate-fade-in" style="animation-delay: 60ms">${renderStandardCard(p.standard, { confidence: p.score })}</div>`;
    html += `<div class="card card-hover animate-fade-in" style="animation-delay: 120ms"><h3 style="margin-top:0; font-weight:700; color:var(--text-main);">Bundle these allied standards with the primary</h3>
      ${alliedList(p.standard.allied)}</div>`;

    const certs = p.standard.certifications || [];
    html += certs.length
      ? `<div class="card card-hover animate-fade-in" style="animation-delay: 180ms"><h3 style="margin-top:0; font-weight:700; color:var(--text-main);">Mandatory certification checks</h3>${certs.map(certAlert).join("")}</div>`
      : "";

    if (data.alternatives.length) {
      html += `<div class="section-header scroll-reveal is-visible" style="margin-top:2.5rem;"><h3 class="section-title" style="font-size:1.3rem;">Other Alternative Matches</h3><div class="section-accent-line"></div></div>` +
        data.alternatives.map((a, idx) => `<div class="animate-fade-in" style="animation-delay: ${300 + idx * 60}ms">${renderStandardCard(a.standard, { confidence: a.score })}</div>`).join("");
    }
    results.innerHTML = html;
    results.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  async function doSearch(q) {
    setStatus(results, "loading", t("status.searching"));
    results.innerHTML = `
      <div class="skeleton-card animate-fade-in">
        <div class="skeleton-line title"></div>
        <div class="skeleton-line subtitle"></div>
        <div class="skeleton-line short"></div>
      </div>
      <div class="skeleton-card animate-fade-in" style="animation-delay: 80ms">
        <div class="skeleton-line title"></div>
        <div class="skeleton-line subtitle"></div>
      </div>`;
    try {
      const data = await fetchJSON(`/api/search?q=${encodeURIComponent(q)}&top_k=6`);
      renderResults(data);
      history.replaceState(null, "", `?q=${encodeURIComponent(q)}`);
    } catch (err) {
      setStatus(results, "error", `Search failed: ${err.message}`);
    }
  }

  if (form) {
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      if (input.value.trim().length >= 2) doSearch(input.value.trim());
    });
  }

  if (chips) {
    chips.addEventListener("click", (e) => {
      const chip = e.target.closest(".chip");
      if (chip) { 
        input.value = chip.textContent.trim(); 
        doSearch(chip.textContent.trim()); 
      }
    });
  }

  const q = new URLSearchParams(location.search).get("q");
  if (q && input) { input.value = q; doSearch(q); }

  if (statsEl) {
    fetchJSON("/api/health").then(h => {
      statsEl.textContent = `${h.stats.catalogue_size} standards · ${h.stats.alias_count} search aliases · catalogue ${h.catalog_version}`;
    }).catch(() => { statsEl.textContent = "API offline"; });
  }
})();
