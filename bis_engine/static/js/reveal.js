/* =====================================================================
   PARAKH Standards Recommendation Engine — Scroll Reveals & Command Palette
   ===================================================================== */
"use strict";

(function () {
  // 1. Scroll-triggered Staggered Reveals
  function initScrollReveals() {
    const reveals = document.querySelectorAll(".reveal-on-scroll");
    if (!reveals.length) return;

    if ("IntersectionObserver" in window) {
      const observer = new IntersectionObserver((entries, obs) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-revealed");
            obs.unobserve(entry.target);
          }
        });
      }, {
        threshold: 0.1,
        rootMargin: "0px 0px -40px 0px"
      });

      reveals.forEach(el => observer.observe(el));
    } else {
      reveals.forEach(el => el.classList.add("is-revealed"));
    }
  }

  // 2. Command Palette Modal (Cmd+K / Ctrl+K / Search Icon)
  function initCommandPalette() {
    const palette = document.getElementById("cmd-palette-modal");
    const input = document.getElementById("cmd-palette-input");
    const resultsContainer = document.getElementById("cmd-palette-results");
    const closeBtn = document.getElementById("cmd-palette-close");
    const openBtns = document.querySelectorAll(".btn-cmd-palette-trigger");

    if (!palette) return;

    function openPalette() {
      palette.classList.add("open");
      palette.setAttribute("aria-hidden", "false");
      document.body.style.overflow = "hidden";
      if (input) {
        input.value = "";
        setTimeout(() => input.focus(), 50);
      }
    }

    function closePalette() {
      palette.classList.remove("open");
      palette.setAttribute("aria-hidden", "true");
      document.body.style.overflow = "";
    }

    openBtns.forEach(btn => {
      btn.addEventListener("click", (e) => {
        e.preventDefault();
        openPalette();
      });
    });

    if (closeBtn) {
      closeBtn.addEventListener("click", closePalette);
    }

    palette.addEventListener("click", (e) => {
      if (e.target === palette) {
        closePalette();
      }
    });

    // Keyboard Shortcuts: Cmd+K, Ctrl+K, or Slash (/) when not in input
    document.addEventListener("keydown", (e) => {
      if ((e.metaKey || e.ctrlKey) && (e.key === "k" || e.key === "K")) {
        e.preventDefault();
        if (palette.classList.contains("open")) {
          closePalette();
        } else {
          openPalette();
        }
      } else if (e.key === "Escape" && palette.classList.contains("open")) {
        closePalette();
      }
    });

    // Live search inside command palette
    let debounceTimer = null;
    if (input && resultsContainer) {
      input.addEventListener("input", () => {
        clearTimeout(debounceTimer);
        const query = input.value.trim();
        if (query.length < 2) {
          resultsContainer.innerHTML = `
            <div class="cmd-palette-empty">
              <span class="mono-label">TYPE 2+ CHARACTERS TO SEARCH INDIAN STANDARDS</span>
            </div>`;
          return;
        }

        debounceTimer = setTimeout(async () => {
          resultsContainer.innerHTML = `
            <div class="cmd-palette-loading">
              <span class="mono-label">QUERYING STANDARDS CATALOGUE...</span>
            </div>`;

          try {
            const res = await fetch(`/api/search?q=${encodeURIComponent(query)}&limit=6`);
            if (!res.ok) throw new Error("Search failed");
            const data = await res.json();
            const results = data.results || [];

            if (results.length === 0) {
              resultsContainer.innerHTML = `
                <div class="cmd-palette-empty">
                  <span class="mono-label">NO MATCHING STANDARDS FOUND FOR "${query}"</span>
                </div>`;
              return;
            }

            resultsContainer.innerHTML = results.map(item => `
              <a href="/standards/${encodeURIComponent(item.code)}" class="cmd-palette-item">
                <div class="cmd-item-code">
                  <span class="badge-code">${item.code}</span>
                  <span class="badge-sector">${item.sector || 'GENERAL'}</span>
                </div>
                <div class="cmd-item-title">${item.title}</div>
                <div class="cmd-item-arrow">→</div>
              </a>
            `).join("");
          } catch (err) {
            resultsContainer.innerHTML = `
              <div class="cmd-palette-empty">
                <span class="mono-label" style="color:var(--danger)">ERROR SEARCHING CATALOGUE</span>
              </div>`;
          }
        }, 200);
      });
    }
  }

  // 3. Quick Settings / Tools Drawer (Bottom Left Floater)
  function initToolsDrawer() {
    const toggleBtn = document.getElementById("tools-floater-toggle");
    const panel = document.getElementById("tools-floater-panel");
    const closeBtn = document.getElementById("tools-floater-close");

    if (!toggleBtn || !panel) return;

    toggleBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      panel.classList.toggle("open");
    });

    if (closeBtn) {
      closeBtn.addEventListener("click", () => panel.classList.remove("open"));
    }

    document.addEventListener("click", (e) => {
      if (panel.classList.contains("open") && !panel.contains(e.target) && !toggleBtn.contains(e.target)) {
        panel.classList.remove("open");
      }
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    initScrollReveals();
    initCommandPalette();
    initToolsDrawer();
  });
})();
