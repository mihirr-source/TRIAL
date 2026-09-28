/* Explore Standards page logic */
"use strict";
(function () {
  const list = $("#standards-list"), chipBar = $("#sector-chips");
  let all = [], sectors = {}, activeSector = null;
  let filterBox = null;

  function render() {
    const term = filterBox ? filterBox.value.trim().toLowerCase() : "";
    const items = all.filter(s =>
      (!activeSector || s.sector === activeSector) &&
      (!term || (s.code + " " + s.title + " " + (s.summary || "")).toLowerCase().includes(term)));
    if (!items.length) {
      list.innerHTML = `<div class="alert-banner warn">No standards match this filter.</div>`;
      return;
    }
    list.innerHTML = items.map(s => renderStandardCard(s)).join("");
  }

  function renderChips() {
    chipBar.innerHTML = `<button class="chip" data-sector="">All sectors</button>` +
      Object.entries(sectors).map(([k, label]) =>
        `<button class="chip" data-sector="${k}">${escapeHtml(label)}</button>`).join("");
  }

  chipBar.addEventListener("click", (e) => {
    const chip = e.target.closest(".chip");
    if (!chip) return;
    activeSector = chip.dataset.sector || null;
    $$(".chip", chipBar).forEach(c => {
      c.style.background = c === chip ? "#0b3a5d" : "";
      c.style.color = c === chip ? "#f4a300" : "";
    });
    render();
  });

  fetchJSON("/api/standards").then(data => {
    all = data.standards;
    sectors = data.sectors;
    renderChips();
    filterBox = document.createElement("input");
    filterBox.type = "search";
    filterBox.placeholder = "Filter by code or title…";
    filterBox.className = "spec-input";
    filterBox.style.minHeight = "0";
    filterBox.style.marginBottom = "1rem";
    filterBox.style.width = "320px";
    filterBox.setAttribute("aria-label", "Filter standards");
    filterBox.addEventListener("input", render);
    list.before(filterBox);
    render();
  }).catch(err => {
    list.innerHTML = `<div class="alert-banner fail">Could not load standards: ${escapeHtml(err.message)}</div>`;
  });
})();
