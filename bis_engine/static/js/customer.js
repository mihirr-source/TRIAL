"use strict";

(function () {
  document.addEventListener("DOMContentLoaded", () => {
    const btnNewTender   = document.getElementById("btn-new-tender");
    const formContainer  = document.getElementById("new-tender-form-container");
    const btnCancel      = document.getElementById("btn-cancel-tender");
    const form           = document.getElementById("new-tender-form");
    const tendersContainer = document.getElementById("tenders-container");
    const modal          = document.getElementById("bid-modal");
    const modalClose     = document.getElementById("bid-modal-close");
    const modalContent   = document.getElementById("bid-modal-content");

    function escapeHtml(unsafe) {
      if (unsafe == null) return "";
      return String(unsafe)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
    }

    function toast(msg, type) {
      if (window.showToast) window.showToast(msg, type);
      else console.log(type + ":", msg);
    }

    // --- Show / hide bid-detail modal ---
    function openModal(bid) {
      if (!modal || !modalContent) return;
      const report    = bid.compliance_report || {};
      const issues    = report.issues    || [];
      const strengths = report.strengths || [];
      const scoreCol  = bid.compliance_score >= 90 ? "var(--accent)" : (bid.compliance_score >= 70 ? "#ff9800" : "#f44336");

      modalContent.innerHTML = `
        <h2 style="margin-top:0;font-size:1.5rem;">Bid from <span class="highlight">${escapeHtml(bid.vendor_name)}</span></h2>
        <div style="display:flex;gap:2rem;margin-top:1rem;padding:1.5rem;background:var(--bg-body);border-radius:8px;flex-wrap:wrap;">
          <div style="flex:1;min-width:100px;">
            <div style="font-size:.85rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;">AI Compliance Score</div>
            <div style="font-size:3rem;font-weight:800;color:${scoreCol};">${bid.compliance_score}<span style="font-size:1.5rem;">%</span></div>
          </div>
          <div style="flex:2;border-left:1px solid var(--border-color);padding-left:2rem;min-width:200px;">
            <p style="color:var(--text-main);font-weight:600;margin-top:0;">${escapeHtml(report.summary || "No summary available.")}</p>
            ${strengths.length ? `<div><strong style="color:var(--accent);">Strengths:</strong><ul style="margin-top:.5rem;padding-left:1.5rem;color:var(--text-muted);">${strengths.map(s=>`<li>${escapeHtml(s)}</li>`).join("")}</ul></div>` : ""}
            ${issues.length   ? `<div style="margin-top:.5rem;"><strong style="color:#f44336;">Issues:</strong><ul style="margin-top:.5rem;padding-left:1.5rem;color:var(--text-muted);">${issues.map(i=>`<li>${escapeHtml(i)}</li>`).join("")}</ul></div>` : ""}
          </div>
        </div>
        <div style="margin-top:2rem;">
          <h3 style="font-size:1.1rem;margin-bottom:.5rem;">Vendor's Specification</h3>
          <div style="background:var(--bg-input);padding:1rem;border-radius:8px;border:1px solid var(--border-color);color:var(--text-muted);font-size:.95rem;white-space:pre-wrap;">${escapeHtml(bid.spec_text)}</div>
        </div>
      `;
      modal.style.display = "flex";
    }

    function closeModal() {
      if (modal) modal.style.display = "none";
    }

    if (modalClose) modalClose.addEventListener("click", closeModal);
    if (modal) modal.addEventListener("click", (e) => { if (e.target === modal) closeModal(); });

    // --- Create Tender form ---
    if (btnNewTender) {
      btnNewTender.addEventListener("click", () => {
        formContainer.style.display = "block";
        document.getElementById("tender-title").focus();
      });
    }

    if (btnCancel) {
      btnCancel.addEventListener("click", () => {
        formContainer.style.display = "none";
        form.reset();
      });
    }

    if (form) {
      form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const title = document.getElementById("tender-title").value.trim();
        const desc  = document.getElementById("tender-desc").value.trim();
        if (!title || !desc) { toast("Please fill in all fields.", "error"); return; }

        const submitBtn = document.getElementById("btn-submit-tender");
        const origText  = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = "Publishing…";

        try {
          const res = await fetch("/api/bids/tenders", {
            method: "POST",
            credentials: "same-origin",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ title, description: desc }),
          });
          const json = await res.json().catch(() => ({}));
          if (!res.ok) throw new Error(json.detail || `Error ${res.status}`);

          toast("Tender published successfully!", "success");
          form.reset();
          formContainer.style.display = "none";
          loadTenders();
        } catch (err) {
          toast(err.message, "error");
        } finally {
          submitBtn.disabled = false;
          submitBtn.textContent = origText;
        }
      });
    }

    // --- Load & render tenders ---
    async function loadTenders() {
      tendersContainer.innerHTML = `<div class="loader-pulse" style="margin:2rem auto;"></div>`;
      try {
        const res = await fetch("/api/bids/tenders", { credentials: "same-origin" });
        const json = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(json.detail || "Failed to load tenders");

        tendersContainer.innerHTML = "";

        if (!json.tenders || json.tenders.length === 0) {
          tendersContainer.innerHTML = `<div class="card" style="text-align:center;padding:3rem;color:var(--text-muted);">No tenders yet. Click <strong>+ Create Tender</strong> to publish your first one.</div>`;
          return;
        }

        json.tenders.forEach(t => {
          const card = document.createElement("div");
          card.className = "card";
          Object.assign(card.style, { background: "var(--bg-card)", border: "1px solid var(--border-color)", padding: "2rem", borderRadius: "12px" });

          let bidsHtml = "";
          if (t.bids && t.bids.length > 0) {
            const rows = t.bids.map((b, idx) => {
              const scoreCol = b.compliance_score >= 90 ? "var(--accent)" : (b.compliance_score >= 70 ? "#ff9800" : "#f44336");
              const top = idx === 0 ? `<span style="background:var(--accent);color:#000;padding:2px 8px;border-radius:4px;font-size:.75rem;font-weight:bold;margin-left:10px;">TOP BID</span>` : "";
              const enc = encodeURIComponent(JSON.stringify(b));
              return `<div class="bid-row" data-bid="${enc}" style="background:var(--bg-body);border:1px solid var(--border-color);padding:1rem;border-radius:8px;display:flex;justify-content:space-between;align-items:center;cursor:pointer;transition:border .2s;">
                <div>
                  <div style="font-weight:600;color:var(--text-main);">${escapeHtml(b.vendor_name)}${top}</div>
                  <div style="font-size:.85rem;color:var(--text-muted);margin-top:4px;">AI Score: <strong style="color:${scoreCol}">${b.compliance_score}%</strong></div>
                </div>
                <button class="btn-secondary-auth" style="padding:.5rem 1rem;pointer-events:none;">View Analysis</button>
              </div>`;
            }).join("");
            bidsHtml = `<h3 style="margin-top:1.5rem;margin-bottom:1rem;font-size:1.1rem;color:var(--text-main);border-top:1px solid var(--border-color);padding-top:1rem;">Bids Received (${t.bids.length})</h3><div style="display:flex;flex-direction:column;gap:1rem;">${rows}</div>`;
          } else {
            bidsHtml = `<div style="margin-top:1.5rem;padding-top:1rem;border-top:1px solid var(--border-color);color:var(--text-muted);font-size:.9rem;">No bids received yet.</div>`;
          }

          card.innerHTML = `
            <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:1rem;gap:1rem;">
              <h2 style="margin:0;font-size:1.4rem;color:var(--text-main);">${escapeHtml(t.title)}</h2>
              <span style="font-family:var(--font-mono);font-size:.8rem;background:var(--bg-body);padding:4px 8px;border-radius:4px;color:var(--text-muted);white-space:nowrap;">ID: TEND-${t.id}</span>
            </div>
            <p style="color:var(--text-muted);font-size:.95rem;line-height:1.5;">${escapeHtml(t.description)}</p>
            ${bidsHtml}
          `;
          tendersContainer.appendChild(card);
        });

        // Wire up bid-row click handlers
        tendersContainer.querySelectorAll(".bid-row").forEach(row => {
          row.addEventListener("click", () => {
            try {
              const bid = JSON.parse(decodeURIComponent(row.getAttribute("data-bid")));
              openModal(bid);
            } catch (e) { console.error("Bid parse error:", e); }
          });
        });

      } catch (err) {
        tendersContainer.innerHTML = `<div style="color:#f44336;text-align:center;padding:2rem;">Error loading tenders: ${escapeHtml(err.message)}</div>`;
      }
    }

    // Init
    loadTenders();
  });
})();
