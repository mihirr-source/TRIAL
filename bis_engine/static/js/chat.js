/* Assistant chat: full-page mode (#chat-page present) or floating widget
 * on every other page. Both talk to POST /api/assistant with the current
 * UI language so replies come back in the user's language. */
"use strict";

(function () {

  function renderRich(el, text) {
    const formatted = String(text)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      .replace(/_(.+?)_/g, "<em>$1</em>")
      .replace(/\n\n/g, "</p><p>")
      .replace(/\n/g, "<br>");
    
    el.innerHTML = `
      <div class="msg-avatar assistant-avatar" aria-hidden="true">🤖</div>
      <div class="msg-content"><p>${formatted}</p></div>
    `;
  }

  function escapeAll(el, text) {
    el.innerHTML = `
      <div class="msg-content">${escapeHtml(text)}</div>
      <div class="msg-avatar user-avatar-msg" aria-hidden="true">👤</div>
    `;
  }

  async function ask(message, logEl, lang) {
    const typing = document.createElement("div");
    typing.className = "chat-msg assistant typing-msg animate-fade-in";
    typing.innerHTML = `
      <div class="msg-avatar assistant-avatar" aria-hidden="true">🤖</div>
      <div class="typing-bubble" aria-label="Assistant is thinking">
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
      </div>
    `;
    logEl.appendChild(typing);
    logEl.scrollTop = logEl.scrollHeight;

    try {
      const data = await fetchJSON("/api/assistant", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, lang }),
      });
      typing.classList.remove("typing-msg");
      renderRich(typing, data.reply);
    } catch (err) {
      typing.classList.remove("typing-msg");
      typing.innerHTML = `
        <div class="msg-avatar assistant-avatar" aria-hidden="true">🤖</div>
        <div class="msg-content error-text"><strong>Service Notice:</strong> ${escapeHtml(err.message)}</div>
      `;
    }
    logEl.scrollTop = logEl.scrollHeight;
  }

  function userMsg(logEl, text) {
    const div = document.createElement("div");
    div.className = "chat-msg user animate-fade-in";
    escapeAll(div, text);
    logEl.appendChild(div);
    logEl.scrollTop = logEl.scrollHeight;
  }

  function bindForm(form, input, logEl, suggestBar) {
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const text = input.value.trim();
      if (!text) return;
      userMsg(logEl, text);
      ask(text, logEl, typeof i18nLang === "function" ? i18nLang() : "en");
      input.value = "";
    });
    if (suggestBar) {
      suggestBar.addEventListener("click", (e) => {
        const chip = e.target.closest(".chip");
        if (!chip) return;
        const query = chip.textContent.trim();
        userMsg(logEl, query);
        ask(query, logEl, typeof i18nLang === "function" ? i18nLang() : "en");
      });
    }
  }

  // ---------------------------------------------------- full-page chat mode
  const page = $("#chat-page");
  if (page) {
    const logEl = $("#chat-log");
    
    // Initial friendly greeting if chat log is empty
    if (logEl && !logEl.hasChildNodes()) {
      const welcome = document.createElement("div");
      welcome.className = "chat-msg assistant animate-fade-in";
      welcome.innerHTML = `
        <div class="msg-avatar assistant-avatar" aria-hidden="true">🤖</div>
        <div class="msg-content">
          <p><strong>Namaste! I am your PARAKH AI Assistant.</strong></p>
          <p>You can ask me questions about Indian Standards (BIS), required test methods, or mandatory certification schemes (ISI mark, CRS, BEE star labelling) in English, हिन्दी, or తెలుగు.</p>
        </div>
      `;
      logEl.appendChild(welcome);
    }

    bindForm($("#chat-form"), $("#chat-input"), logEl, $("#chat-suggest"));
    return;
  }

  // -------------------------------------------------- floating widget mode
  const launcher = document.createElement("button");
  launcher.id = "chat-launcher";
  launcher.className = "chat-launcher";
  launcher.type = "button";
  launcher.setAttribute("aria-label", "PARAKH AI Assistant");
  launcher.innerHTML = `💬`;

  const panel = document.createElement("div");
  panel.id = "chat-panel";
  panel.className = "chat-panel";
  panel.hidden = true;
  panel.setAttribute("role", "dialog");
  panel.setAttribute("aria-label", "PARAKH AI Assistant Widget");
  panel.innerHTML = `
    <div class="chat-head">
      <div style="display:flex; align-items:center; gap:0.5rem;">
        <span style="font-size:1.1rem;">🤖</span>
        <strong data-i18n="nav.assistant">PARAKH AI Assistant</strong>
      </div>
      <button class="chat-close" type="button" aria-label="Close">✕</button>
    </div>
    <div class="chat-log" aria-live="polite">
      <div class="chat-msg assistant animate-fade-in">
        <div class="msg-avatar assistant-avatar" aria-hidden="true">🤖</div>
        <div class="msg-content">
          <p>Hello! Ask me any question about Indian Standards or certification rules.</p>
        </div>
      </div>
    </div>
    <form class="chat-form">
      <input type="text" autocomplete="off" data-i18n-ph="asst.ph"
             placeholder="Ask anything… e.g. “Which standard for drinking water pipes?”">
      <button type="submit" data-i18n="asst.send" class="btn-press">Send</button>
    </form>`;

  launcher.addEventListener("click", () => {
    panel.hidden = !panel.hidden;
    if (!panel.hidden) {
      panel.querySelector("input").focus();
    }
  });

  panel.querySelector(".chat-close").addEventListener("click", (e) => {
    e.preventDefault();
    e.stopPropagation();
    panel.hidden = true;
  });

  bindForm(panel.querySelector(".chat-form"), panel.querySelector("input"),
           panel.querySelector(".chat-log"), null);

  function mount() {
    document.body.appendChild(launcher);
    document.body.appendChild(panel);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mount);
  } else {
    mount();
  }
})();
