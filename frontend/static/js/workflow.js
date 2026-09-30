let currentWorkflowStep = 1;
const completedWorkflowSteps = new Set();

function markStepDone(stepNum) {
  completedWorkflowSteps.add(stepNum);
  renderStepTicks();
}

function renderStepTicks() {
  document.querySelectorAll(".workflow-step").forEach((el, idx) => {
    const num = idx + 1;
    const isActive = (num === currentWorkflowStep);
    const isCompleted = completedWorkflowSteps.has(num) && !isActive;

    el.classList.toggle("active", isActive);
    el.classList.toggle("completed", isCompleted);

    const numEl = el.querySelector(".workflow-step-num");
    const badgeEl = el.querySelector(".workflow-step-badge");

    if (numEl) {
      if (isCompleted) {
        numEl.textContent = "✓";
        numEl.setAttribute("aria-label", `Step ${num} completed`);
      } else {
        numEl.textContent = String(num);
        numEl.removeAttribute("aria-label");
      }
    }

    if (badgeEl) {
      badgeEl.style.display = isCompleted ? "inline-flex" : "none";
      badgeEl.textContent = "✓";
      badgeEl.setAttribute("title", `Step ${num} Completed`);
    }
  });
}

function initTouchDragScroll(containerId) {
  const container = document.getElementById(containerId) || (typeof containerId === 'string' && containerId.startsWith('.') ? document.querySelector(containerId) : null);
  if (!container) return;

  let isDown = false;
  let startX = 0;
  let scrollLeft = 0;

  // Touch drag support for mobile/tablet touchscreens
  let touchStartX = 0;
  let touchStartScroll = 0;

  container.addEventListener('touchstart', (e) => {
    if (e.touches.length === 1) {
      touchStartX = e.touches[0].pageX;
      touchStartScroll = container.scrollLeft;
    }
  }, { passive: true });

  container.addEventListener('touchmove', (e) => {
    if (e.touches.length === 1) {
      const touchX = e.touches[0].pageX;
      const walk = (touchX - touchStartX) * 1.2;
      container.scrollLeft = touchStartScroll - walk;
    }
  }, { passive: true });

  // Mouse / pointer drag support for desktop/tablet emulation
  container.addEventListener('mousedown', (e) => {
    if (e.target.closest('button, a, input, select, textarea')) return;
    isDown = true;
    container.classList.add('touch-dragging');
    startX = e.pageX - container.offsetLeft;
    scrollLeft = container.scrollLeft;
  });

  window.addEventListener('mouseup', () => {
    if (isDown) {
      isDown = false;
      container.classList.remove('touch-dragging');
    }
  });

  container.addEventListener('mousemove', (e) => {
    if (!isDown) return;
    e.preventDefault();
    const x = e.pageX - container.offsetLeft;
    const walk = (x - startX) * 1.5;
    container.scrollLeft = scrollLeft - walk;
  });
}

// Seller questions come only from checks that actually ran on this property.
function collectSellerQuestions() {
  const en = currentLanguage === 'en';
  const parts = [];
  const deed = window._lastDeedData;
  if (deed) {
    const d = (en && deed.whatsapp_draft_en) ? deed.whatsapp_draft_en : deed.whatsapp_draft;
    if (d) parts.push(d);
  }
  const ec = window._lastEcData;
  if (ec) {
    const e = (en && ec.whatsapp_inquiry_en) ? ec.whatsapp_inquiry_en : ec.whatsapp_inquiry;
    if (e) parts.push(e);
  }
  const db = window._lastDatabankData;
  if (db) {
    const q = (en && db.whatsapp_inquiry_en) ? db.whatsapp_inquiry_en : db.whatsapp_inquiry;
    if (q) parts.push(q);
  }
  const elev = window.currentElevationData;
  if (elev && document.getElementById("map-hud")?.style.display !== "none") {
    const f = (en && elev.whatsapp_inquiry_for_seller_en) ? elev.whatsapp_inquiry_for_seller_en : elev.whatsapp_inquiry_for_seller;
    if (f) parts.push(f);
  }
  return parts;
}

function ensureStep4ActionCard() {
  const existingCard = document.querySelector(".step4-action-banner");
  if (existingCard) existingCard.closest(".msg")?.remove();

  const isMl = currentLanguage === 'ml';
  const parts = collectSellerQuestions();
  if (!parts.length) {
    appendMsg("agent", `
      <div class="step4-action-banner" style="font-size: var(--fs-14);">
        ${isMl
          ? 'ചോദിക്കാൻ ഇനിയും ഒന്നുമില്ല. ആധാരമോ EC-യോ സ്കാൻ ചെയ്യുക, അല്ലെങ്കിൽ മാപ്പിൽ പ്ലോട്ട് അടയാളപ്പെടുത്തുക; ആ പരിശോധനകളിൽ കണ്ടതിൽ നിന്നാണ് സന്ദേശം തയ്യാറാക്കുന്നത്.'
          : 'Nothing to ask yet. Scan the deed or EC, or pin the plot on the map. The message is built from what those checks find.'}
      </div>
    `);
    return;
  }

  const waText = parts.join("\n\n");
  const waEncoded = encodeURIComponent(waText);
  appendMsg("agent", `
    <div class="step4-action-banner" style="background:#eef5f5; border:1px solid #a8cfd1; border-radius:10px; padding:12px; margin-bottom:12px;">
      <div class="whatsapp-card">
        <div class="whatsapp-header">
          <span class="whatsapp-title">${isMl ? 'വിൽപ്പനക്കാരനോട് ചോദിക്കേണ്ടത് (WhatsApp):' : 'WhatsApp message for the seller / broker:'}</span>
          <div class="whatsapp-actions">
            <button class="copy-btn" onclick="copyWhatsApp(this); markStepDone(4);">Copy Draft</button>
            <a class="wa-direct-btn" href="https://api.whatsapp.com/send?text=${waEncoded}" target="_blank" rel="noopener noreferrer" onclick="markStepDone(4)">WhatsApp</a>
          </div>
        </div>
        <div class="whatsapp-text" style="white-space:pre-line;">${escapeHtml(waText)}</div>
      </div>
      <div style="display:flex; gap:8px; margin-top:10px; flex-wrap:wrap;">
        <button class="export-report-btn" onclick="toggleChecklist(true)" style="background:#990f3d;">Open Field Checklist</button>
        ${window._lastDeedData ? `<button class="export-report-btn" onclick="exportCurrentDeedDossier(); markStepDone(4);" style="background:#262a33;">Export Deed Dossier (PDF)</button>` : ''}
      </div>
    </div>
  `);
}

function onDemarcatePlotChip() {
  setViewMode('split');
  setMapTool('plot');
  const hud = document.getElementById("map-hud");
  if (hud && hud.classList.contains("collapsed")) toggleHUD();
}

function onCheckElevationChip() {
  setViewMode('split');
  const hud = document.getElementById("map-hud");
  if (hud && hud.classList.contains("collapsed")) toggleHUD();
  const elevBox = document.getElementById("hud-elevation-box");
  if (elevBox) {
    elevBox.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    elevBox.style.transition = 'outline 0.3s ease';
    elevBox.style.outline = '2px solid #990f3d';
    setTimeout(() => { elevBox.style.outline = 'none'; }, 2000);
  }
}

function toggleSatelliteHybridView() {
  setViewMode('split');
  const layerSel = document.getElementById("layer-select");
  if (!layerSel) return;
  const nextLayer = layerSel.value === "google-hybrid" ? "google-satellite" : "google-hybrid";
  layerSel.value = nextLayer;
  switchMapLayer(nextLayer);
}

function triggerWhatsAppInquiry() {
  onStepClick(4);
}

// Highlights the step the user is on. Called by the code as work moves along.
function setWorkflowStep(stepNum) {
  if (stepNum < 1 || stepNum > 4) return;
  currentWorkflowStep = stepNum;
  renderStepTicks();
  if (stepNum > 1) collapseStartCard();
}

// A click on a step does that step's job for the current property.
function onStepClick(stepNum) {
  const isMl = currentLanguage === "ml";
  setWorkflowStep(stepNum);
  if (stepNum === 1) {
    const card = document.getElementById("deed-dropzone-container");
    if (card) {
      card.classList.remove("collapsed");
      card.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  } else if (stepNum === 2) {
    if (window._lastDeedData) {
      auditPriorDeedsOfScannedDeed();
    } else {
      appendMsg("agent", isMl
        ? `മുന്നാധാരങ്ങളും 30 വർഷത്തെ EC-യും അപ്‌ലോഡ് ചെയ്യുക, അല്ലെങ്കിൽ ആദ്യം ഇപ്പോഴത്തെ ആധാരം സ്കാൻ ചെയ്യുക.${DEMO_MODE ? `<br><button type="button" class="link-btn" onclick="openOwnershipTimeline('aluva_broken')">മാതൃക: 3 പിഴവുകളുള്ള ശൃംഖല</button>` : ""}`
        : `Upload the prior deeds and the 30-year EC, or scan the current deed first.${DEMO_MODE ? `<br><button type="button" class="link-btn" onclick="openOwnershipTimeline('aluva_broken')">See a sample chain with 3 defects</button>` : ""}`);
    }
  } else if (stepNum === 3) {
    if (window.innerWidth < 768) setViewMode("map");
    if (typeof map !== "undefined" && map) setTimeout(() => map.invalidateSize(), 200);
    document.getElementById("map-search")?.focus();
  } else if (stepNum === 4) {
    ensureStep4ActionCard();
    setTimeout(() => {
      document.querySelector(".step4-action-banner")?.scrollIntoView({ behavior: "smooth", block: "center" });
    }, 100);
  }
}

// The start card and the suggestions step aside once the user has begun.
function collapseStartCard() {
  document.getElementById("deed-dropzone-container")?.classList.add("collapsed");
  document.getElementById("suggestions")?.classList.add("hidden");
}

async function exportDossierPDF(preset = 'aluva_broken') {
  try {
    const res = await fetch(`/api/timeline_demo?preset=${preset}&lang=${currentLanguage}`);
    if (!res.ok) throw new Error("Could not fetch audit data");
    const data = await res.json();
    const pdfRes = await fetch('/api/export_dossier', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!pdfRes.ok) throw new Error("Failed to generate PDF dossier");
    const blob = await pdfRes.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `kandezhuthu_legal_audit_${preset}.pdf`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  } catch (err) {
    alert("Could not generate PDF dossier: " + err.message);
  }
}

async function exportCurrentDeedDossier() {
  if (!window._lastDeedData) {
    alert(currentLanguage === "ml" ? "ആദ്യം ഒരു ആധാരം സ്കാൻ ചെയ്യുക." : "Scan a deed first.");
    return;
  }
  try {
    const pdfRes = await fetch('/api/export_dossier', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(window._lastDeedData)
    });
    if (!pdfRes.ok) throw new Error("Failed to generate PDF dossier");
    const blob = await pdfRes.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const docNo = (window._lastDeedData.metadata?.document_number || "deed").replace(/[\/\s]/g, "_");
    a.download = `kandezhuthu_deed_dossier_${docNo}.pdf`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  } catch (err) {
    alert("Could not generate PDF dossier: " + err.message);
  }
}

function sendQuickPrompt(promptText) {
  const inp = document.getElementById("input");
  const frm = document.getElementById("form");
  if (inp && frm) {
    inp.value = promptText;
    frm.dispatchEvent(new Event("submit", { cancelable: true }));
  }
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = input.value.trim();
  if (!text) return;
  collapseStartCard();

  appendMsg("user", text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"));
  input.value = "";
  input.style.height = "48px";
  sendBtn.disabled = true;

  const loadingBubble = appendMsg("agent", `
    <div class="typing-indicator">
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
      <span style="font-size: var(--fs-14); color:#990f3d; margin-left:6px; font-weight:500;">
        ${(TRANSLATIONS[currentLanguage] || TRANSLATIONS.en).typingAnalysis}
      </span>
    </div>
  `);

  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, language: currentLanguage, user_id: "web-user" }),
    });

    const data = await res.json();
    let replyText = "";
    if (data.parts && data.parts.length) {
      replyText = data.parts.map(p => p.text || "").join("\n\n");
    } else {
      replyText = "No response was returned by the agent.";
    }

    loadingBubble.innerHTML = formatMarkdown(replyText);
  } catch (err) {
    loadingBubble.innerHTML = `<span style="color:red;">Error connecting to Kandezhuthu auditor: ${err.message}</span>`;
  } finally {
    sendBtn.disabled = false;
    log.scrollTop = log.scrollHeight;
  }
});
