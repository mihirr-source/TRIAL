"use strict";

(function () {
  document.addEventListener("DOMContentLoaded", () => {
    const tabAll = document.getElementById("tab-all-tenders");
    const tabVault = document.getElementById("tab-my-vault");
    const feedContainer = document.getElementById("feed-container");
    const vaultContainer = document.getElementById("vault-container");
    
    // Modal
    const modal = document.getElementById("submit-bid-modal");
    const modalClose = document.getElementById("bid-modal-close");
    const form = document.getElementById("submit-bid-form");
    const modalTenderTitle = document.getElementById("modal-tender-title");
    const modalTenderId = document.getElementById("modal-tender-id");
    const btnSubmit = document.getElementById("btn-submit-bid");

    if (tabAll && tabVault) {
      tabAll.addEventListener("click", () => {
        tabAll.classList.add("active");
        tabVault.classList.remove("active");
        feedContainer.style.display = "flex";
        vaultContainer.style.display = "none";
        loadTenders();
      });
      tabVault.addEventListener("click", () => {
        tabVault.classList.add("active");
        tabAll.classList.remove("active");
        feedContainer.style.display = "none";
        vaultContainer.style.display = "flex";
        loadVault();
      });
    }

    if (modalClose) {
      modalClose.addEventListener("click", () => {
        modal.style.display = "none";
      });
    }

    if (form) {
      form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const specText = document.getElementById("bid-spec-text").value.trim();
        const tenderId = parseInt(modalTenderId.value, 10);
        
        btnSubmit.disabled = true;
        btnSubmit.textContent = "Analyzing Compliance with AI...";
        
        try {
          const res = await fetch("/api/bids/submit", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ tender_id: tenderId, spec_text: specText })
          });
          const data = await res.json();
          if (!res.ok) throw new Error(data.detail || "Failed to submit bid");
          
          window.showToast(`Bid submitted successfully! AI Score: ${data.score}%`, "success");
          form.reset();
          modal.style.display = "none";
          loadTenders(); // refresh to show "Bid Submitted" button
        } catch (err) {
          window.showToast(err.message, "error");
        } finally {
          btnSubmit.disabled = false;
          btnSubmit.textContent = "Submit Bid for AI Evaluation";
        }
      });
    }

    async function loadTenders() {
      try {
        const res = await fetch("/api/bids/tenders");
        if (!res.ok) throw new Error("Failed to load tenders");
        const data = await res.json();
        
        feedContainer.innerHTML = "";
        
        if (data.tenders.length === 0) {
          feedContainer.innerHTML = `<div class="card" style="text-align: center; padding: 3rem; color: var(--text-muted);">No active tenders found.</div>`;
          return;
        }
        
        data.tenders.forEach(t => {
          const card = document.createElement("div");
          card.className = "card";
          card.style.background = "var(--bg-card)";
          card.style.border = "1px solid var(--border-color)";
          card.style.padding = "2rem";
          card.style.borderRadius = "12px";
          
          const actionBtnHtml = t.has_bid 
            ? `<button class="btn-secondary-auth" disabled style="background: var(--bg-body); cursor: not-allowed; color: var(--text-muted);">✓ Bid Submitted</button>`
            : `<button class="btn-primary btn-place-bid" data-id="${t.id}" data-title="${escapeHtml(t.title)}" style="padding: 0.6rem 1.5rem;">Place Bid</button>`;
          
          card.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;">
              <div>
                <h2 style="margin: 0 0 0.5rem 0; font-size: 1.4rem; color: var(--text-main);">${escapeHtml(t.title)}</h2>
                <span style="font-family: var(--font-mono); font-size: 0.8rem; background: var(--bg-body); padding: 4px 8px; border-radius: 4px; color: var(--text-muted);">ID: TEND-${t.id} &bull; Buyer: ${escapeHtml(t.customer_email)}</span>
              </div>
              ${actionBtnHtml}
            </div>
            <p style="color: var(--text-muted); font-size: 0.95rem; line-height: 1.6;">${escapeHtml(t.description)}</p>
          `;
          
          feedContainer.appendChild(card);
        });
        
        // Attach click listeners to bid buttons
        document.querySelectorAll(".btn-place-bid").forEach(btn => {
          btn.addEventListener("click", () => {
            modalTenderId.value = btn.getAttribute("data-id");
            modalTenderTitle.textContent = btn.getAttribute("data-title");
            modal.style.display = "flex";
          });
        });
        
      } catch (err) {
        feedContainer.innerHTML = `<div style="color: red; text-align: center;">Error loading tenders.</div>`;
      }
    }
    
    async function loadVault() {
      try {
        vaultContainer.innerHTML = `<div class="loader-pulse" style="margin: 2rem auto;"></div>`;
        const res = await fetch("/api/bids/vault");
        if (!res.ok) throw new Error("Failed to load vault");
        const data = await res.json();
        
        vaultContainer.innerHTML = "";
        
        if (data.vault.length === 0) {
          vaultContainer.innerHTML = `<div class="card" style="text-align: center; padding: 3rem; color: var(--text-muted);">You haven't submitted any bids yet.</div>`;
          return;
        }
        
        data.vault.forEach(b => {
          const card = document.createElement("div");
          card.className = "card";
          card.style.background = "var(--bg-body)";
          card.style.border = "1px solid var(--border-color)";
          card.style.padding = "1.5rem";
          card.style.borderRadius = "12px";
          
          const scoreColor = b.compliance_score >= 90 ? "var(--accent)" : (b.compliance_score >= 70 ? "#ff9800" : "#f44336");
          const report = b.compliance_report || {};
          
          card.innerHTML = `
            <div style="display: flex; gap: 2rem;">
              <div style="flex: 1;">
                <div style="font-size: 0.85rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1px;">AI Compliance Score</div>
                <div style="font-size: 2.5rem; font-weight: 800; color: ${scoreColor};">${b.compliance_score}<span style="font-size: 1.2rem;">%</span></div>
              </div>
              <div style="flex: 3; border-left: 1px solid var(--border-color); padding-left: 1.5rem;">
                <h3 style="margin: 0 0 0.5rem 0; font-size: 1.2rem; color: var(--text-main);">Tender: ${escapeHtml(b.tender_title)}</h3>
                <p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 1rem;">${escapeHtml(report.summary || "No summary available.")}</p>
                <div style="font-size: 0.85rem; color: var(--text-main); background: var(--bg-card); padding: 0.8rem; border-radius: 6px; border: 1px solid var(--border-color);">
                  <strong>Your Spec Extract:</strong><br/>
                  <span style="color: var(--text-muted);">${escapeHtml(b.spec_text.substring(0, 150))}${b.spec_text.length > 150 ? '...' : ''}</span>
                </div>
              </div>
            </div>
          `;
          
          vaultContainer.appendChild(card);
        });
        
      } catch (err) {
        vaultContainer.innerHTML = `<div style="color: red; text-align: center;">Error loading vault.</div>`;
      }
    }

    function escapeHtml(unsafe) {
      if (!unsafe) return "";
      return (unsafe + "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
    }

    // Init
    loadTenders();
  });
})();
