"use strict";

(function () {
  document.addEventListener("DOMContentLoaded", () => {
    const btnNewTender = document.getElementById("btn-new-tender");
    const formContainer = document.getElementById("new-tender-form-container");
    const btnCancel = document.getElementById("btn-cancel-tender");
    const form = document.getElementById("new-tender-form");
    const tendersContainer = document.getElementById("tenders-container");
    
    // Modal
    const modal = document.getElementById("bid-modal");
    const modalClose = document.getElementById("bid-modal-close");
    const modalContent = document.getElementById("bid-modal-content");

    if (btnNewTender) {
      btnNewTender.addEventListener("click", () => {
        formContainer.style.display = "block";
      });
    }

    if (btnCancel) {
      btnCancel.addEventListener("click", () => {
        formContainer.style.display = "none";
        form.reset();
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
        const title = document.getElementById("tender-title").value.trim();
        const desc = document.getElementById("tender-desc").value.trim();
        
        const submitBtn = document.getElementById("btn-submit-tender");
        submitBtn.disabled = true;
        
        try {
          const res = await fetch("/api/bids/tenders", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ title, description: desc })
          });
          if (!res.ok) throw new Error("Failed to publish tender");
          
          window.showToast("Tender published successfully!", "success");
          form.reset();
          formContainer.style.display = "none";
          loadTenders();
        } catch (err) {
          window.showToast(err.message, "error");
        } finally {
          submitBtn.disabled = false;
        }
      });
    }

    async function loadTenders() {
      try {
        const res = await fetch("/api/bids/tenders");
        if (!res.ok) throw new Error("Failed to load tenders");
        const data = await res.json();
        
        tendersContainer.innerHTML = "";
        
        if (data.tenders.length === 0) {
          tendersContainer.innerHTML = `<div class="card" style="text-align: center; padding: 3rem; color: var(--text-muted);">You haven't created any tenders yet.</div>`;
          return;
        }
        
        data.tenders.forEach(t => {
          const card = document.createElement("div");
          card.className = "card";
          card.style.background = "var(--bg-card)";
          card.style.border = "1px solid var(--border-color)";
          card.style.padding = "2rem";
          card.style.borderRadius = "12px";
          
          let bidsHtml = "";
          if (t.bids && t.bids.length > 0) {
            bidsHtml = `<h3 style="margin-top: 1.5rem; margin-bottom: 1rem; font-size: 1.1rem; color: var(--text-main); border-top: 1px solid var(--border-color); padding-top: 1rem;">Bids Received (${t.bids.length})</h3>`;
            bidsHtml += `<div style="display: flex; flex-direction: column; gap: 1rem;">`;
            
            t.bids.forEach((b, index) => {
              const scoreColor = b.compliance_score >= 90 ? "var(--accent)" : (b.compliance_score >= 70 ? "#ff9800" : "#f44336");
              const rankHtml = index === 0 ? `<span style="background: var(--accent); color: #000; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; margin-left: 10px;">TOP BID</span>` : "";
              
              // We stringify the bid object to pass it to the click handler
              const encodedBid = encodeURIComponent(JSON.stringify(b));
              
              bidsHtml += `
                <div style="background: var(--bg-body); border: 1px solid var(--border-color); padding: 1rem; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; cursor: pointer; transition: border 0.2s;" class="bid-row" data-bid="${encodedBid}">
                  <div>
                    <div style="font-weight: 600; color: var(--text-main);">${escapeHtml(b.vendor_name)} ${rankHtml}</div>
                    <div style="font-size: 0.85rem; color: var(--text-muted); margin-top: 4px;">AI Compliance Score: <strong style="color: ${scoreColor}">${b.compliance_score}%</strong></div>
                  </div>
                  <button class="btn-secondary-auth" style="padding: 0.5rem 1rem; pointer-events: none;">View Analysis</button>
                </div>
              `;
            });
            bidsHtml += `</div>`;
          } else {
            bidsHtml = `<div style="margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid var(--border-color); color: var(--text-muted); font-size: 0.9rem;">No bids received yet.</div>`;
          }
          
          card.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;">
              <h2 style="margin: 0; font-size: 1.4rem; color: var(--text-main);">${escapeHtml(t.title)}</h2>
              <span style="font-family: var(--font-mono); font-size: 0.8rem; background: var(--bg-body); padding: 4px 8px; border-radius: 4px; color: var(--text-muted);">ID: TEND-${t.id}</span>
            </div>
            <p style="color: var(--text-muted); font-size: 0.95rem; line-height: 1.5;">${escapeHtml(t.description)}</p>
            ${bidsHtml}
          `;
          
          tendersContainer.appendChild(card);
        });
        
        // Attach click listeners to bid rows
        document.querySelectorAll(".bid-row").forEach(row => {
          row.addEventListener("click", () => {
            const bid = JSON.parse(decodeURIComponent(row.getAttribute("data-bid")));
            showBidModal(bid);
          });
        });
        
      } catch (err) {
        tendersContainer.innerHTML = `<div style="color: red; text-align: center;">Error loading tenders.</div>`;
      }
    }
    
    function showBidModal(bid) {
      const report = bid.compliance_report || {};
      const issues = report.issues || [];
      const strengths = report.strengths || [];
      
      let issuesHtml = issues.length ? `<div><strong style="color:#f44336">Issues/Deviations:</strong><ul style="margin-top:0.5rem; padding-left:1.5rem; color:var(--text-muted);">` + issues.map(i => `<li>${escapeHtml(i)}</li>`).join('') + `</ul></div>` : "";
      let strengthsHtml = strengths.length ? `<div><strong style="color:var(--accent)">Strengths:</strong><ul style="margin-top:0.5rem; padding-left:1.5rem; color:var(--text-muted);">` + strengths.map(i => `<li>${escapeHtml(i)}</li>`).join('') + `</ul></div>` : "";
      
      modalContent.innerHTML = `
        <h2 style="margin-top: 0; font-size: 1.5rem;">Bid from <span class="highlight">${escapeHtml(bid.vendor_name)}</span></h2>
        <div style="display: flex; gap: 2rem; margin-top: 1rem; padding: 1.5rem; background: var(--bg-body); border-radius: 8px;">
          <div style="flex: 1;">
            <div style="font-size: 0.85rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1px;">AI Compliance Score</div>
            <div style="font-size: 3rem; font-weight: 800; color: ${bid.compliance_score >= 90 ? 'var(--accent)' : '#ff9800'};">${bid.compliance_score}<span style="font-size: 1.5rem;">%</span></div>
          </div>
          <div style="flex: 2; border-left: 1px solid var(--border-color); padding-left: 2rem;">
            <p style="color: var(--text-main); font-weight: 600; margin-top: 0;">${escapeHtml(report.summary || "No summary available.")}</p>
            ${strengthsHtml}
            ${issuesHtml}
          </div>
        </div>
        
        <div style="margin-top: 2rem;">
          <h3 style="font-size: 1.1rem; margin-bottom: 0.5rem;">Vendor's Specification Text</h3>
          <div style="background: var(--bg-input); padding: 1rem; border-radius: 8px; border: 1px solid var(--border-color); color: var(--text-muted); font-size: 0.95rem; white-space: pre-wrap;">${escapeHtml(bid.spec_text)}</div>
        </div>
      `;
      modal.style.display = "flex";
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
