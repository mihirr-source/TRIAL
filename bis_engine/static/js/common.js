/* PARAKH Standards Engine — shared UI helpers */
"use strict";

const $ = (sel, root) => (root || document).querySelector(sel);
const $$ = (sel, root) => Array.from((root || document).querySelectorAll(sel));

function setStatus(el, kind, msg) {
  if (!el) return;
  const cls = kind === "error" ? "alert-banner fail" :
              kind === "warn" ? "alert-banner warn" :
              kind === "ok" ? "alert-banner pass" : "muted small";
  el.className = cls;
  el.setAttribute("role", "status");
  el.textContent = msg;
}

function escapeHtml(s) {
  return String(s == null ? "" : s)
    .replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;").replaceAll("'", "&#39;");
}

async function fetchJSON(url, opts) {
  const res = await fetch(url, opts);
  let body = null;
  try { body = await res.json(); } catch { /* non-JSON error body */ }
  if (!res.ok) {
    const detail = body && body.detail ? body.detail : `${res.status} ${res.statusText}`;
    throw new Error(detail);
  }
  return body;
}

function setActiveNav() {
  const path = location.pathname;
  $$(".main-nav a").forEach((a) => {
    const href = a.getAttribute("href");
    if (href === "/" ? path === "/" : path.startsWith(href)) a.setAttribute("aria-current", "page");
  });
}

function confidencePill(score) {
  const pct = Math.round(score * 100);
  const label = pct >= 75 ? "High confidence" : pct >= 50 ? "Medium confidence" : "Low confidence";
  return `<span class="pill conf">${label} (${pct}%)</span>`;
}

function versionPill(std) {
  return `<span class="pill version">${escapeHtml(std.version)}</span>`;
}

function statusPill(std) {
  return std.status === "active"
    ? '<span class="pill active">active</span>'
    : `<span class="pill">${escapeHtml(std.status)}</span>`;
}

function certAlert(cert) {
  return `<div class="alert-banner warn">
    <strong>⚠ ${escapeHtml(cert.scheme)}</strong> — ${escapeHtml(cert.authority)}<br>
    <span class="small">${escapeHtml(cert.note)}</span>
  </div>`;
}

function alliedList(allied) {
  if (!allied || !allied.length) return '<p class="muted small">No allied standards recorded for this entry.</p>';
  return `<ul>${allied.map(a =>
    `<li><a href="/standards/${encodeURIComponent(a.code)}">${escapeHtml(a.code)}</a>
     <span class="muted small">— ${escapeHtml(a.relation)}</span></li>`).join("")}</ul>`;
}

function renderStandardCard(std, opts = {}) {
  const detail = opts.detail === false ? "" :
    `<p class="small" style="margin:.4rem 0 .6rem">${escapeHtml(std.summary || "")}</p>`;
  const conf = opts.confidence != null ? confidencePill(opts.confidence) : "";
  const examples = (std.examples || []).map(ex => `
    <div class="alert-banner warn small no-print">
      <strong>Spec pitfall:</strong> ${escapeHtml(ex.bad)} → <strong>${escapeHtml(ex.good)}</strong>
      <div class="muted">${escapeHtml(ex.note)}</div>
    </div>`).join("");
  const certs = (std.certifications || []).map(certAlert).join("");
  return `<article class="card" data-code="${escapeHtml(std.code)}">
    <div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:.4rem">
      <span class="std-code"><a href="/standards/${encodeURIComponent(std.code)}">${escapeHtml(std.code)}</a> — ${escapeHtml(std.title)}</span>
      <span>${statusPill(std)}</span>
    </div>
    ${detail}
    <div style="margin:.5rem 0">${versionPill(std)} ${conf}</div>
    ${certs}${examples}
  </article>`;
}

window.BIS = { $, $$, setStatus, escapeHtml, fetchJSON, setActiveNav,
  confidencePill, versionPill, statusPill, certAlert, alliedList, renderStandardCard };
