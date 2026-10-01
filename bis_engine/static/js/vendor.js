"use strict";

(function () {
  document.addEventListener("DOMContentLoaded", () => {
    // Top Views
    const mainPortalView = document.getElementById("main-portal-view");
    const bidWorkspaceView = document.getElementById("bid-workspace-view");
    const btnBackToTenders = document.getElementById("btn-back-to-tenders");

    // Mode Tabs
    const tabAll = document.getElementById("tab-all-tenders");
    const tabVault = document.getElementById("tab-my-vault");
    const feedContainer = document.getElementById("feed-container");
    const vaultContainer = document.getElementById("vault-container");
    const vaultCountBadge = document.getElementById("vault-count-badge");
    const btnRefreshFeed = document.getElementById("btn-refresh-feed");

    // Workspace Elements
    const wsTenderIdBadge = document.getElementById("ws-tender-id-badge");
    const wsTenderBuyerBadge = document.getElementById("ws-tender-buyer-badge");
    const wsTenderTitle = document.getElementById("ws-tender-title");
    const wsTenderDesc = document.getElementById("ws-tender-desc");
    const wsCriteriaList = document.getElementById("ws-criteria-list");
    const wsCriteriaCounter = document.getElementById("ws-criteria-counter");
    const wsTenderId = document.getElementById("ws-tender-id");
    const wsBidAmount = document.getElementById("ws-bid-amount");
    const wsBidDelivery = document.getElementById("ws-bid-delivery");
    const wsSpecText = document.getElementById("ws-spec-text");
    const wsBidForm = document.getElementById("ws-bid-form");
    const wsBtnSubmit = document.getElementById("ws-btn-submit");
    const wsBtnAutofill = document.getElementById("ws-btn-autofill");

    // Vault Detail Modal Elements
    const vaultModal = document.getElementById("vault-detail-modal");
    const vaultModalClose = document.getElementById("vault-modal-close");
    const vaultModalBody = document.getElementById("vault-modal-body");

    let currentTender = null;

    function escapeHtml(unsafe) {
      if (unsafe == null) return "";
      return String(unsafe)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
    }

    function formatINR(val) {
      if (!val || isNaN(val)) return "₹ 0";
      return "₹ " + Number(val).toLocaleString("en-IN", { maximumFractionDigits: 2 });
    }

    function toast(msg, type = "info") {
      if (window.showToast) window.showToast(msg, type);
      else console.log(`[${type}] ${msg}`);
    }

    // --- Switch between Main Feed and Bid Workspace Interface ---
    function openBidWorkspace(tender) {
      currentTender = tender;
      wsTenderId.value = tender.id;
      wsTenderIdBadge.textContent = `TEND-${tender.id}`;
      wsTenderBuyerBadge.innerHTML = `Buyer: <strong>${escapeHtml(tender.customer_email || "Customer")}</strong>`;
      wsTenderTitle.textContent = tender.title;
      wsTenderDesc.textContent = tender.description || "No detailed requirements provided.";

      // Populate interactive criteria checklist
      const reqs = tender.requirements || [];
      wsCriteriaList.innerHTML = "";

      if (reqs.length > 0) {
        reqs.forEach((r) => {
          const itemDiv = document.createElement("label");
          itemDiv.style.display = "flex";
          itemDiv.style.alignItems = "flex-start";
          itemDiv.style.gap = "0.75rem";
          itemDiv.style.padding = "0.85rem 1rem";
          itemDiv.style.background = "var(--bg-body)";
          itemDiv.style.border = "1px solid var(--border-color)";
          itemDiv.style.borderRadius = "8px";
          itemDiv.style.cursor = "pointer";
          itemDiv.style.transition = "border-color 0.2s, background 0.2s";

          itemDiv.innerHTML = `
            <input type="checkbox" class="criteria-checkbox" data-text="${escapeHtml(r)}" checked style="margin-top: 3px; width: 18px; height: 18px; accent-color: var(--accent); cursor: pointer;">
            <div style="flex: 1;">
              <span style="font-size: 0.88rem; color: var(--text-main); font-weight: 600; line-height: 1.4; display: block;">${escapeHtml(r)}</span>
              <span style="font-size: 0.78rem; color: #22c55e; margin-top: 2px; display: block;">✓ We will fulfill this requirement</span>
            </div>
          `;

          wsCriteriaList.appendChild(itemDiv);
        });
        updateCriteriaCounter();
      } else {
        wsCriteriaList.innerHTML = `<div style="color:var(--text-muted); font-size:0.88rem; padding:1rem; background:var(--bg-body); border-radius:8px;">General procurement criteria applies.</div>`;
        wsCriteriaCounter.textContent = "All Criteria";
      }

      wsCriteriaList.querySelectorAll(".criteria-checkbox").forEach(cb => {
        cb.addEventListener("change", updateCriteriaCounter);
      });

      wsBidAmount.value = "";
      wsBidDelivery.value = "10";
      wsSpecText.value = "";

      mainPortalView.style.display = "none";
      bidWorkspaceView.style.display = "block";
      window.scrollTo({ top: 0, behavior: "smooth" });
      wsBidAmount.focus();
    }

    function closeBidWorkspace() {
      bidWorkspaceView.style.display = "none";
      mainPortalView.style.display = "block";
      currentTender = null;
      window.scrollTo({ top: 0, behavior: "smooth" });
    }

    function updateCriteriaCounter() {
      const allCb = wsCriteriaList.querySelectorAll(".criteria-checkbox");
      if (allCb.length === 0) return;
      const checkedCount = Array.from(allCb).filter(cb => cb.checked).length;
      wsCriteriaCounter.textContent = `${checkedCount} of ${allCb.length} Criteria Selected`;
      wsCriteriaCounter.style.color = checkedCount === allCb.length ? "#22c55e" : (checkedCount > 0 ? "#ff9800" : "#f44336");
    }

    if (btnBackToTenders) {
      btnBackToTenders.addEventListener("click", closeBidWorkspace);
    }

    // Auto-fill Sample Bid
    if (wsBtnAutofill) {
      wsBtnAutofill.addEventListener("click", () => {
        wsBidAmount.value = "345000";
        wsBidDelivery.value = "8";
        wsSpecText.value = `We are pleased to submit our formal technical proposal adhering strictly to Bureau of Indian Standards (BIS) specifications:
1. Product Certification: Certified with valid BIS ISI Mark under Mandatory Quality Control Order (QCO).
2. Material Grade & Specification: High-performance grade compliant with all physical, chemical, and mechanical test parameters.
3. Quality Assurance: Complete batch laboratory test reports and official Manufacturer's Test Certificate (MTC) provided with every dispatch.
4. Logistics & Delivery: Guaranteed direct site delivery within 8 business days in sealed tamper-proof packaging.
5. Warranty: Full 12-month manufacturer replacement warranty against any deviation.`;
        
        wsCriteriaList.querySelectorAll(".criteria-checkbox").forEach(cb => cb.checked = true);
        updateCriteriaCounter();
        toast("Sample bid proposal auto-filled!", "info");
      });
    }

    // Submit Bid Form Handler
    if (wsBidForm) {
      wsBidForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const tenderId = parseInt(wsTenderId.value, 10);
        const bidAmount = parseFloat(wsBidAmount.value) || 0;
        const deliveryDays = parseInt(wsBidDelivery.value, 10) || 7;
        const specText = wsSpecText.value.trim();

        if (!tenderId || !specText) {
          toast("Please enter your specification proposal.", "error");
          return;
        }

        const selectedReqs = Array.from(wsCriteriaList.querySelectorAll(".criteria-checkbox:checked"))
          .map(cb => cb.getAttribute("data-text"));

        const origText = wsBtnSubmit.textContent;
        wsBtnSubmit.disabled = true;
        wsBtnSubmit.textContent = "Analyzing Compliance with AI...";

        try {
          const res = await fetch("/api/bids/submit", {
            method: "POST",
            credentials: "same-origin",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              tender_id: tenderId,
              spec_text: specText,
              bid_amount: bidAmount,
              delivery_days: deliveryDays,
              declared_reqs: selectedReqs
            })
          });

          const data = await res.json().catch(() => ({}));
          if (!res.ok) throw new Error(data.detail || `Error submitting bid (${res.status})`);

          toast(`Bid Submitted! Placed in your vault as Pending. AI Score: ${data.score}%`, "success");
          closeBidWorkspace();
          
          // Switch to My Vault so vendor immediately sees their pending bid
          tabVault.click();
          await updateVaultCount();
        } catch (err) {
          toast(err.message, "error");
        } finally {
          wsBtnSubmit.disabled = false;
          wsBtnSubmit.textContent = origText;
        }
      });
    }

    // --- Modal for Detailed Vault View ---
    function openVaultModal(bid) {
      if (!vaultModal || !vaultModalBody) return;
      const score = bid.compliance_score || 0;
      const scoreCol = score >= 88 ? "var(--accent)" : (score >= 75 ? "#ff9800" : "#f44336");
      const report = bid.compliance_report || {};
      const strengths = report.strengths || [];
      const issues = report.issues || [];
      const breakdown = report.requirements_breakdown || [];
      const fulfilled = bid.fulfilled_reqs || report.fulfilled_count || 0;
      const total = bid.total_reqs || report.total_count || breakdown.length || 0;
      const rawStatus = (bid.status || "pending").toLowerCase();
      const isApproved = rawStatus === "approved" || rawStatus === "confirmed";
      const isRejected = rawStatus === "rejected";

      let statusBadge = "";
      if (isApproved) {
        statusBadge = `<span style="background: rgba(34, 197, 94, 0.2); color: #22c55e; border: 1px solid rgba(34, 197, 94, 0.4); padding: 4px 10px; border-radius: 6px; font-weight: 800; font-size: 0.85rem;">✅ Approved</span>`;
      } else if (isRejected) {
        statusBadge = `<span style="background: rgba(244, 67, 54, 0.2); color: #f44336; border: 1px solid rgba(244, 67, 54, 0.4); padding: 4px 10px; border-radius: 6px; font-weight: 700; font-size: 0.85rem;">❌ Not Selected</span>`;
      } else {
        statusBadge = `<span style="background: rgba(255, 230, 0, 0.2); color: var(--accent); border: 1px solid rgba(255, 230, 0, 0.4); padding: 4px 10px; border-radius: 6px; font-weight: 700; font-size: 0.85rem;">⏳ Pending</span>`;
      }

      let breakdownHtml = "";
      if (breakdown.length > 0) {
        breakdownHtml = `
          <div style="margin-top:1.2rem;">
            <h4 style="font-size:0.95rem;color:var(--text-main);margin-bottom:0.6rem;text-transform:uppercase;letter-spacing:0.5px;">Requirements Coverage Matrix</h4>
            <div style="display:flex;flex-direction:column;gap:0.5rem;">
              ${breakdown.map(item => {
                const isFulfilled = item.status === "Fulfilled";
                const badgeCol = isFulfilled ? "#22c55e" : (item.status === "Partial" ? "#ff9800" : "#f44336");
                const icon = isFulfilled ? "✅" : (item.status === "Partial" ? "⚠️" : "❌");
                return `
                  <div style="background:var(--bg-body);border:1px solid var(--border-color);padding:0.75rem 1rem;border-radius:8px;display:flex;justify-content:space-between;align-items:center;gap:1rem;">
                    <div>
                      <div style="font-size:0.88rem;color:var(--text-main);font-weight:600;">${icon} ${escapeHtml(item.requirement)}</div>
                      <div style="font-size:0.8rem;color:var(--text-muted);margin-top:2px;">${escapeHtml(item.notes)}</div>
                    </div>
                    <span style="font-size:0.75rem;font-weight:700;padding:2px 8px;border-radius:4px;color:${badgeCol};background:rgba(255,255,255,0.05);white-space:nowrap;">${item.status}</span>
                  </div>
                `;
              }).join("")}
            </div>
          </div>
        `;
      }

      vaultModalBody.innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <span style="font-family:var(--font-mono);font-size:0.8rem;background:var(--bg-body);padding:4px 8px;border-radius:4px;color:var(--accent);font-weight:600;">BID EVALUATION REPORT</span>
          ${statusBadge}
        </div>
        <h2 style="margin-top:0.6rem;margin-bottom:0.2rem;font-size:1.4rem;color:var(--text-main);">${escapeHtml(bid.tender_title || "Tender Proposal")}</h2>
        <span style="font-size:0.85rem;color:var(--text-muted);display:block;margin-bottom:0.8rem;">Tender ID: TEND-${bid.tender_id}</span>
        
        <!-- Key Metrics Cards -->
        <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(130px, 1fr));gap:0.8rem;margin:1rem 0;">
          <div style="background:var(--bg-body);padding:1rem;border-radius:8px;border:1px solid var(--border-color);text-align:center;">
            <div style="font-size:0.75rem;color:var(--text-muted);text-transform:uppercase;font-weight:700;">AI Score</div>
            <div style="font-size:2.2rem;font-weight:800;color:${scoreCol};line-height:1.2;">${score}%</div>
          </div>
          <div style="background:var(--bg-body);padding:1rem;border-radius:8px;border:1px solid var(--border-color);text-align:center;">
            <div style="font-size:0.75rem;color:var(--text-muted);text-transform:uppercase;font-weight:700;">Price Quote</div>
            <div style="font-size:1.3rem;font-weight:800;color:var(--text-main);margin-top:6px;">${formatINR(bid.bid_amount)}</div>
          </div>
          <div style="background:var(--bg-body);padding:1rem;border-radius:8px;border:1px solid var(--border-color);text-align:center;">
            <div style="font-size:0.75rem;color:var(--text-muted);text-transform:uppercase;font-weight:700;">Timeline</div>
            <div style="font-size:1.3rem;font-weight:800;color:var(--text-main);margin-top:6px;">${bid.delivery_days || 7} Days</div>
          </div>
          <div style="background:var(--bg-body);padding:1rem;border-radius:8px;border:1px solid var(--border-color);text-align:center;">
            <div style="font-size:0.75rem;color:var(--text-muted);text-transform:uppercase;font-weight:700;">Fulfillment</div>
            <div style="font-size:1.3rem;font-weight:800;color:#22c55e;margin-top:6px;">${fulfilled}/${total} Reqs</div>
          </div>
        </div>

        <div style="background:var(--bg-body);border:1px solid var(--border-color);padding:1.2rem;border-radius:8px;margin-bottom:1rem;">
          <div style="color:var(--text-main);font-weight:600;font-size:0.92rem;">${escapeHtml(report.summary || "Specification evaluated against BIS standards.")}</div>
          ${strengths.length ? `<div style="margin-top:0.6rem;"><strong style="color:var(--accent);font-size:0.85rem;">Strengths:</strong><ul style="margin:0.2rem 0 0 1.2rem;padding:0;color:var(--text-muted);font-size:0.85rem;">${strengths.map(s=>`<li>${escapeHtml(s)}</li>`).join("")}</ul></div>` : ""}
          ${issues.length ? `<div style="margin-top:0.6rem;"><strong style="color:#f44336;font-size:0.85rem;">Gaps / Risks:</strong><ul style="margin:0.2rem 0 0 1.2rem;padding:0;color:var(--text-muted);font-size:0.85rem;">${issues.map(i=>`<li>${escapeHtml(i)}</li>`).join("")}</ul></div>` : ""}
        </div>

        ${breakdownHtml}

        <div style="margin-top:1.2rem;">
          <h4 style="font-size:0.95rem;margin-bottom:0.4rem;color:var(--text-main);text-transform:uppercase;letter-spacing:0.5px;">Submitted Technical Proposal</h4>
          <div style="background:var(--bg-input);padding:1rem;border-radius:8px;border:1px solid var(--border-color);color:var(--text-muted);font-size:0.88rem;white-space:pre-wrap;max-height:150px;overflow-y:auto;line-height:1.5;">${escapeHtml(bid.spec_text || "")}</div>
        </div>
      `;

      vaultModal.style.display = "flex";
    }

    function closeVaultModal() {
      if (vaultModal) vaultModal.style.display = "none";
    }

    if (vaultModalClose) vaultModalClose.addEventListener("click", closeVaultModal);
    if (vaultModal) vaultModal.addEventListener("click", (e) => { if (e.target === vaultModal) closeVaultModal(); });

    // --- Tabs Switching ---
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

    if (btnRefreshFeed) {
      btnRefreshFeed.addEventListener("click", () => {
        if (tabAll.classList.contains("active")) loadTenders();
        else loadVault();
        toast("Refreshed", "info");
      });
    }

    // --- Load Active Tenders ---
    async function loadTenders() {
      feedContainer.innerHTML = `<div class="loader-pulse" style="margin: 3rem auto;"></div>`;
      try {
        const res = await fetch("/api/bids/tenders", { credentials: "same-origin" });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(data.detail || "Failed to load tenders");

        feedContainer.innerHTML = "";
        const tenders = data.tenders || [];

        if (tenders.length === 0) {
          feedContainer.innerHTML = `
            <div class="card" style="text-align: center; padding: 4rem 2rem; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 12px;">
              <div style="font-size: 2.5rem; margin-bottom: 0.8rem;">📋</div>
              <h3 style="margin: 0 0 0.5rem 0; color: var(--text-main);">No Active Tenders Found</h3>
              <p style="color: var(--text-muted); max-width: 450px; margin: 0 auto; font-size: 0.95rem;">
                When customers publish new tenders, they will appear here immediately for you to place bids on.
              </p>
            </div>
          `;
          return;
        }

        tenders.forEach(t => {
          const card = document.createElement("div");
          card.className = "card";
          card.style.background = "var(--bg-card)";
          card.style.border = "1px solid var(--border-color)";
          card.style.padding = "2rem";
          card.style.borderRadius = "12px";

          const hasBid = Boolean(t.has_bid);
          const reqs = t.requirements || [];

          const actionBtnHtml = hasBid
            ? `<div style="display:flex; align-items:center; gap:0.6rem;">
                 <span style="background: rgba(34, 197, 94, 0.15); color: #22c55e; border: 1px solid rgba(34, 197, 94, 0.3); padding: 0.5rem 1rem; border-radius: 6px; font-size: 0.85rem; font-weight: 700;">✓ Bid Submitted</span>
                 <button class="btn-secondary-auth btn-view-vault" style="padding: 0.5rem 0.9rem; font-size: 0.82rem; border-radius: 6px; border: 1px solid var(--border-color); background: var(--bg-body); cursor: pointer;">View in Vault</button>
               </div>`
            : `<button class="btn-primary btn-place-bid" data-tender='${escapeHtml(JSON.stringify(t))}' style="padding: 0.75rem 1.8rem; border-radius: 8px; font-weight: 800; font-size: 0.95rem; cursor: pointer; box-shadow: 0 4px 15px rgba(255,230,0,0.25);">
                 Place Bid 🚀
               </button>`;

          let reqsPreviewHtml = "";
          if (reqs.length > 0) {
            reqsPreviewHtml = `
              <div style="margin-top: 1rem; border-top: 1px dashed var(--border-color); padding-top: 0.8rem;">
                <div style="font-size: 0.78rem; text-transform: uppercase; letter-spacing: 1px; color: var(--accent); font-weight: 700; margin-bottom: 0.3rem;">Evaluation Criteria (${reqs.length}):</div>
                <div style="display:flex; flex-wrap:wrap; gap:0.5rem;">
                  ${reqs.map(r => `<span style="background:var(--bg-body); border:1px solid var(--border-color); padding:3px 8px; border-radius:4px; font-size:0.8rem; color:var(--text-muted);">✓ ${escapeHtml(r)}</span>`).join("")}
                </div>
              </div>
            `;
          }

          card.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem; flex-wrap: wrap; gap: 1rem;">
              <div>
                <h2 style="margin: 0 0 0.4rem 0; font-size: 1.35rem; color: var(--text-main); font-weight: 700;">${escapeHtml(t.title)}</h2>
                <div style="display: flex; gap: 0.8rem; align-items: center; flex-wrap: wrap;">
                  <span style="font-family: var(--font-mono); font-size: 0.8rem; background: var(--bg-body); padding: 4px 8px; border-radius: 4px; color: var(--text-muted); border: 1px solid var(--border-color);">TEND-${t.id}</span>
                  <span style="font-size: 0.85rem; color: var(--text-muted);">Buyer: <strong style="color: var(--text-main);">${escapeHtml(t.customer_email)}</strong></span>
                  ${t.budget ? `<span style="font-size: 0.85rem; color: var(--accent); font-weight:600;">Est. Budget: ${escapeHtml(t.budget)}</span>` : ""}
                </div>
              </div>
              <div>${actionBtnHtml}</div>
            </div>
            <div style="background: var(--bg-body); padding: 1.2rem; border-radius: 8px; border: 1px solid var(--border-color);">
              <div style="font-size: 0.78rem; text-transform: uppercase; letter-spacing: 1px; color: var(--text-muted); margin-bottom: 0.4rem; font-weight: 700;">Scope of Work:</div>
              <p style="color: var(--text-main); font-size: 0.92rem; line-height: 1.6; margin: 0; white-space: pre-wrap;">${escapeHtml(t.description)}</p>
              ${reqsPreviewHtml}
            </div>
          `;

          feedContainer.appendChild(card);
        });

        // Wire Place Bid buttons to open dedicated Bid Workspace Interface
        feedContainer.querySelectorAll(".btn-place-bid").forEach(btn => {
          btn.addEventListener("click", () => {
            try {
              const tenderData = JSON.parse(btn.getAttribute("data-tender"));
              openBidWorkspace(tenderData);
            } catch (e) {
              console.error(e);
            }
          });
        });

        // Wire View in Vault buttons
        feedContainer.querySelectorAll(".btn-view-vault").forEach(btn => {
          btn.addEventListener("click", () => tabVault.click());
        });

      } catch (err) {
        feedContainer.innerHTML = `
          <div style="color: #f44336; text-align: center; padding: 3rem; background: var(--bg-card); border-radius: 12px; border: 1px solid var(--border-color);">
            <p style="font-weight: 600; margin-bottom: 0.5rem;">Failed to load active tenders</p>
            <span style="font-size: 0.85rem; color: var(--text-muted);">${escapeHtml(err.message)}</span>
          </div>
        `;
      }
    }

    // --- Load Vendor Vault ---
    async function loadVault() {
      vaultContainer.innerHTML = `<div class="loader-pulse" style="margin: 3rem auto;"></div>`;
      try {
        const res = await fetch("/api/bids/vault", { credentials: "same-origin" });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(data.detail || "Failed to load bid vault");

        vaultContainer.innerHTML = "";
        const vault = data.vault || [];

        if (vaultCountBadge) {
          vaultCountBadge.textContent = vault.length;
          vaultCountBadge.style.display = vault.length > 0 ? "inline-block" : "none";
        }

        if (vault.length === 0) {
          vaultContainer.innerHTML = `
            <div class="card" style="text-align: center; padding: 4rem 2rem; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 12px;">
              <div style="font-size: 2.5rem; margin-bottom: 0.8rem;">🔒</div>
              <h3 style="margin: 0 0 0.5rem 0; color: var(--text-main);">Your Bid Vault is Empty</h3>
              <p style="color: var(--text-muted); max-width: 450px; margin: 0 auto 1.5rem auto; font-size: 0.95rem;">
                Submit your first bid with price quote and specifications under <strong>Active Tenders</strong> to track real-time AI evaluation and win probability.
              </p>
              <button class="btn-primary" id="btn-goto-tenders" style="padding: 0.7rem 1.6rem; border-radius: 8px; cursor:pointer;">Browse Active Tenders</button>
            </div>
          `;
          const btnGoto = document.getElementById("btn-goto-tenders");
          if (btnGoto) btnGoto.addEventListener("click", () => tabAll.click());
          return;
        }

        vault.forEach(b => {
          const card = document.createElement("div");
          card.className = "card";
          card.style.background = "var(--bg-card)";
          card.style.padding = "1.8rem";
          card.style.borderRadius = "12px";

          const rawStatus = (b.status || "pending").toLowerCase();
          const isApproved = rawStatus === "approved" || rawStatus === "confirmed";
          const isRejected = rawStatus === "rejected";

          // Card border and status banner based on status
          card.style.border = isApproved ? "2px solid #22c55e" : (isRejected ? "1px solid rgba(244,67,54,0.4)" : "1px solid var(--border-color)");

          let statusBadge = "";
          if (isApproved) {
            statusBadge = `<span style="background: rgba(34, 197, 94, 0.2); color: #22c55e; border: 1px solid rgba(34, 197, 94, 0.4); padding: 4px 10px; border-radius: 6px; font-weight: 800; font-size: 0.82rem;">✅ Approved</span>`;
          } else if (isRejected) {
            statusBadge = `<span style="background: rgba(244, 67, 54, 0.15); color: #f44336; border: 1px solid rgba(244, 67, 54, 0.3); padding: 4px 10px; border-radius: 6px; font-weight: 700; font-size: 0.82rem;">❌ Not Selected</span>`;
          } else {
            statusBadge = `<span style="background: rgba(255, 230, 0, 0.18); color: var(--accent); border: 1px solid rgba(255, 230, 0, 0.4); padding: 4px 10px; border-radius: 6px; font-weight: 700; font-size: 0.82rem;">⏳ Pending</span>`;
          }

          const score = b.compliance_score || 0;
          const scoreCol = score >= 88 ? "var(--accent)" : (score >= 75 ? "#ff9800" : "#f44336");
          const report = b.compliance_report || {};
          const fulfilled = b.fulfilled_reqs || report.fulfilled_count || 0;
          const total = b.total_reqs || report.total_count || 0;
          const encBid = encodeURIComponent(JSON.stringify(b));

          card.innerHTML = `
            <div style="display: flex; gap: 1.8rem; flex-wrap: wrap;">
              <div style="flex: 1; min-width: 150px; display: flex; flex-direction: column; justify-content: center; align-items: center; background: var(--bg-body); padding: 1.2rem; border-radius: 8px; border: 1px solid var(--border-color); text-align: center;">
                <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1px; font-weight: 700;">AI Compliance</div>
                <div style="font-size: 2.6rem; font-weight: 800; color: ${scoreCol}; line-height: 1.1; margin: 0.2rem 0;">${score}<span style="font-size: 1.2rem;">%</span></div>
                <span style="font-size: 0.8rem; color: #22c55e; font-weight: 600;">${fulfilled}/${total} Reqs Met</span>
              </div>
              <div style="flex: 3; min-width: 260px;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.6rem; gap: 1rem; flex-wrap: wrap;">
                  <div>
                    <div style="display:flex; align-items:center; gap:0.6rem; flex-wrap:wrap; margin-bottom:0.3rem;">
                      <h3 style="margin: 0; font-size: 1.25rem; color: var(--text-main); font-weight: 700;">Tender: ${escapeHtml(b.tender_title)}</h3>
                      ${statusBadge}
                    </div>
                    <div style="display:flex; gap:0.8rem; font-size:0.85rem; color:var(--text-muted);">
                      <span>💰 Quote: <strong style="color:var(--text-main);">${formatINR(b.bid_amount)}</strong></span>
                      <span>⏱ Delivery: <strong style="color:var(--text-main);">${b.delivery_days || 7} Days</strong></span>
                    </div>
                  </div>
                  <button class="btn-secondary-auth btn-view-analysis" data-bid="${encBid}" style="padding: 0.45rem 1rem; font-size: 0.82rem; border-radius: 6px; border: 1px solid var(--border-color); background: var(--bg-body); cursor: pointer; white-space: nowrap;">
                    View Analysis ↗
                  </button>
                </div>
                <p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 0.8rem; line-height: 1.5;">${escapeHtml(report.summary || "Specification evaluated against BIS standards.")}</p>
                <div style="font-size: 0.85rem; color: var(--text-main); background: var(--bg-body); padding: 0.75rem 1rem; border-radius: 6px; border: 1px solid var(--border-color);">
                  <strong style="color: var(--text-muted); font-size: 0.78rem; text-transform: uppercase;">Your Proposal Extract:</strong>
                  <div style="color: var(--text-main); margin-top: 4px; line-height: 1.4;">${escapeHtml(b.spec_text ? (b.spec_text.substring(0, 160) + (b.spec_text.length > 160 ? "…" : "")) : "")}</div>
                </div>
              </div>
            </div>
          `;

          vaultContainer.appendChild(card);
        });

        // Wire View Analysis buttons
        vaultContainer.querySelectorAll(".btn-view-analysis").forEach(btn => {
          btn.addEventListener("click", () => {
            try {
              const bidData = JSON.parse(decodeURIComponent(btn.getAttribute("data-bid")));
              openVaultModal(bidData);
            } catch (e) {
              console.error(e);
            }
          });
        });

      } catch (err) {
        vaultContainer.innerHTML = `
          <div style="color: #f44336; text-align: center; padding: 3rem; background: var(--bg-card); border-radius: 12px; border: 1px solid var(--border-color);">
            <p style="font-weight: 600; margin-bottom: 0.5rem;">Failed to load vault</p>
            <span style="font-size: 0.85rem; color: var(--text-muted);">${escapeHtml(err.message)}</span>
          </div>
        `;
      }
    }

    async function updateVaultCount() {
      try {
        const res = await fetch("/api/bids/vault", { credentials: "same-origin" });
        const data = await res.json().catch(() => ({}));
        if (res.ok && data.vault && vaultCountBadge) {
          vaultCountBadge.textContent = data.vault.length;
          vaultCountBadge.style.display = data.vault.length > 0 ? "inline-block" : "none";
        }
      } catch (e) {}
    }

    // Init
    loadTenders();
    updateVaultCount();
  });
})();
