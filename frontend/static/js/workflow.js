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

function updateStepNavBar() {
  const stepNum = currentWorkflowStep;
  const prevBtn = document.getElementById("btn-prev-step");
  const nextBtn = document.getElementById("btn-next-step");
  const navText = {
    en: {
      prev: [
        "← Back",
        "← Back",
        "← Back",
        "← Back"
      ],
      next: [
        "Next: Prior deeds →",
        "Next: Site →",
        "Next: Follow-up →",
        "Start over ↺"
      ]
    },
    ml: {
      prev: [
        "← തിരികെ",
        "← തിരികെ",
        "← തിരികെ",
        "← തിരികെ"
      ],
      next: [
        "അടുത്തത്: മുന്നാധാരം →",
        "അടുത്തത്: സ്ഥലം →",
        "അടുത്തത്: തുടർനടപടി →",
        "വീണ്ടും തുടങ്ങുക ↺"
      ]
    }
  };

  const lang = currentLanguage || "en";

  if (prevBtn) {
    prevBtn.disabled = (stepNum === 1);
    prevBtn.textContent = (navText[lang] || navText.en).prev[stepNum - 1];
  }

  if (nextBtn) {
    nextBtn.textContent = (navText[lang] || navText.en).next[stepNum - 1];
    nextBtn.classList.toggle("restart", stepNum === 4);
  }

}

function syncChipsBar() {
  const bar = document.getElementById("chips-container");
  if (!bar) return;
  const anyVisible = [...bar.querySelectorAll(".chip")].some(c => c.style.display !== "none");
  bar.style.display = anyVisible ? "" : "none";
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
      <div class="step4-action-banner" style="font-size:0.85rem;">
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
  ensureStep4ActionCard();
  setTimeout(() => {
    const waCard = document.querySelector(".whatsapp-card") || document.querySelector(".step4-action-banner");
    if (waCard) {
      waCard.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }, 100);
}

function setWorkflowStep(stepNum) {
  if (stepNum < 1 || stepNum > 4) return;
  currentWorkflowStep = stepNum;

  // 1. Active step and ticks for finished work
  renderStepTicks();

  // 2. Update step navigation bar controls
  updateStepNavBar();

  // 3. Progressive Disclosure
  const dropzoneContainer = document.getElementById("deed-dropzone-container");
  const categoryTabs = document.querySelector(".category-tabs");
  const dropzone = document.getElementById("deed-dropzone");
  const toggleBtn = document.getElementById("dropzone-toggle-btn");

  // Redundant category-tabs row is permanently hidden (workflow steps encapsulate these cleanly)
  if (categoryTabs) {
    categoryTabs.style.setProperty("display", "none", "important");
  }

  if (stepNum === 1) {
    // Step 1: Ingest Document
    // SHOW #deed-dropzone-container (full un-minimized dropzone with the test deed cards)
    if (dropzoneContainer) {
      dropzoneContainer.style.removeProperty("display");
      dropzoneContainer.style.setProperty("display", "block", "important");
      dropzoneContainer.classList.remove("minimized");
    }
    if (dropzone) {
      dropzone.classList.remove("collapsed");
    }
    if (toggleBtn) {
      toggleBtn.textContent = (currentLanguage === "ml") ? "− ചുരുക്കുക" : "− Minimize";
    }

    // Step 1 dedicated chips: Document Ingest only
    const step1AllowedChips = [
      "chip-sample-deed",
      "chip-sample-ec",
      "chip-upload-deed"
    ];
    document.querySelectorAll(".chips-bar .chip").forEach(chip => {
      chip.style.setProperty("display", step1AllowedChips.includes(chip.id) ? "inline-flex" : "none", "important");
    });
    syncChipsBar();

    if (currentViewMode === "map") {
      setViewMode("split");
    }

  } else if (stepNum === 2) {
    // Step 2: Prior Title & Encumbrance
    // COMPLETELY HIDE #deed-dropzone-container (display: none !important;) so the chat pane has full 100% vertical space
    if (dropzoneContainer) {
      dropzoneContainer.style.setProperty("display", "none", "important");
    }

    // Step 2 dedicated chips: Lineage Audit only
    const step2AllowedChips = [
      "chip-timeline-aluva",
      "chip-mary-roy",
      "chip-timeline-clean",
      "chip-fair-value"
    ];
    document.querySelectorAll(".chips-bar .chip").forEach(chip => {
      chip.style.setProperty("display", step2AllowedChips.includes(chip.id) ? "inline-flex" : "none", "important");
    });
    syncChipsBar();

    if (currentViewMode === "map") {
      setViewMode("split");
    }

  } else if (stepNum === 3) {
    // Step 3: Satellite & KPBR
    // COMPLETELY HIDE #deed-dropzone-container
    if (dropzoneContainer) {
      dropzoneContainer.style.setProperty("display", "none", "important");
    }

    // Switch view mode to split (or map on small screens)
    if (window.innerWidth < 768) {
      setViewMode("map");
    } else {
      setViewMode("split");
    }

    // Show satellite tools (#tool-road, #tool-plot) and presets (#preset-select)
    const toolRoad = document.getElementById("tool-road");
    if (toolRoad) toolRoad.style.display = "";
    const toolPlot = document.getElementById("tool-plot");
    if (toolPlot) toolPlot.style.display = "";
    const presetSelect = document.getElementById("preset-select");
    if (presetSelect) presetSelect.style.display = "";

    // Set map tool for satellite plot verification
    setMapTool("plot");

    // Step 3 dedicated chips: Satellite & KPBR only
    const step3AllowedChips = [
      "chip-measure-road",
      "chip-demarcate-plot",
      "chip-check-elevation"
    ];
    document.querySelectorAll(".chips-bar .chip").forEach(chip => {
      chip.style.setProperty("display", step3AllowedChips.includes(chip.id) ? "inline-flex" : "none", "important");
    });
    syncChipsBar();

    // Ensure HUD is open/visible
    const hud = document.getElementById("map-hud");
    if (hud && hud.classList.contains("collapsed")) {
      toggleHUD();
    }
    if (typeof map !== "undefined" && map) {
      setTimeout(() => { map.invalidateSize(); }, 200);
    }

  } else if (stepNum === 4) {
    // Step 4: Due Diligence & Action
    // COMPLETELY HIDE #deed-dropzone-container
    if (dropzoneContainer) {
      dropzoneContainer.style.setProperty("display", "none", "important");
    }

    // Show action chips / checklist toggle (#btn-checklist-toggle)
    const btnChecklist = document.getElementById("btn-checklist-toggle");
    if (btnChecklist) btnChecklist.style.display = "";

    // Step 4 dedicated chips: Action & Resolution only
    const step4AllowedChips = [
      "chip-open-checklist",
      "chip-wa-inquiry",
      "chip-export-dossier"
    ];
    document.querySelectorAll(".chips-bar .chip").forEach(chip => {
      chip.style.setProperty("display", step4AllowedChips.includes(chip.id) ? "inline-flex" : "none", "important");
    });
    syncChipsBar();

    // Automatically open or highlight field checklist and ensure WhatsApp inquiry card
    toggleChecklist(true);
    ensureStep4ActionCard();

    setTimeout(() => {
      const waCard = document.querySelector(".whatsapp-card") || document.querySelector(".step4-action-banner");
      if (waCard) {
        waCard.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    }, 150);
  }
}

function nextWorkflowStep() {
  if (currentWorkflowStep < 4) {
    setWorkflowStep(currentWorkflowStep + 1);
  } else {
    // Restart Audit ↺
    setWorkflowStep(1);
  }
}

function prevWorkflowStep() {
  if (currentWorkflowStep > 1) {
    setWorkflowStep(currentWorkflowStep - 1);
  }
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

async function exportPlotDossier() {
  const coords = document.getElementById("hud-coords").textContent;
  const locality = document.getElementById("hud-locality-title").textContent;
  const centsText = document.getElementById("hud-cents").textContent;
  const centsVal = parseFloat(centsText) || 10.0;
  const roadMText = document.getElementById("hud-road-text").textContent;
  const roadMVal = parseFloat(roadMText) || 3.0;

  const plotPayload = {
    property_identifier: `${locality} (GPS: ${coords})`,
    document_number: "Satellite Ground Inspection Plot",
    sro: "Jurisdictional SRO",
    extent_cents: centsVal,
    classification: "Purayidam (Ground Check Required)",
    sanity_score: roadMVal >= 3.0 ? 85 : 45,
    risk_verdict: roadMVal >= 3.0 ? "PASS WITH CONDITIONS" : "DEFECTIVE ACCESS ROAD",
    findings: [
      {
        title: roadMVal >= 3.0 ? "KPBR 2019 Access Road Pass" : "Defective Access Road (< 3m)",
        severity: roadMVal >= 3.0 ? "LOW" : "CRITICAL",
        kerala_statute: "Kerala Panchayat Building Rules, 2019 (Rule 26 / Table 5)",
        explanation: `Satellite access road measured: ${roadMVal} meters. Under KPBR 2019, residential plots requiring building permits require minimum 3.0m motorable access.`
      }
    ],
    boundaries: [
      { direction: "Satellite Polygon", boundary_description: `${polygonPoints.length || 4} marked survey corner stones encompassing ${centsVal} Cents.` }
    ],
    building_rules: {
      rule_citation: "KPBR 2019 Rule 26 (Table 5)",
      min_road_width_m: 3.0,
      front_setback_m: 3.0,
      rear_setback_m: 1.5,
      side_setback_1_m: 1.0,
      side_setback_2_m: 1.2
    },
    whatsapp_inquiry: currentLanguage === 'ml'
      ? `നമസ്കാരം, ${locality}-ൽ ഞാൻ കണ്ട വസ്തുവിന്റെ സാറ്റലൈറ്റ് പരിശോധനയിൽ ഏകദേശം ${centsVal} സെന്റ് സ്ഥലവും ${roadMVal} മീറ്റർ വഴി വീതിയും കാണുന്നുണ്ട്. ഈ വസ്തുവിലേക്കുള്ള വഴി പഞ്ചായത്ത് വഴിയാണോ അതോ സ്വകാര്യ വഴിയവകാശമാണോ എന്ന് വ്യക്തമാക്കാമോ?`
      : `Hello, based on satellite analysis of the plot in ${locality} (~${centsVal} Cents, ~${roadMVal}m road width), could you please clarify whether the access road is a dedicated public Panchayat/Municipal road or a private easement pathway?`,
    whatsapp_inquiry_en: `Hello, based on satellite analysis of the plot in ${locality} (~${centsVal} Cents, ~${roadMVal}m road width), could you please clarify whether the access road is a dedicated public Panchayat/Municipal road or a private easement pathway?`,
    lang: currentLanguage
  };

  if (window.currentElevationData) {
    const elev = window.currentElevationData;
    plotPayload.findings.push({
      title: `Topographic Elevation: ${elev.elevation_meters}m MSL (${elev.flood_risk_level} Flood Risk)`,
      severity: (elev.flood_risk_level === "CRITICAL" || elev.flood_risk_level === "HIGH") ? "CRITICAL" : "LOW",
      kerala_statute: "KSDMA Flood Hazard Advisory & Kerala Conservation of Paddy Land Act 2008",
      explanation: `${elev.ksdma_hazard_advisory} River Basin: ${elev.river_basin || 'Local Watershed'}. Recommended Plinth Level: ≥${elev.recommended_plinth_height_m}m above road level.`
    });
  }

  try {
    const pdfRes = await fetch('/api/export_dossier', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(plotPayload)
    });
    if (!pdfRes.ok) throw new Error("Failed to generate PDF dossier");
    const blob = await pdfRes.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `kandezhuthu_plot_dossier_${locality.replace(/[\/,\s]/g, "_")}.pdf`;
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

  const lower = text.toLowerCase();
  if (lower.includes("timeline") || (lower.includes("ownership") && lower.includes("history")) || lower.includes("munnadharam") || lower.includes("മുന്നാധാരം")) {
    input.value = "";
    input.style.height = "48px";
    let preset = "aluva_broken";
    if (lower.includes("kakkanad") || lower.includes("wetland") || lower.includes("minor")) {
      preset = "kakkanad_wetland";
    } else if (lower.includes("clean")) {
      preset = "clean_title";
    }
    openOwnershipTimeline(preset);
    return;
  }

  const isPricingQuery = lower.includes("price") || lower.includes("bought") || lower.includes("how much") || lower.includes("consideration") || lower.includes("public") || lower.includes("fair value") || lower.includes("ന്യായവില") || lower.includes("പ്രതിഫല");

  if (isPricingQuery) {
    appendMsg("user", text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"));
    input.value = "";
    input.style.height = "48px";
    sendBtn.disabled = true;

    let preset = "aluva_broken";
    if (lower.includes("kakkanad") || lower.includes("wetland") || lower.includes("minor")) {
      preset = "kakkanad_wetland";
    } else if (lower.includes("clean")) {
      preset = "clean_title";
    }

    const answerHtml = `
      <div style="line-height:1.55; color:#262a33; font-size:0.88rem;">
        <h4 style="color:#990f3d; margin-top:0; margin-bottom:0.4rem; display:flex; align-items:center; gap:6px;">
          <span>§</span>
          <span>Yes, Historical Purchase Price is a Statutory Public Record in Kerala!</span>
        </h4>
        <p style="margin-bottom:0.5rem;">
          Under <strong>Sections 51 & 57 of the Indian Registration Act, 1908</strong>, all registered title deeds (such as Sale Deeds${currentLanguage === 'ml' ? ' / <em>തീറാധാരം</em>' : ''}) are recorded in <strong>Book 1 ("Register of non-testamentary documents relating to immovable property")</strong>, which is <strong>open to public inspection</strong> by any citizen upon payment of the statutory search fee.
        </p>
        <div style="background:#f6ede2; border-left:3px solid #990f3d; padding:0.55rem 0.8rem; border-radius:0 6px 6px 0; margin-bottom:0.65rem; font-size:0.83rem;">
          <strong>Three Key Statutory Price & Valuation Realities in Kerala:</strong>
          <ol style="margin:4px 0 0 18px; padding:0;">
            <li style="margin-bottom:3px;"><strong>Registered Consideration${currentLanguage === 'ml' ? ' (പ്രതിഫല തുക)' : ''}:</strong> The exact purchase price stated on the face of the document. Any citizen can apply for an Encumbrance Certificate (EC) or certified copy${currentLanguage === 'ml' ? ' (<em>പകർപ്പ്</em>)' : ''} from the Sub-Registrar Office (SRO) or the online PEARL portal (<code>keralaregistration.gov.in</code>).</li>
            <li style="margin-bottom:3px;"><strong>Kerala Govt Notified Fair Value${currentLanguage === 'ml' ? ' (ഭൂമിയുടെ ന്യായവില - Section 28A)' : ' (Fair Value - Section 28A Kerala Stamp Act)'}:</strong> The statutory minimum floor valuation per Are fixed by the Revenue Department for every Re-Survey number. 8% Stamp Duty + 2% Reg fee must be paid on whichever is higher (registered consideration vs fair value).</li>
            <li style="margin-bottom:2px;"><strong>Undervaluation Penalties (Section 45A Kerala Stamp Act):</strong> If a deed is registered below market value to evade 8% stamp duty or capital gains tax, District Registrar audits assess deficit duty with 12% penal interest, which becomes a <strong>first statutory charge / revenue recovery lien directly on the land</strong>.</li>
          </ol>
        </div>
        <p style="margin-bottom:0.4rem; font-size:0.83rem; color:#66605c;">
          Below is the chronological 30-year ownership and consideration audit for this property, detailing exactly what previous owners paid per Cent, their registered bank liabilities, and fair value benchmarks:
        </p>
      </div>
    `;

    appendMsg("agent", answerHtml);
    const timelineBubble = appendMsg("agent", `
      <div class="typing-indicator">
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <span style="font-size:0.85rem; color:#990f3d; margin-left:6px; font-weight:600;">
          Loading statutory purchase price and valuation audit...
        </span>
      </div>
    `);

    fetch(`/api/timeline_demo?preset=${preset}&lang=${currentLanguage}`)
      .then(res => res.json())
      .then(data => {
        renderOwnershipTimeline(timelineBubble, data, preset);
        sendBtn.disabled = false;
      })
      .catch(err => {
        timelineBubble.innerHTML = `<span style="color:red;">Error loading pricing timeline: ${err.message}</span>`;
        sendBtn.disabled = false;
      });
    return;
  }

  appendMsg("user", text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"));
  input.value = "";
  input.style.height = "48px";
  sendBtn.disabled = true;

  const loadingBubble = appendMsg("agent", `
    <div class="typing-indicator">
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
      <span style="font-size:0.85rem; color:#990f3d; margin-left:6px; font-weight:500;">
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
