/* =====================================================================
   PARAKH Standards Recommendation Engine — Navbar Module (navbar.js)
   Controls scroll transitions, sticky compact search, language dropdown,
   and responsive mobile navigation.
   ===================================================================== */
"use strict";

(function () {
  function initNavbar() {
    const header = document.querySelector(".site-header");
    const hero = document.querySelector(".hero-section");
    const compactSearch = document.getElementById("nav-compact-search-form");
    const compactInput = document.getElementById("nav-compact-query");
    const mobileToggle = document.getElementById("mobile-nav-toggle");
    const mainNav = document.getElementById("main-nav");
    const langBtn = document.getElementById("lang-dropdown-btn");
    const langContainer = document.querySelector(".lang-dropdown-container");

    // 1. Scroll Transition & Compact Search Visibility
    function updateNavbarScroll() {
      if (!header) return;
      const scrollY = window.scrollY || window.pageYOffset;
      
      if (!hero) {
        // Non-homepage: always scrolled solid
        header.classList.add("scrolled");
        return;
      }

      const heroBottom = hero.offsetTop + hero.offsetHeight - 120;

      if (scrollY > 40) {
        header.classList.add("scrolled");
      } else {
        header.classList.remove("scrolled");
      }

      if (scrollY > heroBottom) {
        header.classList.add("show-compact-search");
      } else {
        header.classList.remove("show-compact-search");
      }
    }

    window.addEventListener("scroll", updateNavbarScroll, { passive: true });
    updateNavbarScroll();

    // 2. Compact Search Submission
    if (compactSearch && compactInput) {
      compactSearch.addEventListener("submit", (e) => {
        e.preventDefault();
        const val = compactInput.value.trim();
        if (val.length >= 2) {
          if (location.pathname === "/") {
            const homeInput = document.getElementById("q");
            if (homeInput) {
              homeInput.value = val;
              const homeForm = document.getElementById("search-form");
              if (homeForm) homeForm.dispatchEvent(new Event("submit"));
            }
            window.scrollTo({ top: 0, behavior: "smooth" });
          } else {
            location.href = `/?q=${encodeURIComponent(val)}`;
          }
        }
      });
    }

    // 3. Language Selection (Desktop Dropdown & Mobile Menu)
    function switchLanguage(lang) {
      if (lang && window.setLang) {
        window.setLang(lang);
      }
      if (langContainer) langContainer.classList.remove("open");
      updateActiveLangUI(lang);
    }

    if (langBtn && langContainer) {
      langBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        langContainer.classList.toggle("open");
      });

      document.addEventListener("click", (e) => {
        if (!langContainer.contains(e.target)) {
          langContainer.classList.remove("open");
        }
      });

      document.querySelectorAll(".lang-option").forEach((opt) => {
        opt.addEventListener("click", () => {
          switchLanguage(opt.getAttribute("data-lang"));
        });
      });
    }

    // Mobile language pill clicks
    document.querySelectorAll(".mobile-lang-pill").forEach((pill) => {
      pill.addEventListener("click", () => {
        switchLanguage(pill.getAttribute("data-lang"));
      });
    });

    function updateActiveLangUI(currentLang) {
      const activeLang = currentLang || (typeof window.i18nLang === "function" ? window.i18nLang() : "en");
      
      document.querySelectorAll(".lang-option").forEach((opt) => {
        opt.classList.toggle("active", opt.getAttribute("data-lang") === activeLang);
      });
      
      document.querySelectorAll(".mobile-lang-pill").forEach((pill) => {
        pill.classList.toggle("active", pill.getAttribute("data-lang") === activeLang);
      });

      const langLabel = document.getElementById("current-lang-label");
      if (langLabel) {
        langLabel.textContent = activeLang === "hi" ? "हिन्दी" : activeLang === "te" ? "తెలుగు" : "English";
      }
    }

    updateActiveLangUI();

    // 4. Slide-out Navigation Drawer (Open / Close / Backdrop / Escape)
    const drawerToggles = document.querySelectorAll(".nav-drawer-toggle, #mobile-nav-toggle, #nav-drawer-toggle");
    const drawerCloseBtn = document.getElementById("drawer-close-btn");
    const drawerBackdrop = document.getElementById("nav-drawer-backdrop");

    function openDrawer() {
      if (mainNav) mainNav.classList.add("open");
      if (drawerBackdrop) drawerBackdrop.classList.add("open");
      drawerToggles.forEach(t => t.setAttribute("aria-expanded", "true"));
      document.body.style.overflow = "hidden";
    }

    function closeDrawer() {
      if (mainNav) mainNav.classList.remove("open");
      if (drawerBackdrop) drawerBackdrop.classList.remove("open");
      drawerToggles.forEach(t => t.setAttribute("aria-expanded", "false"));
      document.body.style.overflow = "";
    }

    drawerToggles.forEach(btn => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        if (mainNav && mainNav.classList.contains("open")) {
          closeDrawer();
        } else {
          openDrawer();
        }
      });
    });

    if (drawerCloseBtn) {
      drawerCloseBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        closeDrawer();
      });
    }

    if (drawerBackdrop) {
      drawerBackdrop.addEventListener("click", closeDrawer);
    }

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && mainNav && mainNav.classList.contains("open")) {
        closeDrawer();
      }
    });

    // Highlight active nav item
    if (window.BIS && window.BIS.setActiveNav) {
      window.BIS.setActiveNav();
    }
  }

  document.addEventListener("DOMContentLoaded", initNavbar);
})();
