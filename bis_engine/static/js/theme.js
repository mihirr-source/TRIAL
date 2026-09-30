/* =====================================================================
   PARAKH Standards Recommendation Engine — Theme Controller (theme.js)
   Handles System Preference, User Override, Anti-flash state & UI toggles
   ===================================================================== */
"use strict";

(function () {
  const STORAGE_KEY = "bis_theme";

  function getSystemTheme() {
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  }

  function getSavedTheme() {
    return localStorage.getItem(STORAGE_KEY) || getSystemTheme();
  }

  function applyTheme(theme, animate = false) {
    if (animate) {
      document.documentElement.classList.add("theme-transition");
      setTimeout(() => {
        document.documentElement.classList.remove("theme-transition");
      }, 300);
    }
    document.documentElement.setAttribute("data-theme", theme);
    updateToggleButtons(theme);
    window.dispatchEvent(new CustomEvent("themechanged", { detail: { theme } }));
  }

  function updateToggleButtons(theme) {
    const isDark = theme === "dark";
    document.querySelectorAll(".theme-toggle-btn").forEach((btn) => {
      btn.setAttribute("aria-label", isDark ? "Switch to Light Mode" : "Switch to Dark Mode");
      btn.setAttribute("title", isDark ? "Switch to Light Mode" : "Switch to Dark Mode");
      btn.innerHTML = isDark
        ? `<svg class="theme-icon sun-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>`
        : `<svg class="theme-icon moon-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>`;
    });
  }

  function toggleTheme() {
    const current = document.documentElement.getAttribute("data-theme") || getSavedTheme();
    const next = current === "dark" ? "light" : "dark";
    localStorage.setItem(STORAGE_KEY, next);
    applyTheme(next, true);
  }

  function initTheme() {
    const theme = getSavedTheme();
    applyTheme(theme, false);

    // Watch for system theme changes if user has not manually set a preference
    if (window.matchMedia) {
      window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", (e) => {
        if (!localStorage.getItem(STORAGE_KEY)) {
          applyTheme(e.matches ? "dark" : "light", true);
        }
      });
    }

    // Attach listeners to all theme toggle buttons
    document.addEventListener("click", (e) => {
      const btn = e.target.closest(".theme-toggle-btn");
      if (btn) {
        e.preventDefault();
        toggleTheme();
      }
    });
  }

  // Expose API globally
  window.Theme = {
    get: () => document.documentElement.getAttribute("data-theme") || getSavedTheme(),
    set: (t) => {
      localStorage.setItem(STORAGE_KEY, t);
      applyTheme(t, true);
    },
    toggle: toggleTheme,
    init: initTheme,
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initTheme);
  } else {
    initTheme();
  }
})();
