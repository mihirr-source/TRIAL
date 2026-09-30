/* =====================================================================
   PARAKH Standards Recommendation Engine — Components Module (components.js)
   Manages Cookie Consent, Floating Side Actions, and Scroll Animations
   ===================================================================== */
"use strict";

(function () {
  const COOKIE_STORAGE_KEY = "bis_cookie_consent";

  function initCookieBar() {
    const bar = document.getElementById("cookie-notice-bar");
    if (!bar) return;

    const consent = localStorage.getItem(COOKIE_STORAGE_KEY);
    if (!consent) {
      setTimeout(() => {
        bar.classList.add("visible");
      }, 750);
    }

    const acceptBtn = document.getElementById("btn-cookie-accept");
    const declineBtn = document.getElementById("btn-cookie-decline");
    const customizeBtn = document.getElementById("btn-cookie-customize");

    function saveAndClose(type) {
      localStorage.setItem(COOKIE_STORAGE_KEY, type);
      bar.classList.remove("visible");
      if (window.showToast) {
        showToast(type === "all" ? "Cookie preferences saved." : "Optional cookies declined.", "info", 2500);
      }
    }

    if (acceptBtn) acceptBtn.addEventListener("click", () => saveAndClose("all"));
    if (declineBtn) declineBtn.addEventListener("click", () => saveAndClose("essential"));
    if (customizeBtn) customizeBtn.addEventListener("click", () => saveAndClose("customized"));
  }

  function initSideActionBar() {
    const btnFeedback = document.getElementById("side-btn-feedback");
    const btnAssistant = document.getElementById("side-btn-assistant");
    const btnHistory = document.getElementById("side-btn-history");
    const btnShare = document.getElementById("side-btn-share");
    const btnTheme = document.getElementById("side-btn-theme");

    if (btnShare) {
      btnShare.addEventListener("click", () => {
        if (navigator.clipboard) {
          navigator.clipboard.writeText(window.location.href).then(() => {
            if (window.showToast) showToast("Link copied to clipboard!", "success");
          }).catch(() => {
            if (window.showToast) showToast("Share URL: " + window.location.href, "info");
          });
        }
      });
    }

    if (btnAssistant) {
      btnAssistant.addEventListener("click", () => {
        const chatLauncher = document.querySelector(".chat-launcher");
        if (chatLauncher) {
          chatLauncher.click();
        } else {
          location.href = "/assistant";
        }
      });
    }

    if (btnFeedback) {
      btnFeedback.addEventListener("click", () => {
        if (window.showToast) {
          showToast("Feedback modal: Thank you for helping us improve the standards portal!", "info");
        }
      });
    }

    if (btnHistory) {
      btnHistory.addEventListener("click", () => {
        location.href = "/standards";
      });
    }

    if (btnTheme && window.Theme) {
      btnTheme.addEventListener("click", () => {
        window.Theme.toggle();
      });
    }
  }

  function initScrollReveal() {
    if (!("IntersectionObserver" in window)) {
      document.querySelectorAll(".scroll-reveal").forEach((el) => el.classList.add("is-visible"));
      return;
    }

    const observer = new IntersectionObserver((entries, obs) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          obs.unobserve(entry.target);
        }
      });
    }, {
      threshold: 0.12,
      rootMargin: "0px 0px -40px 0px"
    });

    document.querySelectorAll(".scroll-reveal").forEach((el) => {
      observer.observe(el);
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    initCookieBar();
    initSideActionBar();
    initScrollReveal();
  });
})();
