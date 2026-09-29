/* =====================================================================
   BIS Standards Recommendation Engine — Footer Reveal Script (footer-reveal.js)
   Controls height measurement, scroll progress computation, and staggered
   blur/opacity/translate animations for the sticky under-page footer reveal.
   ===================================================================== */
"use strict";

(function () {
  function initFooterReveal() {
    const footer = document.querySelector(".reveal-footer");
    const pageWrap = document.querySelector(".page-wrap");
    if (!footer || !pageWrap) return;

    const cols = footer.querySelectorAll(".reveal-footer-col");
    const prefersReducedMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    // 1. Dynamic Height Measurement with ResizeObserver
    function updateFooterHeight() {
      const height = footer.offsetHeight;
      if (height > 0) {
        document.documentElement.style.setProperty("--footer-height", `${height}px`);
      }
    }

    if ("ResizeObserver" in window) {
      const ro = new ResizeObserver(() => {
        updateFooterHeight();
      });
      ro.observe(footer);
    } else {
      window.addEventListener("resize", updateFooterHeight, { passive: true });
    }
    updateFooterHeight();

    // 2. Scroll Progress & Staggered Column Animation
    let isTicking = false;

    function onScroll() {
      if (!isTicking) {
        window.requestAnimationFrame(() => {
          renderReveal();
          isTicking = false;
        });
        isTicking = true;
      }
    }

    function renderReveal() {
      const windowHeight = window.innerHeight;
      const scrollHeight = document.documentElement.scrollHeight;
      const scrollY = window.scrollY || window.pageYOffset;
      const totalScrollable = scrollHeight - windowHeight;
      const footerHeight = footer.offsetHeight || 380;

      if (totalScrollable <= 0) return;

      const distanceToBottom = totalScrollable - scrollY;
      // Progress from 0 (completely covered) to 1 (fully revealed)
      const rawProgress = 1 - (distanceToBottom / Math.max(1, footerHeight));
      const progress = Math.min(1, Math.max(0, rawProgress));

      // Toggle active / interactive state
      if (progress > 0.02) {
        footer.classList.add("is-active");
        footer.removeAttribute("inert");
        footer.removeAttribute("aria-hidden");
      } else {
        footer.classList.remove("is-active");
        footer.setAttribute("inert", "");
        footer.setAttribute("aria-hidden", "true");
      }

      if (prefersReducedMotion) {
        cols.forEach(col => {
          col.style.opacity = progress > 0.1 ? "1" : "0";
          col.style.transform = "none";
          col.style.filter = "none";
        });
        return;
      }

      // Animate columns with small progressive stagger
      cols.forEach((col, index) => {
        const startThreshold = 0.1 + (index * 0.12);
        const endThreshold = Math.min(1.0, startThreshold + 0.55);

        let colProgress = 0;
        if (progress >= endThreshold) {
          colProgress = 1;
        } else if (progress <= startThreshold) {
          colProgress = 0;
        } else {
          colProgress = (progress - startThreshold) / (endThreshold - startThreshold);
        }

        // Apply smooth easing
        const eased = Math.sin((colProgress * Math.PI) / 2);
        const translateY = Math.max(0, (1 - eased) * 28);
        const blurAmount = Math.max(0, (1 - eased) * 8);
        const opacity = Math.min(1, Math.max(0, eased * 1.05));

        col.style.transform = `translateY(${translateY.toFixed(1)}px)`;
        col.style.filter = blurAmount < 0.1 ? "none" : `blur(${blurAmount.toFixed(1)}px)`;
        col.style.opacity = opacity.toFixed(2);
      });
    }

    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", () => {
      updateFooterHeight();
      onScroll();
    }, { passive: true });

    // Initial render
    setTimeout(() => {
      updateFooterHeight();
      renderReveal();
    }, 60);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initFooterReveal);
  } else {
    initFooterReveal();
  }
})();
