// AI Shield — content script. Runs on every page; never throws.
(() => {
  "use strict";

  if (window.__aiShieldLoaded) return;
  window.__aiShieldLoaded = true;

  const TEXT_THRESHOLD = 0.7;
  const IMAGE_THRESHOLD = 0.7;
  const MIN_IMG_SIZE = 100; // px — skip icons/avatars
  const MAX_NODE_CHARS = 500;
  const SCAN_DEBOUNCE_MS = 600;
  const MAX_NODES_PER_PASS = 400;

  let enabled = true;
  let threshold = 0.7; // popup-adjustable
  const textCache = new Map(); // text -> {is_toxic, toxicity_score}
  const imgCache = new Map(); // src -> {is_nsfw, nsfw_score}
  let blurredCount = 0;
  let scanTimer = null;

  // ---------- settings ----------

  try {
    chrome.storage.sync.get({ enabled: true, threshold: 0.7 }, (s) => {
      enabled = !!s.enabled;
      threshold = Number(s.threshold) || 0.7;
      if (enabled) scheduleScan();
    });
    chrome.storage.onChanged.addListener((changes) => {
      if (changes.enabled) {
        enabled = !!changes.enabled.newValue;
        if (enabled) scheduleScan();
        else removeAllBlurs();
      }
      if (changes.threshold) {
        threshold = Number(changes.threshold.newValue) || 0.7;
        reevaluateBlurs();
      }
    });
  } catch (_) {}

  // ---------- text scanning ----------

  function collectTextNodes(root) {
    const walker = document.createTreeWalker(
      root,
      NodeFilter.SHOW_TEXT,
      {
        acceptNode(node) {
          if (!node.nodeValue || node.nodeValue.trim().length < 4)
            return NodeFilter.FILTER_REJECT;
          const p = node.parentElement;
          if (!p) return NodeFilter.FILTER_REJECT;
          const tag = p.closest("script,style,noscript,textarea,input,code,pre,[contenteditable='true']");
          if (tag) return NodeFilter.FILTER_REJECT;
          if (p.closest(".ai-shield-blur-text")) return NodeFilter.FILTER_REJECT;
          if (p.offsetParent === null && getComputedStyle(p).position !== "fixed")
            return NodeFilter.FILTER_REJECT;
          return NodeFilter.FILTER_ACCEPT;
        },
      }
    );
    const nodes = [];
    let n;
    while ((n = walker.nextNode()) && nodes.length < MAX_NODES_PER_PASS) {
      nodes.push(n);
    }
    return nodes;
  }

  async function scanText(root) {
    const nodes = collectTextNodes(root);
    if (!nodes.length) return;

    const pending = [];
    const seen = new Set();
    for (const node of nodes) {
      const text = node.nodeValue.trim().slice(0, MAX_NODE_CHARS);
      if (seen.has(text)) continue;
      seen.add(text);
      if (!textCache.has(text)) pending.push(text);
    }
    if (pending.length) {
      try {
        const resp = await chrome.runtime.sendMessage({
          type: "analyzeText",
          texts: pending,
        });
        if (resp && resp.ok) {
          for (const r of resp.results) {
            textCache.set(r.text, r);
          }
        }
      } catch (_) {
        return; // backend down — do nothing this pass
      }
    }

    for (const node of nodes) {
      if (!node.isConnected) continue;
      const text = node.nodeValue.trim().slice(0, MAX_NODE_CHARS);
      const verdict = textCache.get(text);
      if (verdict && verdict.toxicity_score > threshold) blurTextNode(node, verdict);
    }
  }

  function blurTextNode(node, verdict) {
    const parent = node.parentElement;
    if (!parent || parent.closest(".ai-shield-blur-text")) return;

    const span = document.createElement("span");
    span.className = "ai-shield-blur-text";
    span.dataset.aiShieldScore = String(verdict.toxicity_score ?? "");

    const original = document.createTextNode(node.nodeValue);
    span.appendChild(original);

    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "ai-shield-reveal-btn";
    btn.textContent = "View Harmful Content";
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      e.preventDefault();
      span.classList.add("ai-shield-revealed");
      btn.remove();
      blurredCount = Math.max(0, blurredCount - 1);
      updateBadgeCount();
    });

    span.appendChild(btn);
    parent.replaceChild(span, node);
    blurredCount += 1;
    updateBadgeCount();
  }

  // ---------- image scanning ----------

  function collectImages() {
    const imgs = [];
    for (const img of document.images) {
      if (img.closest(".ai-shield-blur-img")) continue;
      if (img.width < MIN_IMG_SIZE || img.height < MIN_IMG_SIZE) continue;
      const src = img.currentSrc || img.src;
      if (!src || !/^https?:/i.test(src)) continue;
      imgs.push(img);
    }
    return imgs.slice(0, MAX_NODES_PER_PASS);
  }

  async function scanImages() {
    const imgs = collectImages();
    if (!imgs.length) return;

    const pending = [];
    const seen = new Set();
    for (const img of imgs) {
      const src = img.currentSrc || img.src;
      if (!seen.has(src)) {
        seen.add(src);
        if (!imgCache.has(src)) pending.push(src);
      }
    }
    if (pending.length) {
      try {
        const resp = await chrome.runtime.sendMessage({
          type: "analyzeImages",
          urls: pending,
        });
        if (resp && resp.ok) {
          for (const r of resp.results) {
            if (!r.error) imgCache.set(r.url, r);
          }
        }
      } catch (_) {
        return;
      }
    }

    for (const img of imgs) {
      if (!img.isConnected) continue;
      const src = img.currentSrc || img.src;
      const verdict = imgCache.get(src);
      if (verdict && verdict.nsfw_score > threshold) blurImage(img, verdict);
    }
  }

  function blurImage(img, verdict) {
    const wrapper = document.createElement("span");
    wrapper.className = "ai-shield-blur-img";
    wrapper.dataset.aiShieldScore = String(verdict.nsfw_score ?? "");

    img.parentNode.insertBefore(wrapper, img);
    wrapper.appendChild(img);

    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "ai-shield-reveal-btn";
    btn.textContent = "View Harmful Content";
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      e.preventDefault();
      wrapper.classList.add("ai-shield-revealed");
      btn.remove();
      blurredCount = Math.max(0, blurredCount - 1);
      updateBadgeCount();
    });
    wrapper.appendChild(btn);

    blurredCount += 1;
    updateBadgeCount();
  }

  // ---------- housekeeping ----------

  function removeAllBlurs() {
    document
      .querySelectorAll(".ai-shield-blur-text, .ai-shield-blur-img")
      .forEach((el) => {
        el.classList.add("ai-shield-revealed");
        const btn = el.querySelector(".ai-shield-reveal-btn");
        if (btn) btn.remove();
      });
  }

  // Re-apply or lift blurs when the threshold slider moves.
  function reevaluateBlurs() {
    document.querySelectorAll(".ai-shield-blur-text").forEach((el) => {
      const score = Number(el.dataset.aiShieldScore);
      if (!Number.isNaN(score)) {
        el.classList.toggle("ai-shield-revealed", score <= threshold);
      }
    });
    document.querySelectorAll(".ai-shield-blur-img").forEach((el) => {
      const score = Number(el.dataset.aiShieldScore);
      if (!Number.isNaN(score)) {
        el.classList.toggle("ai-shield-revealed", score <= threshold);
      }
    });
  }

  function updateBadgeCount() {
    try {
      chrome.runtime.sendMessage({ type: "updateBadge", count: blurredCount });
    } catch (_) {}
  }

  function scheduleScan() {
    if (!enabled) return;
    clearTimeout(scanTimer);
    scanTimer = setTimeout(() => {
      scanText(document.body);
      scanImages();
    }, SCAN_DEBOUNCE_MS);
  }

  // Popup asks for the current blurred count.
  chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
    if (msg && msg.type === "getStats") {
      sendResponse({ ok: true, count: blurredCount });
    }
    return false;
  });

  const observer = new MutationObserver(() => scheduleScan());
  function startObserver() {
    observer.observe(document.body, { childList: true, subtree: true });
  }

  if (document.body) {
    startObserver();
    scheduleScan();
  } else {
    document.addEventListener("DOMContentLoaded", () => {
      startObserver();
      scheduleScan();
    });
  }
})();
