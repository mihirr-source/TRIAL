"use strict";

(function () {
  document.addEventListener("DOMContentLoaded", () => {
    const btnNewTender     = document.getElementById("btn-new-tender");
    const formContainer    = document.getElementById("new-tender-form-container");
    const btnCancel        = document.getElementById("btn-cancel-tender");
    const btnAutofill      = document.getElementById("btn-autofill-tender");
    const btnRefresh       = document.getElementById("btn-refresh-customer");
    const form             = document.getElementById("new-tender-form");
    const tendersContainer = document.getElementById("tenders-container");
    const modal            = document.getElementById("bid-modal");
    const modalClose       = document.getElementById("bid-modal-close");
    const modalContent     = document.getElementById("bid-modal-content");

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

    // --- Show / hide bid-detail modal ---
    function openModal(bid) {
      if (!modal || !modalContent) return;
      const report    = bid.compliance_report || {};
      const issues    = report.issues    || [];
      const strengths = report.strengths || [];
      const breakdown = report.requirements_breakdown || [];
      const score     = bid.compliance_score || 0;
      const scoreCol  = score >= 88 ? "var(--accent)" : (score >= 75 ? "#ff9800" : "#f44336");
      const fulfilled = bid.fulfilled_reqs || report.fulfilled_count || 0;
      const total     = bid.total_reqs || report.total_count || breakdown.length || 0;

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

      modalContent.innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <span style="font-family:var(--font-mono);font-size:0.8rem;background:var(--bg-body);padding:4px 8px;border-radius:4px;color:var(--accent);font-weight:600;">TECHNICAL BID EVALUATION</span>
          <span style="font-size:0.85rem;color:var(--text-muted);">${escapeHtml(bid.vendor_email || "")}</span>
        </div>
        <h2 style="margin-top:0.6rem;margin-bottom:0.4rem;font-size:1.4rem;color:var(--text-main);">Bid from <span class="highlight">${escapeHtml(bid.vendor_name || "Vendor")}</span></h2>
        
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
            <div style="font-size:0.75rem;color:var(--text-muted);text-transform:uppercase;font-weight:700;">Requirements</div>
            <div style="font-size:1.3rem;font-weight:800;color:#22c55e;margin-top:6px;">${fulfilled}/${total} Met</div>
          </div>
        </div>

        <div style="background:var(--bg-body);border:1px solid var(--border-color);padding:1.2rem;border-radius:8px;margin-bottom:1rem;">
          <div style="color:var(--text-main);font-weight:600;font-size:0.92rem;">${escapeHtml(report.summary || "Specification evaluated against BIS standards.")}</div>
          ${strengths.length ? `<div style="margin-top:0.6rem;"><strong style="color:var(--accent);font-size:0.85rem;">Strengths:</strong><ul style="margin:0.2rem 0 0 1.2rem;padding:0;color:var(--text-muted);font-size:0.85rem;">${strengths.map(s=>`<li>${escapeHtml(s)}</li>`).join("")}</ul></div>` : ""}
          ${issues.length ? `<div style="margin-top:0.6rem;"><strong style="color:#f44336;font-size:0.85rem;">Gaps / Risks:</strong><ul style="margin:0.2rem 0 0 1.2rem;padding:0;color:var(--text-muted);font-size:0.85rem;">${issues.map(i=>`<li>${escapeHtml(i)}</li>`).join("")}</ul></div>` : ""}
        </div>

        ${breakdownHtml}

        <div style="margin-top:1.2rem;">
          <h4 style="font-size:0.95rem;margin-bottom:0.4rem;color:var(--text-main);text-transform:uppercase;letter-spacing:0.5px;">Vendor Specification Submission</h4>
          <div style="background:var(--bg-input);padding:1rem;border-radius:8px;border:1px solid var(--border-color);color:var(--text-muted);font-size:0.88rem;white-space:pre-wrap;max-height:160px;overflow-y:auto;line-height:1.5;">${escapeHtml(bid.spec_text || "")}</div>
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

    if (btnRefresh) {
      btnRefresh.addEventListener("click", () => {
        loadTenders();
        toast("Refreshed tenders", "info");
      });
    }

    if (btnAutofill) {
      btnAutofill.addEventListener("click", () => {
        document.getElementById("tender-title").value = "Procurement of 500 MT Structural Steel Sections conforming to IS 2062:2011";
        document.getElementById("tender-budget").value = "₹ 25,00,000";
        document.getElementById("tender-desc").value = `Required structural steel beams, channels, and angles for infrastructure project:
- Standards: Must conform strictly to BIS IS 2062:2011 (Grade E250 Quality A/BR)
- Certification: Mandatory valid BIS ISI mark license under Quality Control Order (QCO)
- Testing: Mill Test Certificate (MTC) and NABL accredited laboratory tensile/bend test reports for each batch
- Delivery Schedule: Direct delivery to project warehouse within 14 business days
- Inspection: Pre-dispatch physical inspection by third-party agency`;
        toast("Sample tender requirements loaded!", "info");
      });
    }

    if (form) {
      form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const title  = document.getElementById("tender-title").value.trim();
        const budget = document.getElementById("tender-budget").value.trim();
        const desc   = document.getElementById("tender-desc").value.trim();
        
        if (!title || !desc) {
          toast("Please fill in all required fields.", "error");
          return;
        }

        const submitBtn = document.getElementById("btn-submit-tender");
        const origText  = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = "Publishing…";

        try {
          const res = await fetch("/api/bids/tenders", {
            method: "POST",
            credentials: "same-origin",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ title, description: desc, budget: budget }),
          });
          const json = await res.json().catch(() => ({}));
          if (!res.ok) throw new Error(json.detail || `Error ${res.status}`);

          toast("Tender published successfully! Now visible in Vendor Portal.", "success");
          form.reset();
          formContainer.style.display = "none";
          await loadTenders();
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
      tendersContainer.innerHTML = `<div class="loader-pulse" style="margin:3rem auto;"></div>`;
      try {
        const res = await fetch("/api/bids/tenders", { credentials: "same-origin" });
        const json = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(json.detail || "Failed to load tenders");

        tendersContainer.innerHTML = "";
        const tenders = json.tenders || [];

        if (tenders.length === 0) {
          tendersContainer.innerHTML = `
            <div class="card" style="text-align:center;padding:4rem 2rem;background:var(--bg-card);border:1px solid var(--border-color);border-radius:12px;">
              <div style="font-size:2.5rem;margin-bottom:0.8rem;">📢</div>
              <h3 style="margin:0 0 0.5rem 0;color:var(--text-main);">No Tenders Published Yet</h3>
              <p style="color:var(--text-muted);max-width:450px;margin:0 auto 1.5rem auto;font-size:0.95rem;">
                Click <strong>+ Create Tender</strong> to post your first procurement scope. Registered vendors will be able to submit competitive bids.
              </p>
            </div>
          `;
          return;
        }

        tenders.forEach(t => {
          const card = document.createElement("div");
          card.className = "card";
          Object.assign(card.style, {
            background: "var(--bg-card)",
            border: "1px solid var(--border-color)",
            padding: "2rem",
            borderRadius: "12px",
            boxShadow: "0 4px 20px rgba(0,0,0,0.15)"
          });

          const bids = t.bids || [];
          const reqs = t.requirements || [];

          let bidsHtml = "";
          if (bids.length > 0) {
            // Sort bids by compliance score descending
            const sortedBids = [...bids].sort((a, b) => (b.compliance_score || 0) - (a.compliance_score || 0));

            const rows = sortedBids.map((b, idx) => {
              const score = b.compliance_score || 0;
              const scoreCol = score >= 88 ? "var(--accent)" : (score >= 75 ? "#ff9800" : "#f44336");
              const topBadge = idx === 0 
                ? `<span style="background:var(--accent);color:#000;padding:2px 8px;border-radius:4px;font-size:0.72rem;font-weight:800;letter-spacing:0.5px;margin-left:8px;">★ BEST BID</span>` 
                : "";
              const enc = encodeURIComponent(JSON.stringify(b));
              const rep = b.compliance_report || {};
              const fulfilled = b.fulfilled_reqs || rep.fulfilled_count || 0;
              const total = b.total_reqs || rep.total_count || reqs.length || 0;

              return `
                <div class="bid-row" data-bid="${enc}" style="background:var(--bg-body);border:1px solid var(--border-color);padding:1.2rem;border-radius:8px;display:flex;justify-content:space-between;align-items:center;cursor:pointer;transition:all .2s;flex-wrap:wrap;gap:1rem;">
                  <div style="display:flex;gap:1.5rem;align-items:center;flex-wrap:wrap;">
                    <div>
                      <div style="font-weight:700;color:var(--text-main);font-size:1.05rem;">
                        ${escapeHtml(b.vendor_name || "Vendor")} ${topBadge}
                      </div>
                      <div style="font-size:0.8rem;color:var(--text-muted);margin-top:2px;">${escapeHtml(b.vendor_email || "")}</div>
                    </div>
                    <div style="display:flex;gap:1.2rem;border-left:1px solid var(--border-color);padding-left:1.2rem;font-size:0.88rem;">
                      <div>
                        <span style="color:var(--text-muted);font-size:0.75rem;display:block;text-transform:uppercase;">Quote</span>
                        <strong style="color:var(--text-main);">${formatINR(b.bid_amount)}</strong>
                      </div>
                      <div>
                        <span style="color:var(--text-muted);font-size:0.75rem;display:block;text-transform:uppercase;">Delivery</span>
                        <strong style="color:var(--text-main);">${b.delivery_days || 7} Days</strong>
                      </div>
                      <div>
                        <span style="color:var(--text-muted);font-size:0.75rem;display:block;text-transform:uppercase;">Fulfillment</span>
                        <strong style="color:#22c55e;">${fulfilled}/${total} Met</strong>
                      </div>
                      <div>
                        <span style="color:var(--text-muted);font-size:0.75rem;display:block;text-transform:uppercase;">AI Score</span>
                        <strong style="color:${scoreCol};font-weight:800;">${score}%</strong>
                      </div>
                    </div>
                  </div>
                  <button class="btn-secondary-auth" style="padding:0.5rem 1rem;font-size:0.82rem;border-radius:6px;border:1px solid var(--border-color);background:var(--bg-card);pointer-events:none;">
                    View Evaluation ↗
                  </button>
                </div>
              `;
            }).join("");

            bidsHtml = `
              <h3 style="margin-top:1.8rem;margin-bottom:1rem;font-size:1.15rem;color:var(--text-main);border-top:1px solid var(--border-color);padding-top:1.2rem;display:flex;justify-content:space-between;align-items:center;">
                <span>Vendor Bids Received (${bids.length})</span>
                <span style="font-size:0.8rem;color:var(--text-muted);font-weight:normal;">Ranked by AI Compliance & Scope Match</span>
              </h3>
              <div style="display:flex;flex-direction:column;gap:0.8rem;">${rows}</div>
            `;
          } else {
            bidsHtml = `
              <div style="margin-top:1.5rem;padding-top:1.2rem;border-top:1px solid var(--border-color);color:var(--text-muted);font-size:0.9rem;display:flex;align-items:center;gap:0.5rem;">
                <span>⏳ Awaiting vendor submissions. Bids will be evaluated by AI in real-time.</span>
              </div>
            `;
          }

          let reqsPreviewHtml = "";
          if (reqs.length > 0) {
            reqsPreviewHtml = `
              <div style="margin-top:0.8rem;border-top:1px dashed var(--border-color);padding-top:0.6rem;">
                <div style="font-size:0.75rem;text-transform:uppercase;letter-spacing:1px;color:var(--accent);font-weight:700;margin-bottom:0.3rem;">Evaluation Criteria (${reqs.length}):</div>
                <div style="display:flex;flex-wrap:wrap;gap:0.4rem;">
                  ${reqs.map(r => `<span style="background:var(--bg-body);border:1px solid var(--border-color);padding:2px 7px;border-radius:4px;font-size:0.78rem;color:var(--text-muted);">✓ ${escapeHtml(r)}</span>`).join("")}
                </div>
              </div>
            `;
          }

          card.innerHTML = `
            <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:1rem;gap:1rem;flex-wrap:wrap;">
              <div>
                <h2 style="margin:0 0 0.3rem 0;font-size:1.35rem;color:var(--text-main);font-weight:700;">${escapeHtml(t.title)}</h2>
                <div style="display:flex;gap:0.8rem;align-items:center;flex-wrap:wrap;font-size:0.85rem;color:var(--text-muted);">
                  <span style="font-family:var(--font-mono);font-size:0.8rem;background:var(--bg-body);padding:3px 7px;border-radius:4px;border:1px solid var(--border-color);">TEND-${t.id}</span>
                  ${t.budget ? `<span>Est. Budget: <strong style="color:var(--accent);">${escapeHtml(t.budget)}</strong></span>` : ""}
                  <span>&bull; Status: <span style="color:#22c55e;font-weight:600;">ACTIVE</span></span>
                </div>
              </div>
              <span style="background:var(--bg-body);border:1px solid var(--border-color);padding:4px 10px;border-radius:6px;font-size:0.82rem;color:var(--text-muted);">
                ${bids.length} ${bids.length === 1 ? 'Bid' : 'Bids'}
              </span>
            </div>
            <div style="background:var(--bg-body);padding:1.2rem;border-radius:8px;border:1px solid var(--border-color);">
              <div style="font-size:0.75rem;text-transform:uppercase;letter-spacing:1px;color:var(--text-muted);margin-bottom:0.3rem;font-weight:700;">Tender Scope:</div>
              <p style="color:var(--text-main);font-size:0.92rem;line-height:1.6;margin:0;white-space:pre-wrap;">${escapeHtml(t.description)}</p>
              ${reqsPreviewHtml}
            </div>
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
            } catch (e) {
              console.error("Bid parse error:", e);
            }
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
