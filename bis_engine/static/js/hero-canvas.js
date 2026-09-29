/* =====================================================================
   BIS Standards Recommendation Engine — Interactive Hero ASCII Canvas
   Renders an interactive matrix of ASCII characters and chromatic color
   blobs that dynamically react to cursor movement and viewport resize.
   ===================================================================== */
"use strict";

(function () {
  function initHeroCanvas() {
    const canvas = document.getElementById("hero-ascii-canvas");
    if (!canvas) return;

    const ctx = canvas.getContext("2d", { alpha: true });
    if (!ctx) return;

    // Respect user motion preference
    const prefersReducedMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    let width = 0;
    let height = 0;
    let animationFrameId = null;
    let isVisible = true;
    let lastTime = 0;

    // Mouse coordinates (normalized 0 to 1)
    let mouse = { x: 0.65, y: 0.35, targetX: 0.65, targetY: 0.35, isHovering: false };

    // ASCII character set from light to dense
    const CHARS = ["·", "+", "*", "=", "%", "#", "@", "&", "$"];
    const FONT_SIZE = 13;
    const CELL_W = 12;
    const CELL_H = 14;

    function resize() {
      const rect = canvas.parentElement ? canvas.parentElement.getBoundingClientRect() : { width: window.innerWidth, height: 600 };
      width = Math.floor(rect.width);
      height = Math.floor(rect.height || 600);
      
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      canvas.style.width = width + "px";
      canvas.style.height = height + "px";
      ctx.scale(dpr, dpr);
    }

    window.addEventListener("resize", () => {
      resize();
    }, { passive: true });

    // Track mouse over hero section
    const heroSection = canvas.closest(".hero-section") || canvas.parentElement;
    if (heroSection) {
      heroSection.addEventListener("mousemove", (e) => {
        const rect = heroSection.getBoundingClientRect();
        mouse.targetX = (e.clientX - rect.left) / rect.width;
        mouse.targetY = (e.clientY - rect.top) / rect.height;
        mouse.isHovering = true;
      }, { passive: true });

      heroSection.addEventListener("mouseleave", () => {
        mouse.isHovering = false;
      });
    }

    // Pause rendering when tab is hidden or element is scrolled out of viewport
    if ("IntersectionObserver" in window && heroSection) {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          isVisible = entry.isIntersecting;
          if (isVisible && !animationFrameId && !prefersReducedMotion) {
            lastTime = performance.now();
            render(lastTime);
          }
        });
      }, { threshold: 0.05 });
      observer.observe(heroSection);
    }

    document.addEventListener("visibilitychange", () => {
      isVisible = !document.hidden;
      if (isVisible && !animationFrameId && !prefersReducedMotion) {
        lastTime = performance.now();
        render(lastTime);
      }
    });

    resize();

    // Render loop
    function render(currentTime) {
      if (!isVisible) {
        animationFrameId = null;
        return;
      }

      const elapsed = (currentTime - lastTime) * 0.001;
      lastTime = currentTime;
      const t = currentTime * 0.0015;

      // Smooth mouse interpolation
      mouse.x += (mouse.targetX - mouse.x) * 0.08;
      mouse.y += (mouse.targetY - mouse.y) * 0.08;

      ctx.clearRect(0, 0, width, height);

      ctx.font = `bold ${FONT_SIZE}px "JetBrains Mono", ui-monospace, monospace`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";

      const cols = Math.ceil(width / CELL_W);
      const rows = Math.ceil(height / CELL_H);

      // Center point for chromatic rainbow blob
      const blobX = mouse.x * width;
      const blobY = mouse.y * height;
      const maxDist = Math.max(width, height) * 0.7;

      for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
          const px = c * CELL_W + CELL_W / 2;
          const py = r * CELL_H + CELL_H / 2;

          // Distance to interactive blob
          const dx = px - blobX;
          const dy = py - blobY;
          const dist = Math.sqrt(dx * dx + dy * dy);

          // Wave field
          const wave1 = Math.sin(c * 0.08 + t * 1.5) * Math.cos(r * 0.08 + t * 1.2);
          const wave2 = Math.sin((c + r) * 0.05 - t * 0.8);
          const combined = (wave1 + wave2 + 2) / 4;

          // Interactive influence near mouse
          const mouseFactor = Math.max(0, 1 - dist / (maxDist * 0.55));
          const intensity = Math.min(1, Math.max(0, combined * 0.4 + mouseFactor * 0.75));

          if (intensity < 0.12) continue;

          // Pick character based on intensity
          const charIndex = Math.min(CHARS.length - 1, Math.floor(intensity * CHARS.length));
          const char = CHARS[charIndex];

          // Chromatic gradient color (Cyan -> Pink -> Orange -> Vivid Yellow)
          const hue = (t * 20 + (c / cols) * 120 + (r / rows) * 80 + mouseFactor * 100) % 360;
          const alpha = Math.min(0.85, intensity * 0.95);

          // In light/dark mode the characters stand out sharply on the yellow background
          ctx.fillStyle = `hsla(${hue}, 85%, 25%, ${alpha})`;
          ctx.fillText(char, px, py);
        }
      }

      if (!prefersReducedMotion) {
        animationFrameId = requestAnimationFrame(render);
      }
    }

    if (prefersReducedMotion) {
      // Static single draw
      render(0);
    } else {
      lastTime = performance.now();
      animationFrameId = requestAnimationFrame(render);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initHeroCanvas);
  } else {
    initHeroCanvas();
  }
})();
