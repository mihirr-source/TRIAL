// AI Shield — background service worker (MV3).
// Sole network caller: content scripts message here; never fetch directly.

const API_BASE = "http://localhost:8000";
const MAX_TEXT_BATCH = 40;
const MAX_IMAGE_BATCH = 20;

async function analyzeText(texts) {
  const out = [];
  for (let i = 0; i < texts.length; i += MAX_TEXT_BATCH) {
    const batch = texts.slice(i, i + MAX_TEXT_BATCH);
    const res = await fetch(`${API_BASE}/analyze-batch`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ texts: batch }),
    });
    if (!res.ok) throw new Error(`analyze-batch HTTP ${res.status}`);
    const data = await res.json();
    out.push(...data.results);
  }
  return out;
}

async function analyzeImages(urls) {
  const out = [];
  for (let i = 0; i < urls.length; i += MAX_IMAGE_BATCH) {
    const batch = urls.slice(i, i + MAX_IMAGE_BATCH);
    const res = await fetch(`${API_BASE}/analyze-image-urls`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ urls: batch }),
    });
    if (!res.ok) throw new Error(`analyze-image-urls HTTP ${res.status}`);
    const data = await res.json();
    out.push(...data.results);
  }
  return out;
}

async function checkHealth() {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error(`health HTTP ${res.status}`);
  return res.json();
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  (async () => {
    try {
      if (msg.type === "analyzeText") {
        sendResponse({ ok: true, results: await analyzeText(msg.texts) });
      } else if (msg.type === "analyzeImages") {
        sendResponse({ ok: true, results: await analyzeImages(msg.urls) });
      } else if (msg.type === "health") {
        sendResponse({ ok: true, data: await checkHealth() });
      } else if (msg.type === "updateBadge") {
        const tabId = sender.tab ? sender.tab.id : undefined;
        const count = Math.max(0, msg.count | 0);
        if (tabId !== undefined) {
          await chrome.action.setBadgeText({
            text: count > 0 ? String(count) : "",
            tabId,
          });
          await chrome.action.setBadgeBackgroundColor({
            color: "#b91c1c",
            tabId,
          });
        }
        sendResponse({ ok: true });
      } else {
        sendResponse({ ok: false, error: `Unknown message ${msg.type}` });
      }
    } catch (err) {
      sendResponse({ ok: false, error: String(err && err.message) });
    }
  })();
  return true; // keep the channel open for the async response
});
