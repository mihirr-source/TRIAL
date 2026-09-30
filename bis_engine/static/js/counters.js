/* =====================================================================
   PARAKH Standards Recommendation Engine — Monospace Numeric Counters
   Animates numeric values when scrolled into viewport using requestAnimationFrame
   ===================================================================== */
"use strict";

(function () {
  function initCounters() {
    const counterElements = document.querySelectorAll("[data-counter-target]");
    if (!counterElements.length) return;

    const prefersReducedMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    function animateCounter(el) {
      const targetStr = el.getAttribute("data-counter-target") || "0";
      const target = parseFloat(targetStr.replace(/[^0-9.]/g, "")) || 0;
      const prefix = el.getAttribute("data-counter-prefix") || "";
      const suffix = el.getAttribute("data-counter-suffix") || "";
      const duration = parseInt(el.getAttribute("data-counter-duration") || "1400", 10);

      if (prefersReducedMotion) {
        el.textContent = `${prefix}${targetStr}${suffix}`;
        return;
      }

      let startTime = null;

      function step(now) {
        if (!startTime) startTime = now;
        const progress = Math.min((now - startTime) / duration, 1);
        // Easing: easeOutExpo
        const ease = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
        const current = Math.floor(ease * target);

        el.textContent = `${prefix}${current.toLocaleString()}${suffix}`;

        if (progress < 1) {
          requestAnimationFrame(step);
        } else {
          el.textContent = `${prefix}${targetStr}${suffix}`;
        }
      }

      requestAnimationFrame(step);
    }

    if ("IntersectionObserver" in window) {
      const observer = new IntersectionObserver((entries, obs) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            animateCounter(entry.target);
            obs.unobserve(entry.target);
          }
        });
      }, { threshold: 0.2 });

      counterElements.forEach(el => observer.observe(el));
    } else {
      counterElements.forEach(el => animateCounter(el));
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initCounters);
  } else {
    initCounters();
  }
})();
