// AI Shield — popup logic: toggle, threshold, backend status, tab count.

const $ = (id) => document.getElementById(id);

async function getActiveTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab;
}

function sendToTab(tabId, message) {
  return new Promise((resolve) => {
    chrome.tabs.sendMessage(tabId, message, (resp) => {
      void chrome.runtime.lastError; // content script may be absent
      resolve(resp || null);
    });
  });
}

// ---- toggle ----

chrome.storage.sync.get({ enabled: true, threshold: 0.7 }, (s) => {
  $("toggle").checked = s.enabled;
  $("threshold").value = s.threshold;
  $("threshold-value").textContent = Number(s.threshold).toFixed(2);
});

$("toggle").addEventListener("change", async (e) => {
  await chrome.storage.sync.set({ enabled: e.target.checked });
});

$("threshold").addEventListener("input", async (e) => {
  const v = Number(e.target.value);
  $("threshold-value").textContent = v.toFixed(2);
  await chrome.storage.sync.set({ threshold: v });
});

// ---- backend status ----

(async () => {
  const dot = $("status-dot");
  const text = $("status-text");
  try {
    const resp = await chrome.runtime.sendMessage({ type: "health" });
    if (resp && resp.ok && resp.data.status === "ok") {
      dot.classList.add(resp.data.model_loaded ? "online" : "offline");
      text.textContent = resp.data.model_loaded
        ? "Backend online · model loaded"
        : "Backend online · model idle";
    } else {
      dot.classList.add("offline");
      text.textContent = "Backend unreachable";
    }
  } catch (_) {
    dot.classList.add("offline");
    text.textContent = "Backend unreachable";
  }
})();

// ---- blurred count for this tab ----

(async () => {
  const tab = await getActiveTab();
  if (!tab || !/^https?:/i.test(tab.url || "")) {
    $("count").textContent = "0";
    return;
  }
  const resp = await sendToTab(tab.id, { type: "getStats" });
  $("count").textContent = resp && resp.ok ? String(resp.count) : "0";
})();
