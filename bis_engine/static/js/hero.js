/* =====================================================================
   PARAKH Standards Recommendation Engine — Hero Module (hero.js)
   Controls background slideshow cross-fade, sector filters & trending chips
   ===================================================================== */
"use strict";

(function () {
  function initHero() {
    const slides = document.querySelectorAll(".hero-slide");
    if (!slides.length) return;

    let currentSlide = 0;
    const intervalTime = 6000;

    function nextSlide() {
      slides[currentSlide].classList.remove("active");
      currentSlide = (currentSlide + 1) % slides.length;
      slides[currentSlide].classList.add("active");
    }

    // Initialize first slide as active
    slides[0].classList.add("active");
    setInterval(nextSlide, intervalTime);
  }

  document.addEventListener("DOMContentLoaded", initHero);
})();
