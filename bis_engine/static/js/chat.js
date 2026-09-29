/* Assistant chat: full-page mode (#chat-page present) or floating widget
 * on every other page. Both talk to POST /api/assistant with the current
 * UI language so replies come back in the user's language. */
"use strict";

(function () {

  function renderRich(el, text) {
    el.innerHTML = String(text)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/`(.+?)`/g, "<code>$1</code>")
      .replace(/_(.+?)_/g, "<em>$1</em>")
      .replace(/\n/g, "<br>");
  }

  function escapeAll(el, text) {
    el.textContent = text;
  }

  async function ask(message, logEl, lang) {
    const typing = document.createElement("div");
    typing.className = "chat-msg assistant";
    typing.textContent = "…";
    logEl.appendChild(typing);
    logEl.scrollTop = logEl.scrollHeight;
    try {
      const data = await fetchJSON("/api/assistant", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, lang }),
      });
      renderRich(typing, data.reply);
    } catch (err) {
      typing.textContent = `Error: ${err.message}`;
    }
    logEl.scrollTop = logEl.scrollHeight;
  }

  function userMsg(logEl, text) {
    const div = document.createElement("div");
    div.className = "chat-msg user";
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
      ask(text, logEl, i18nLang());
      input.value = "";
    });
    if (suggestBar) {
      suggestBar.addEventListener("click", (e) => {
        const chip = e.target.closest(".chip");
        if (!chip) return;
        userMsg(logEl, chip.textContent.trim());
        ask(chip.textContent.trim(), logEl, i18nLang());
      });
    }
  }

  // ---------------------------------------------------- full-page chat mode
  const page = $("#chat-page");
  if (page) {
    const logEl = $("#chat-log");
    bindForm($("#chat-form"), $("#chat-input"), logEl, $("#chat-suggest"));
    return;
  }

  // -------------------------------------------------- floating widget mode
  const launcher = document.createElement("button");
  launcher.id = "chat-launcher";
  launcher.className = "chat-launcher";
  launcher.type = "button";
  launcher.setAttribute("aria-label", "AI Assistant");
  launcher.textContent = "💬";

  const panel = document.createElement("div");
  panel.id = "chat-panel";
  panel.className = "chat-panel";
  panel.hidden = true;
  panel.setAttribute("role", "dialog");
  panel.setAttribute("aria-label", "AI Assistant");
  panel.innerHTML = `
    <div class="chat-head">
      <strong data-i18n="nav.assistant">AI Assistant</strong>
      <button class="chat-close" type="button" aria-label="Close">✕</button>
    </div>
    <div class="chat-log" aria-live="polite"></div>
    <form class="chat-form searchbar">
      <input type="text" autocomplete="off" data-i18n-ph="asst.ph"
             placeholder="Ask anything… e.g. “Which standard for drinking water pipes?”">
      <button type="submit" data-i18n="asst.send">Send</button>
    </form>`;

  launcher.addEventListener("click", () => {
    panel.hidden = !panel.hidden;
    if (!panel.hidden) panel.querySelector("input").focus();
  });
  panel.querySelector(".chat-close").addEventListener("click", () => { panel.hidden = true; });
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
