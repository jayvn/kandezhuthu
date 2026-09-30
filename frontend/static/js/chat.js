function onChipClick(key) {
  const t = TRANSLATIONS[currentLanguage] || TRANSLATIONS.en;
  const prompt = (t.chipPrompts && t.chipPrompts[key]) || (TRANSLATIONS.en.chipPrompts && TRANSLATIONS.en.chipPrompts[key]);
  if (prompt) {
    sendPrompt(prompt);
  }
}

function updateGuidanceBarText() {
  const guidanceIcon = document.getElementById("guidance-icon");
  const guidanceText = document.getElementById("guidance-text");
  const guidanceActions = document.getElementById("guidance-actions");
  const guidanceFinishBtn = document.getElementById("guidance-finish-btn");
  const guidanceUndoBtn = document.getElementById("guidance-undo-btn");
  const t = TRANSLATIONS[currentLanguage] || TRANSLATIONS.en;

  if (guidanceUndoBtn) guidanceUndoBtn.textContent = t.btnUndo;
  if (guidanceFinishBtn) {
    guidanceFinishBtn.textContent = t.guidanceSeal;
    guidanceFinishBtn.style.display = activeTool === "road" ? "none" : "";
  }

  const guidancePinActions = document.getElementById("guidance-pin-actions");

  if (typeof activeTool === "undefined" || activeTool === "pin") {
    if (guidanceIcon) guidanceIcon.textContent = "●";
    if (guidanceText) guidanceText.textContent = (typeof currentMarker !== "undefined" && currentMarker) ? t.guidancePinned : t.guidanceDefault;
    if (guidanceActions) guidanceActions.style.display = "none";
    if (guidancePinActions) guidancePinActions.style.display = "flex";
  } else if (activeTool === "plot") {
    if (guidanceIcon) guidanceIcon.textContent = "◇";
    if (guidanceText) guidanceText.textContent = t.guidancePlot;
    if (guidanceActions) guidanceActions.style.display = "flex";
    if (guidancePinActions) guidancePinActions.style.display = "none";
  } else if (activeTool === "road") {
    if (guidanceIcon) guidanceIcon.textContent = "↔";
    if (guidanceText) guidanceText.textContent = t.guidanceRoad;
    if (guidanceActions) guidanceActions.style.display = "flex";
    if (guidancePinActions) guidancePinActions.style.display = "none";
  }
}

function setViewMode(mode) {
  currentViewMode = mode;
  document.body.className = "view-" + mode;
  document.querySelectorAll(".view-btn").forEach(btn => {
    btn.classList.toggle("active", btn.getAttribute("data-mode") === mode);
  });
  if (map) {
    setTimeout(() => { map.invalidateSize(); }, 250);
  }
}

function toggleDropzone(force) {
  const container = document.getElementById("deed-dropzone-container");
  const btn = document.getElementById("dropzone-toggle-btn");
  if (!container) return;
  const shouldMinimize = typeof force === "boolean" ? force : !container.classList.contains("minimized");
  if (shouldMinimize) {
    container.classList.add("minimized");
    if (btn) btn.textContent = "+ Add document";
  } else {
    container.classList.remove("minimized");
    if (btn) btn.textContent = "− Minimize";
  }
}

input.addEventListener("input", function() {
  this.style.height = "48px";
  this.style.height = Math.min(this.scrollHeight, 140) + "px";
});
input.addEventListener("keydown", function(e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    form.dispatchEvent(new Event("submit"));
  }
});

function appendMsg(who, htmlContent) {
  const m = document.createElement("div");
  m.className = "msg " + who;
  const label = document.createElement("div");
  label.className = "msg-label";
  label.textContent = who === "user" ? "You" : "Kandezhuthu AI";
  m.appendChild(label);

  const b = document.createElement("div");
  b.className = "bubble";
  b.innerHTML = htmlContent;
  m.appendChild(b);

  log.appendChild(m);
  log.scrollTop = log.scrollHeight;
  return b;
}

const WA_HEADING = /^[#>*\s]*(?:\*\*)?\s*'?(?:വാട്സാപ്പ് ചോദ്യം|WhatsApp Message|WhatsApp Inquiry|ചോദിക്കേണ്ട ചോദ്യം)[^\n]*$/im;

function escapeHtml(str) {
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function renderMarkdownBlock(text) {
  // Models sometimes emit LaTeX arrows; show them as plain glyphs.
  text = text
    .replace(/\$\\+(?:leftarrow|gets|longleftarrow)\$/g, "←")
    .replace(/\$\\+(?:rightarrow|to|longrightarrow)\$/g, "→");
  if (window.marked && window.DOMPurify) {
    return DOMPurify.sanitize(marked.parse(text, { gfm: true, breaks: true }));
  }
  return "<p>" + escapeHtml(text).replace(/\n\n/g, "</p><p>").replace(/\n/g, "<br>") + "</p>";
}

function formatMarkdown(text) {
  if (!text) return "";
  // Pull the WhatsApp draft out before rendering so it becomes a copyable card.
  const heading = text.match(WA_HEADING);
  if (!heading) return renderMarkdownBlock(text);

  const before = text.slice(0, heading.index);
  let rest = text.slice(heading.index + heading[0].length);
  const next = rest.search(/\n\s*(?:#{1,6}\s|---\s*\n)/);
  const after = next >= 0 ? rest.slice(next) : "";
  let draft = (next >= 0 ? rest.slice(0, next) : rest).trim();

  const quoted = draft.match(/["“]([^"”]{15,})["”]/);
  draft = (quoted ? quoted[1] : draft)
    .replace(/^```[a-z]*\s*/i, "").replace(/\s*```$/, "")
    .replace(/^[>\s]+/gm, "").trim();
  if (draft.length <= 10) return renderMarkdownBlock(text);

  const waCard = `
    <div class="whatsapp-card">
      <div class="whatsapp-header">
        <span class="whatsapp-title">${currentLanguage === 'ml' ? 'വിൽപ്പനക്കാരനോട് ചോദിക്കാൻ (WhatsApp)' : 'Message for the seller'}</span>
        <div class="whatsapp-actions">
          <button class="copy-btn" onclick="copyText(this)">Copy</button>
          <a class="wa-direct-btn" href="https://api.whatsapp.com/send?text=${encodeURIComponent(draft)}" target="_blank" rel="noopener noreferrer">WhatsApp</a>
        </div>
      </div>
      <div class="whatsapp-text">${escapeHtml(draft)}</div>
    </div>`;
  return renderMarkdownBlock(before) + waCard + (after.trim() ? renderMarkdownBlock(after) : "");
}

function fallbackCopy(text) {
  const ta = document.createElement("textarea");
  ta.value = text;
  ta.style.position = "fixed";
  ta.style.opacity = "0";
  document.body.appendChild(ta);
  ta.focus();
  ta.select();
  try { document.execCommand("copy"); } catch (e) {}
  document.body.removeChild(ta);
}

function copyText(btn, text) {
  if (!text) {
    const card = btn.closest(".whatsapp-card");
    if (card) {
      const textEl = card.querySelector(".whatsapp-text");
      if (textEl) text = textEl.textContent.trim();
    }
  }
  const doFeedback = () => {
    const originalText = btn.innerHTML;
    const originalBg = btn.style.backgroundColor;
    const originalColor = btn.style.color;
    btn.innerHTML = "✓ Copied!";
    btn.style.backgroundColor = "#0d7680";
    btn.style.color = "#ffffff";
    btn.classList.add("copied");
    setTimeout(() => {
      btn.innerHTML = originalText;
      btn.style.backgroundColor = originalBg;
      btn.style.color = originalColor;
      btn.classList.remove("copied");
    }, 2000);
  };

  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(doFeedback).catch(() => {
      fallbackCopy(text);
      doFeedback();
    });
  } else {
    fallbackCopy(text);
    doFeedback();
  }
}
const copyWhatsApp = copyText;

function sendPrompt(text) {
  input.value = text;
  form.dispatchEvent(new Event("submit"));
}

/* Drag and Drop Handlers with Window-Level Protection */
let windowDragCounter = 0;

window.addEventListener("dragenter", (e) => {
  if (e.dataTransfer && e.dataTransfer.types && Array.from(e.dataTransfer.types).includes("Files")) {
    e.preventDefault();
    windowDragCounter++;
    const overlay = document.getElementById("drop-overlay");
    const dropzone = document.getElementById("deed-dropzone");
    if (overlay) overlay.classList.add("active");
    if (dropzone) dropzone.classList.add("drag-hover");
  }
});

window.addEventListener("dragover", (e) => {
  e.preventDefault();
  if (e.dataTransfer) {
    e.dataTransfer.dropEffect = "copy";
  }
});

window.addEventListener("dragleave", (e) => {
  e.preventDefault();
  windowDragCounter--;
  if (windowDragCounter <= 0) {
    windowDragCounter = 0;
    const overlay = document.getElementById("drop-overlay");
    const dropzone = document.getElementById("deed-dropzone");
    if (overlay) overlay.classList.remove("active");
    if (dropzone) dropzone.classList.remove("drag-hover");
  }
});

window.addEventListener("drop", (e) => {
  e.preventDefault();
  windowDragCounter = 0;
  const overlay = document.getElementById("drop-overlay");
  const dropzone = document.getElementById("deed-dropzone");
  if (overlay) overlay.classList.remove("active");
  if (dropzone) dropzone.classList.remove("drag-hover");

  if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length) {
    if (e.dataTransfer.files.length === 1) {
      handleDeedUpload(e.dataTransfer.files[0]);
    } else {
      handleMultipleDeedUploads(Array.from(e.dataTransfer.files));
    }
  }
});

/* Batch Upload Handler */
async function handleMultipleDeedUploads(files) {
  appendMsg("user", `<strong>Uploaded ${files.length} Deed Documents in Batch</strong>`);
  for (let i = 0; i < files.length; i++) {
    await handleDeedUpload(files[i]);
  }
}

/* Multimodal Deed OCR Upload Handler with Progressive Steps */
async function handleDeedUpload(file) {
  if (!file) return;
  setWorkflowStep(2);
  const fileName = file.name;
  const fileSizeKb = (file.size / 1024).toFixed(1);

  appendMsg("user", `<strong>Uploaded Deed Document:</strong> ${fileName} (${fileSizeKb} KB)`);

  const loadingBubble = appendMsg("agent", `
    <div class="ocr-progress-card">
      <div class="ocr-progress-header">
        <span class="ocr-spinner"></span>
        <span>Ingesting Deed Document: <strong>${fileName}</strong> (${fileSizeKb} KB)</span>
      </div>
      <div class="ocr-steps">
        <div class="ocr-step active" id="ocr-step-1">
          <span>●</span> <span>Step 1: Reading document scan & packaging multimodal payload...</span>
        </div>
        <div class="ocr-step" id="ocr-step-2">
          <span>○</span> <span>Step 2: Cloud Document AI & Gemini 3.8 Flash Multimodal OCR...</span>
        </div>
        <div class="ocr-step" id="ocr-step-3">
          <span>○</span> <span>Step 3: Kerala 4-trap statutory audit & boundary extraction...</span>
        </div>
      </div>
    </div>
  `);

  const step1 = loadingBubble.querySelector("#ocr-step-1");
  const step2 = loadingBubble.querySelector("#ocr-step-2");
  const step3 = loadingBubble.querySelector("#ocr-step-3");

  try {
    // Step 1 done -> Step 2 active
    setTimeout(() => {
      if (step1 && step2) {
        step1.className = "ocr-step done";
        step1.innerHTML = "<span>✓</span> <span>Step 1: Document scan ingested</span>";
        step2.className = "ocr-step active";
        step2.innerHTML = "<span>●</span> <span>Step 2: Cloud Document AI & Gemini 3.8 Flash Vision OCR running...</span>";
      }
    }, 400);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("user_id", "web-user");

    const isEc = file.name.toLowerCase().includes("ec") || file.name.toLowerCase().includes("encumbrance") || file.name.toLowerCase().includes("kudikkadam");
    const endpoint = (isEc ? "/api/upload_ec" : "/api/upload_deed") + `?lang=${currentLanguage}`;

    const res = await fetch(endpoint, {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      throw new Error(`Processing failed with status ${res.status}`);
    }

    // Step 2 done -> Step 3 active
    if (step2 && step3) {
      step2.className = "ocr-step done";
      step2.innerHTML = "<span>✓</span> <span>Step 2: Malayalam/English deed text parsed</span>";
      step3.className = "ocr-step active";
      step3.innerHTML = "<span>●</span> <span>Step 3: Auditing 4 statutory traps & KPBR setbacks...</span>";
    }

    const result = await res.json();

    // Render result card
    setTimeout(() => {
      renderDeedAuditCard(loadingBubble, result, fileName);
    }, 300);

  } catch (err) {
    loadingBubble.innerHTML = `<span style="color:#990f3d;">▲ Error analyzing deed document: ${err.message}</span>`;
  }
}

/* Sample Deed OCR Runner */
async function runSampleDeedOCR(docType = "deed") {
  setWorkflowStep(2);
  const isEc = docType === "ec";
  const docTitle = isEc ? "Sample Kerala SRO Encumbrance Certificate (EC Form 15, 30-Year Search)" : "Sample Kerala Title Deed (Aluva SRO Doc 1420/2014, Re-Sy 345/1)";
  const fileName = isEc ? "kerala_sro_ec_aluva_30_year_search.pdf" : "kerala_sale_deed_aluva_re_sy_345_1.pdf";
  const step1Desc = isEc ? "Sample SRO Form 15 EC (1994-2024 Search Period)" : "Sample PDF loaded (11 Cents, Aluva West Village)";
  const step3Desc = isEc ? "Auditing registered mortgages, liens & SARFAESI charges..." : "Evaluating pathway easement, minor shares & wetland status...";

  appendMsg("user", `<strong>Demonstration Request:</strong> Scan ${docTitle}`);

  const loadingBubble = appendMsg("agent", `
    <div class="ocr-progress-card">
      <div class="ocr-progress-header">
        <span class="ocr-spinner"></span>
        <span>Scanning Document: <strong>${fileName}</strong> (Gemini 3.8 Flash Vision)</span>
      </div>
      <div class="ocr-steps">
        <div class="ocr-step done">
          <span>✓</span> <span>Step 1: ${step1Desc}</span>
        </div>
        <div class="ocr-step active">
          <span>●</span> <span>Step 2: Cloud Document AI & Multimodal Vision OCR extraction...</span>
        </div>
        <div class="ocr-step">
          <span>○</span> <span>Step 3: ${step3Desc}</span>
        </div>
      </div>
    </div>
  `);

  try {
    const res = await fetch(`/api/sample_deed?doc_type=${docType}&process=true&user_id=web-user&lang=${currentLanguage}`);
    if (!res.ok) throw new Error("Could not process sample document");
    const result = await res.json();
    setTimeout(() => {
      renderDeedAuditCard(loadingBubble, result, fileName);
    }, 400);
  } catch (err) {
    loadingBubble.innerHTML = `<span style="color:#990f3d;">▲ Error scanning document: ${err.message}</span>`;
  }
}

/* Render Extracted Deed Card */
function renderDeedAuditCard(container, data, fileName) {
  // The server reports failures as HTTP 200 with an error text part. A failed
  // scan must never fall through to the "no red flags" card.
  const scanError = data && (data.error || (data.parts && data.parts[0] && data.parts[0].text));
  if (!data || scanError || (!data.sanity_result && data.entries === undefined && data.is_nil_encumbrance === undefined)) {
    container.innerHTML = `<span style="color:#990f3d;">▲ The document could not be read, so nothing was checked.</span>` +
      (scanError ? `<div style="margin-top:6px; font-size: var(--fs-12); color:#66605c;">${escapeHtml(String(scanError))}</div>` : "");
    return;
  }
  window._lastUploadedDeedData = data;
  if (data.sanity_result) window._lastDeedData = data; else window._lastEcData = data;
  markStepDone(data.sanity_result ? 1 : 2);
  setWorkflowStep(2);

  if (data.is_nil_encumbrance !== undefined || data.entries !== undefined) {
    const ecScore = data.safety_score ?? 100;
    const isNil = data.is_nil_encumbrance;
    const badgeColor = isNil ? "#0d7680" : (data.risk_flags && data.risk_flags.length ? "#990f3d" : "#c07a1a");
    const badgeText = isNil ? "● NIL ENCUMBRANCE (Nil-EC)" : (data.risk_flags && data.risk_flags.length ? "■ ACTIVE LIABILITIES / GEHAN" : "▲ RECORDED TRANSACTIONS");

    let entriesHtml = "";
    if (data.entries && data.entries.length) {
      entriesHtml = `
        <div style="margin-top:10px; font-size: var(--fs-14);">
          <strong>Official SRO EC Registration Entries (${data.total_entries_count}):</strong>
          <div style="display:flex; flex-direction:column; gap:6px; margin-top:6px;">
            ${data.entries.map(e => `
              <div style="background:#f6ede2; border:1px solid #e9decf; border-radius:6px; padding:6px 10px;">
                <div style="display:flex; justify-content:space-between; font-weight:700;">
                  <span>Doc #${e.doc_number} (${e.year}) - SRO ${e.sro_name}</span>
                  <span style="color:${e.is_undischarged_liability || e.is_court_attachment ? '#990f3d' : '#0d7680'};">${e.nature_of_act}</span>
                </div>
                <div style="color:#66605c; font-size: var(--fs-12); margin-top:2px;">
                  ${e.claimants && e.claimants.length ? `Favoring: ${e.claimants.join(', ')} | ` : ''}
                  ${e.liability_amount_inr ? `Liability: ₹${e.liability_amount_inr.toLocaleString()} | ` : ''}
                  ${e.notes ? e.notes : ''}
                </div>
              </div>
            `).join('')}
          </div>
        </div>
      `;
    }

    let risksHtml = "";
    if (data.risk_flags && data.risk_flags.length) {
      risksHtml = `
        <div style="margin-top:10px; background:#fbebee; border:1px solid #f0c2cf; border-radius:8px; padding:8px 12px;">
          <div style="font-weight:700; color:#7c0c32; font-size: var(--fs-14); margin-bottom:4px;">■ Critical Encumbrance Flags:</div>
          ${data.risk_flags.map(r => `
            <div style="font-size: var(--fs-12); color:#5f0926; margin-bottom:6px;">
              <strong>${r.title}:</strong> ${r.description}<br>
              <small style="color:#7c0c32;">Remedy: ${r.remedial_action}</small>
            </div>
          `).join('')}
        </div>
      `;
    }

    container.innerHTML = `
      <div class="deed-audit-card">
        <div class="deed-audit-header">
          <div>
            <div style="font-size: var(--fs-14); font-weight:700; color:#990f3d;">SRO Encumbrance Certificate (EC) Audit</div>
            <div style="font-size: var(--fs-12); color:#66605c;">${fileName} • Search Period: ${data.ec_period || '30 Years'}</div>
          </div>
          <div style="background:${badgeColor}; color:#fff; font-size: var(--fs-12); font-weight:700; padding:3px 10px; border-radius:12px;">
            ${badgeText} (${ecScore}/100)
          </div>
        </div>
        <div style="font-size: var(--fs-14); color:#4d4845; margin-top:8px;">${data.summary}</div>
        ${risksHtml}
        ${entriesHtml}
        <div class="deed-action-buttons">
          <button class="deed-action-btn primary" onclick="onStepClick(4)">${currentLanguage === 'ml' ? "ഉടമയോട് ചോദിക്കുക" : "Ask seller"}</button>
        </div>
      </div>
    `;
    setWorkflowStep(2);
    container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    log.scrollTop = log.scrollHeight;
    return;
  }

  const meta = data.metadata || {};
  const sanity = data.sanity_result || {};
  const score = sanity.sanity_score ?? 100;

  let scoreClass = "clear";
  let scoreIcon = "●";
  if (score < 50) {
    scoreClass = "danger";
    scoreIcon = "■";
  } else if (score < 85) {
    scoreClass = "caution";
    scoreIcon = "▲";
  }

  // Boundaries list
  let boundariesHtml = "";
  if (meta.boundaries && meta.boundaries.length) {
    boundariesHtml = `
      <div class="boundary-box">
        <div class="boundary-title">${currentLanguage === 'ml' ? 'നാലതിരുകൾ (ചതുരതിരുകൾ):' : 'Four Boundaries Schedule:'}</div>
        ${meta.boundaries.map(b => {
          let dir = b.direction || '';
          let desc = b.boundary_description || '';
          if (currentLanguage === 'en') {
            dir = dir.replace(/\s*\([^)]*[\u0D00-\u0D7F][^)]*\)/g, '');
            desc = desc.replace(/\s*\([^)]*[\u0D00-\u0D7F][^)]*\)/g, '');
          }
          return `
          <div class="boundary-row">
            <span class="boundary-dir">${dir}:</span>
            <span>${desc}</span>
          </div>`;
        }).join("")}
      </div>
    `;
  }

  // Prior Deeds list
  let priorHtml = "";
  if (meta.prior_deeds && meta.prior_deeds.length) {
    priorHtml = `
      <div class="prior-deeds-box">
        <div class="prior-title">${currentLanguage === 'ml' ? 'മുന്നാധാര വിവരങ്ങൾ (Prior Title Lineage):' : 'Prior Title Lineage:'}</div>
        ${meta.prior_deeds.map(p => {
          let dt = p.deed_type || "Prior Deed";
          if (currentLanguage === 'en') {
            dt = dt.replace(/[\u0D00-\u0D7F]+\s*\/?\s*/g, '').trim() || "Prior Deed";
          }
          return `
          <div class="prior-item">
            <strong>${p.doc_number || "Doc"}</strong> ${p.year ? `(${p.year})` : ""} - ${dt}
            ${p.sro_name ? `· SRO ${p.sro_name}` : ""}
          </div>`;
        }).join("")}
      </div>
    `;
  }

  // Findings list
  let findingsHtml = "";
  if (sanity.findings && sanity.findings.length) {
    findingsHtml = `
      <div class="findings-box">
        <div style="font-weight:700; color:#990f3d; font-size: var(--fs-14); margin-bottom:0.35rem;">▲ ${currentLanguage === 'ml' ? 'കണ്ടെത്തിയ നിയമക്കുരുക്കുകൾ:' : 'Statutory Red Flags Detected:'}</div>
        ${sanity.findings.map(f => {
          let exp = f.explanation || '';
          if (currentLanguage === 'en') {
            exp = exp.replace(/\s*\([^)]*[\u0D00-\u0D7F][^)]*\)/g, '');
          }
          return `
          <div class="finding-alert ${f.severity === 'CRITICAL' ? 'critical' : ''}">
            <div class="finding-alert-header">
              <span>${f.title} ${currentLanguage === 'ml' && f.title_malayalam ? `(${f.title_malayalam})` : ''}</span>
              <span style="font-size: var(--fs-12); text-transform:uppercase;">${f.severity}</span>
            </div>
            <div>${exp}</div>
            <div style="font-size: var(--fs-12); color:#66605c; margin-top:3px;"><strong>Statute:</strong> ${f.kerala_statute}</div>
          </div>`;
        }).join("")}
      </div>
    `;
  }

  // Building rules pill
  let buildingHtml = "";
  if (data.building_rules) {
    const br = data.building_rules;
    buildingHtml = `
      <div style="background:#eef5f5; border:1px solid #a8cfd1; border-radius:8px; padding:0.55rem 0.75rem; margin-bottom:0.85rem; font-size: var(--fs-12); color:#0d7680;">
        <strong>Building Rules Match (${br.rule_citation || 'KPBR 2019'}):</strong><br>
        • Min Access Road Width: <strong>${br.min_road_width_m} meters</strong><br>
        • Setbacks: Front ${br.front_setback_m}m | Rear ${br.rear_setback_m}m | Sides ${br.side_setback_1_m}m & ${br.side_setback_2_m}m
      </div>
    `;
  }

  // Paddy conversion fee pill
  let paddyHtml = "";
  if (data.paddy_conversion && data.paddy_conversion.statutory_conversion_fee_inr > 0) {
    const pc = data.paddy_conversion;
    paddyHtml = `
      <div style="background:#fbf0e0; border:1px solid #ecd2a8; border-radius:8px; padding:0.55rem 0.75rem; margin-bottom:0.85rem; font-size: var(--fs-12); color:#8a4d00;">
        <strong>Form 6 Section 27A Conversion Fee:</strong><br>
        • Estimated Govt Fee: <strong>₹${pc.statutory_conversion_fee_inr.toLocaleString('en-IN')}</strong> (${pc.applicable_slab_percentage}% slab)<br>
        • Free Exemption Applied: ${pc.free_exemption_cents} Cents (Govt exemption for residential plots up to 25 cents).
      </div>
    `;
  }

  const ml = currentLanguage === 'ml';
  const verdictCopy = score < 60
    ? ["danger", "■", ml ? "ഗുരുതരമായ പ്രശ്നങ്ങൾ കണ്ടെത്തി" : "High-risk clauses found",
       ml ? "പണം നൽകുന്നതിന് മുമ്പ് താഴെയുള്ള കാര്യങ്ങൾ വിൽപ്പനക്കാരനോട് ചോദിച്ച് വ്യക്തമാക്കുക." : "Resolve the points below with the seller before paying anything."]
    : score < 85
    ? ["caution", "▲", ml ? "വ്യക്തത വേണ്ട കാര്യങ്ങൾ" : "Points to clarify",
       ml ? "30 വർഷത്തെ ബാധ്യതാ സർട്ടിഫിക്കറ്റുമായും (EC) മുന്നാധാരങ്ങളുമായും ഒത്തുനോക്കുക." : "Check these against the 30-year EC and the prior deeds."]
    : ["clear", "●", ml ? "പ്രശ്നങ്ങൾ കണ്ടെത്തിയില്ല" : "No red flags found",
       ml ? "അടുത്തത്: EC-യും മുന്നാധാരങ്ങളുമായി ഒത്തുനോക്കുക." : "Next: match it against the EC and the prior deeds."];
  const buyerVerdictHtml = `
      <div class="buyer-verdict-box ${verdictCopy[0]}">
        <div class="buyer-verdict-title"><span aria-hidden="true">${verdictCopy[1]}</span> <span>${verdictCopy[2]}</span></div>
        <div class="buyer-verdict-text">${verdictCopy[3]}</div>
      </div>
    `;

  const dash = v => (v === undefined || v === null || v === "" ? "—" : v);
  const factsHtml = `
        <div class="deed-grid">
          <div class="deed-grid-item">
            <div class="deed-grid-label">${ml ? "സർവേ നമ്പർ" : "Survey no"}</div>
            <div class="deed-grid-val">${dash(meta.re_survey_no || meta.survey_no)}</div>
          </div>
          <div class="deed-grid-item">
            <div class="deed-grid-label">${ml ? "വില്ലേജ്" : "Village"}</div>
            <div class="deed-grid-val">${dash(meta.village)}${meta.taluk ? `, ${meta.taluk}` : ""}</div>
          </div>
          <div class="deed-grid-item">
            <div class="deed-grid-label">${ml ? "വിസ്തീർണ്ണം" : "Extent"}</div>
            <div class="deed-grid-val">${meta.extent_cents != null ? `${meta.extent_cents} ${ml ? "സെന്റ്" : "cents"}` : "—"}</div>
          </div>
          <div class="deed-grid-item">
            <div class="deed-grid-label">${ml ? "ഭൂമിയുടെ തരം" : "Land type"}</div>
            <div class="deed-grid-val${meta.is_paddy_wetland_risk ? " is-risk" : ""}">${dash(meta.revenue_classification)}${meta.is_paddy_wetland_risk ? " ▲" : ""}</div>
          </div>
        </div>`;
  const detailsHtml = [
    boundariesHtml && `<details class="deed-more"><summary>${ml ? "നാലതിരുകൾ" : "Boundaries"}</summary>${boundariesHtml}</details>`,
    priorHtml && `<details class="deed-more"><summary>${ml ? "മുന്നാധാരങ്ങൾ" : "Prior deeds recited"} (${meta.prior_deeds.length})</summary>${priorHtml}</details>`,
    (buildingHtml || paddyHtml) && `<details class="deed-more"><summary>${ml ? "കെട്ടിട ചട്ടങ്ങളും ഫീസും" : "Building rules and fees"}</summary>${buildingHtml}${paddyHtml}</details>`,
  ].filter(Boolean).join("");

  const cardHtml = `
    <div class="deed-audit-card">
      <div class="deed-card-header">
        <div class="deed-title-group">
          <span class="deed-doc-tag">${meta.document_number ? `Doc ${meta.document_number}` : escapeHtml(fileName || "")}</span>
          ${meta.year ? `<span class="deed-meta">${meta.year}</span>` : ""}
          ${meta.deed_type ? `<span class="deed-meta">· ${meta.deed_type}</span>` : ""}
          ${meta.sro_name ? `<span class="deed-meta">· SRO ${meta.sro_name}</span>` : ""}
        </div>
        <div class="deed-score-badge ${scoreClass}">
          <span aria-hidden="true">${scoreIcon}</span>
          <span class="sr-only">${{ danger: ml ? "അപകടം" : "Danger", caution: ml ? "ശ്രദ്ധിക്കുക" : "Caution", clear: ml ? "പ്രശ്നങ്ങളില്ല" : "No red flags" }[scoreClass]}:</span>
          <span>${score}/100</span>
        </div>
      </div>

      <div class="deed-card-body">
        ${buyerVerdictHtml}
        ${findingsHtml}
        ${factsHtml}
        ${detailsHtml}

        <div class="deed-action-buttons">
          <button class="deed-action-btn primary" onclick="onStepClick(4)">${ml ? "ഉടമയോട് ചോദിക്കുക" : "Ask seller"}</button>
          <button class="deed-action-btn" onclick="auditPriorDeedsOfScannedDeed()">${ml ? "മുന്നാധാരം പരിശോധിക്കുക" : "Check prior deeds"}</button>
          <button class="deed-action-btn" onclick="locatePlotOnSatellite('${escapeHtml(meta.village || '')}', '${escapeHtml(meta.re_survey_no || meta.survey_no || '')}')">${ml ? "മാപ്പിൽ കാണുക" : "Find on map"}</button>
          <button class="deed-action-btn" onclick="exportCurrentDeedDossier()">↓ PDF</button>
        </div>
      </div>
    </div>
  `;

  container.innerHTML = cardHtml;
  setWorkflowStep(2);
  container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  log.scrollTop = log.scrollHeight;
}

function locatePlotOnSatellite(village, survey) {
  setViewMode('split');
  if (!village) return;
  // Goes to the village; the user moves the pin onto the actual plot.
  const searchInput = document.getElementById('map-search');
  if (searchInput) {
    searchInput.value = `${village}, Kerala`;
    searchLocation();
  }
}

// Sends the prior deeds recited in the scanned deed to the agent's chain audit.
function auditPriorDeedsOfScannedDeed() {
  const meta = (window._lastDeedData && window._lastDeedData.metadata) || {};
  const priors = meta.prior_deeds || [];
  const isMl = currentLanguage === 'ml';
  if (!priors.length) {
    appendMsg("agent", isMl
      ? "ഈ ആധാരത്തിൽ മുന്നാധാരങ്ങളുടെ വിവരം കണ്ടില്ല. മുന്നാധാരങ്ങൾ അപ്‌ലോഡ് ചെയ്യുക, അല്ലെങ്കിൽ അവയുടെ നമ്പർ, വർഷം, SRO, കക്ഷികൾ, വിസ്തീർണ്ണം എന്നിവ ചാറ്റിൽ എഴുതുക."
      : "This deed doesn't recite any prior deeds. Upload the prior deeds, or type each one's number, year, SRO, parties and extent in the chat.");
    return;
  }
  const lines = priors.map(p => `- Doc ${p.doc_number || "?"}${p.year ? ` (${p.year})` : ""}${p.deed_type ? `, ${p.deed_type}` : ""}${p.sro_name ? `, SRO ${p.sro_name}` : ""}`).join("\n");
  const current = `Doc ${meta.document_number || "?"}${meta.year ? ` (${meta.year})` : ""}, Survey ${meta.re_survey_no || meta.survey_no || "?"}, ${meta.village || ""}, ${meta.extent_cents ?? "?"} cents, sellers: ${(meta.grantors || []).join(", ") || "?"}, buyers: ${(meta.grantees || []).join(", ") || "?"}`;
  sendPrompt(`Audit the title chain for this property.\nCurrent deed: ${current}\nPrior deeds recited in it:\n${lines}\nFlag gaps, extent changes and missing heirs, and list which prior deeds I still need to get.`);
}

function askAboutDeed(docNo, surveyNo) {
  const prompt = `Based on deed ${docNo ? 'Doc ' + docNo : ''}${surveyNo ? ` (Survey No ${surveyNo})` : ''}, what are the critical legal risks, pathway easements, and physical checks needed before paying token advance?`;
  input.value = prompt;
  input.focus();
}

/* Open Interactive 30-Year Ownership Timeline */
async function openOwnershipTimeline(preset = 'aluva_broken') {
  setWorkflowStep(2);
  const presetLabels = {
    aluva_broken: "Aluva Broken Chain (Doc 1420/2014 · Mary Roy Defect & Federal Bank Mortgage)",
    kakkanad_wetland: "Kakkanad Wetland & Minor Share (Doc 1204/2015 · Sec 8 HMGA & Data Bank)",
    clean_title: "39-Year Lineage Chain (Doc 945/2018 · no gaps found)"
  };

  appendMsg("user", `<strong>Sample timeline:</strong> <em>${presetLabels[preset] || preset}</em>`);

  const loadingBubble = appendMsg("agent", `
    <div class="typing-indicator">
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
      <span style="font-size: var(--fs-14); color:#990f3d; margin-left:6px; font-weight:600;">
        ${currentLanguage === 'ml' ? '30 വർഷത്തെ മുന്നാധാര ശൃംഖല പരിശോധിക്കുന്നു...' : 'Reconstructing 30-year chronological title chain across decades...'}
      </span>
    </div>
  `);

  try {
    const res = await fetch(`/api/timeline_demo?preset=${preset}&lang=${currentLanguage}`);
    if (!res.ok) throw new Error("Could not load ownership timeline");
    const data = await res.json();
    renderOwnershipTimeline(loadingBubble, data, preset);
  } catch (err) {
    loadingBubble.innerHTML = `<span style="color:#990f3d;">▲ Error loading ownership timeline: ${err.message}</span>`;
  }
}

/* Render Interactive Ownership Timeline Card */
function renderOwnershipTimeline(container, data, currentPreset = 'aluva_broken') {
  const score = data.score ?? 0;
  let scoreClass = "danger";
  let scoreIcon = "■";
  if (score >= 85) {
    scoreClass = "clear";
    scoreIcon = "●";
  } else if (score >= 50) {
    scoreClass = "caution";
    scoreIcon = "▲";
  }

  const nodes = data.nodes || [];
  const nodesHtml = nodes.map((node, idx) => {
    const statusClass = node.status || (node.flags && node.flags.length ? "broken" : "valid");
    const markerIcon = statusClass === "valid" ? "✓" : (statusClass === "warning" ? "!" : "✕");

    let flagsHtml = "";
    if (node.flags && node.flags.length) {
      flagsHtml = `
        <div class="timeline-flags-list">
          ${node.flags.map(f => `
            <div class="timeline-flag-pill ${statusClass === 'warning' ? 'warning' : ''}">
              <div class="timeline-flag-title">
                <span>${statusClass === 'warning' ? '▲' : '■'}</span>
                <span>${f.title}</span>
              </div>
              <div class="timeline-flag-statute"><strong>Statute:</strong> ${f.statute}</div>
              <div class="timeline-flag-desc">${f.desc}</div>
            </div>
          `).join("")}
        </div>
      `;
    }

    let financialHtml = "";
    if (node.consideration_display) {
      financialHtml = `
        <div style="margin-top:0.45rem; padding:0.45rem 0.65rem; background:#f6ede2; border:1px solid #e9decf; border-radius:6px; font-size: var(--fs-12);">
          <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:4px;">
            <span style="font-weight:700; color:#990f3d; display:flex; align-items:center; gap:4px;">
              <span>₹</span>
              <span>${node.consideration_display}</span>
            </span>
            ${node.price_per_cent ? `<span style="background:#eef2f7; color:#0f5499; padding:1px 6px; border-radius:4px; font-weight:700; font-size: var(--fs-12);">${node.price_per_cent}</span>` : ''}
            ${node.stamp_duty_paid ? `<span style="background:#f6ede2; color:#66605c; padding:1px 6px; border-radius:4px; font-size: var(--fs-12);">Stamp Duty: ${node.stamp_duty_paid}</span>` : ''}
          </div>
          ${node.financial_note ? `<div style="color:#4d4845; margin-top:3px; font-size: var(--fs-12);">${node.financial_note}</div>` : ''}
          ${node.govt_fair_value && node.govt_fair_value !== 'N/A' ? `<div style="color:#66605c; font-size: var(--fs-12); margin-top:2px;"><strong>Kerala Govt Fair Value ${currentLanguage === 'ml' ? '(ന്യായവില Sec 28A)' : '(Sec 28A)'}:</strong> ${node.govt_fair_value}</div>` : ''}
        </div>
      `;
    }

    return `
      <div class="timeline-item ${statusClass}">
        <div class="timeline-marker">${markerIcon}</div>
        <div class="timeline-node-card">
          <div class="timeline-node-header">
            <div class="timeline-doc-title">
              <span class="timeline-year-tag">${node.year}</span>
              <span>${node.deed_type}</span>
              <span style="font-weight:400; color:#66605c; font-size: var(--fs-12);">${currentLanguage === 'ml' && node.deed_malayalam ? `(${node.deed_malayalam})` : ''}</span>
            </div>
            <div style="display:flex; align-items:center; gap:0.35rem;">
              <span class="timeline-extent-tag">${node.extent_cents} Cents</span>
              <span style="font-size: var(--fs-12); background:#f6ede2; padding:1px 5px; border-radius:4px; color:#66605c;">Doc #${node.doc_number}</span>
            </div>
          </div>

          <div class="timeline-parties">
            <span><strong>From:</strong> ${node.from_parties.join(", ")}</span>
            <span class="timeline-party-arrow">→</span>
            <span><strong>To:</strong> ${node.to_parties.join(", ")}</span>
            <span style="color:#66605c; font-size: var(--fs-12);">· SRO ${node.sro}</span>
          </div>

          ${node.notes ? `<div style="font-size: var(--fs-12); color:#66605c; margin-top:2px;"><em>${node.notes}</em></div>` : ''}
          ${financialHtml}
          ${flagsHtml}
        </div>
      </div>
    `;
  }).join("");

  let waHtml = "";
  const waInquiry = (currentLanguage === 'en' && data.whatsapp_inquiry_en) ? data.whatsapp_inquiry_en : data.whatsapp_inquiry;
  if (waInquiry) {
    const safeWa = waInquiry.replace(/'/g, "\\'").replace(/"/g, '&quot;');
    const waEncoded = encodeURIComponent(waInquiry);
    waHtml = `
      <div class="whatsapp-card" style="margin-top:1rem;">
        <div class="whatsapp-header">
          <div class="whatsapp-title">${currentLanguage === 'ml' ? 'വിൽപ്പനക്കാരനോട് ചോദിക്കേണ്ട ചോദ്യങ്ങൾ (WhatsApp):' : 'WhatsApp Inquiry for Broker / Seller:'}</div>
          <div class="whatsapp-actions">
            <button class="copy-btn" onclick="copyWhatsApp(this)">Copy Draft</button>
            <a class="wa-direct-btn" href="https://api.whatsapp.com/send?text=${waEncoded}" target="_blank" rel="noopener noreferrer">Send WhatsApp</a>
          </div>
        </div>
        <div class="whatsapp-text">${waInquiry}</div>
      </div>
    `;
  }

  let finTransHtml = "";
  if (data.financial_transparency) {
    const ft = data.financial_transparency;
    finTransHtml = `
      <div class="financial-transparency-card" style="margin-bottom:0.85rem; padding:0.75rem 0.9rem; background:linear-gradient(135deg, #eef5f5 0%, #eef5f5 100%); border:1px solid #a8cfd1; border-radius:8px; box-shadow:0 1px 3px rgba(0,0,0,0.04);">
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:6px; flex-wrap:wrap; gap:6px;">
          <div style="display:flex; align-items:center; gap:6px;">
            <span style="font-size: var(--fs-16);">₹</span>
            <span style="font-weight:700; color:#0a5c63; font-size: var(--fs-14);">Public Purchase Price & Valuation Intelligence</span>
            <span style="background:#a8cfd1; color:#0d7680; font-size: var(--fs-12); font-weight:700; padding:1px 7px; border-radius:10px;">SRO PUBLIC RECORD</span>
          </div>
          <span style="font-size: var(--fs-12); color:#0d7680; font-weight:600;">Registration Act 1908 (Sec 51) · Book 1</span>
        </div>

        <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(180px, 1fr)); gap:6px; margin-top:6px; font-size: var(--fs-12);">
          <div style="background:white; padding:6px 9px; border-radius:6px; border:1px solid #dcebec;">
            <div style="color:#66605c; font-size: var(--fs-12); font-weight:600;">LAST REGISTERED PURCHASE PRICE</div>
            <div style="font-weight:800; color:#990f3d; font-size: var(--fs-16); margin-top:1px;">${ft.last_purchase_price}</div>
            <div style="color:#66605c; font-size: var(--fs-12);">by ${ft.last_buyer} (${ft.last_purchase_year})</div>
          </div>
          <div style="background:white; padding:6px 9px; border-radius:6px; border:1px solid #dcebec;">
            <div style="color:#66605c; font-size: var(--fs-12); font-weight:600;">HISTORICAL RATE & FAIR VALUE</div>
            <div style="font-weight:800; color:#0f5499; font-size: var(--fs-14); margin-top:1px;">${ft.historical_rate_per_cent}</div>
            <div style="color:#66605c; font-size: var(--fs-12);">Govt Fair Value: ${ft.current_govt_fair_value}</div>
          </div>
          <div style="background:white; padding:6px 9px; border-radius:6px; border:1px solid #dcebec;">
            <div style="color:#66605c; font-size: var(--fs-12); font-weight:600;">ACTIVE BANK LIEN (SRO EC)</div>
            <div style="font-weight:800; color:${ft.active_bank_lien_inr.includes('Nil') ? '#0d7680' : '#990f3d'}; font-size: var(--fs-14); margin-top:1px;">${ft.active_bank_lien_inr}</div>
            <div style="color:#66605c; font-size: var(--fs-12);">${ft.active_bank_lien_inr.includes('Nil') ? '✓ Clean 30-Yr Search' : '■ Undischarged Gehan Mortgage'}</div>
          </div>
        </div>

        <div style="margin-top:7px; font-size: var(--fs-12); color:#0d7680; line-height:1.4;">
          <strong>Pricing Intelligence:</strong> ${ft.market_price_context}
        </div>
        <div style="margin-top:4px; font-size: var(--fs-12); color:#a35c00; line-height:1.35;">
          ▲ <strong>Kerala Stamp Act Sec 45A:</strong> ${ft.undervaluation_warning}
        </div>
      </div>
    `;
  }

  const cardHtml = `
    <div class="timeline-card">
      <div class="timeline-card-header">
        <div class="timeline-title-group">
          <div class="timeline-title">
            <span>§</span>
            <span>${currentLanguage === "ml" ? "30 വർഷത്തെ മുന്നാധാര ശൃംഖല (മാതൃക)" : "30-year title chain (sample)"}</span>
          </div>
          <div class="timeline-subtitle">${data.property_identifier}</div>
        </div>
        <div class="deed-score-badge ${scoreClass}">
          <span aria-hidden="true">${scoreIcon}</span>
          <span>${score}/100 · ${data.risk_verdict}</span>
        </div>
      </div>

      <div class="timeline-preset-bar">
        <button class="timeline-preset-btn ${currentPreset === 'aluva_broken' ? 'active' : ''}" onclick="openOwnershipTimeline('aluva_broken')">
          ■ Aluva (3 Red-Flag Traps)
        </button>
        <button class="timeline-preset-btn ${currentPreset === 'kakkanad_wetland' ? 'active' : ''}" onclick="openOwnershipTimeline('kakkanad_wetland')">
          Kakkanad (Wetland & Minor Share)
        </button>
        <button class="timeline-preset-btn ${currentPreset === 'clean_title' ? 'active' : ''}" onclick="openOwnershipTimeline('clean_title')">
          ● No gaps found (39 Yrs)
        </button>
      </div>

      <div style="background:${data.chain_intact ? '#eef5f5' : '#fbebee'}; border:1px solid ${data.chain_intact ? '#a8cfd1' : '#f0c2cf'}; border-radius:8px; padding:0.6rem 0.8rem; font-size: var(--fs-12); color:${data.chain_intact ? '#0d7680' : '#7c0c32'}; margin-bottom:0.75rem;">
        <strong>Audit Summary:</strong> ${data.summary}
      </div>

      ${finTransHtml}

      <div class="timeline-track">
        ${nodesHtml}
      </div>

      ${waHtml}

      <div class="timeline-actions">
        <button class="timeline-btn primary" onclick="locateTimelineOnMap('${currentPreset}')">
          <span>View Region on Satellite</span>
        </button>
        <button class="timeline-btn" onclick="toggleChecklist(true)">
          <span>On-Site Checklist</span>
        </button>
        <button class="timeline-btn" onclick="exportDossierPDF('${currentPreset}')" title="Download Publication-Grade Advocate Legal PDF Report">
          <span>Download Advocate PDF</span>
        </button>
        <button class="timeline-btn" onclick="window.print()" title="Print this view">
          <span>Print</span>
        </button>
      </div>
    </div>
  `;

  container.innerHTML = cardHtml;
  log.scrollTop = log.scrollHeight;
}

function locateTimelineOnMap(preset) {
  if (currentViewMode === "chat") {
    setViewMode("split");
  }
  if (preset === "kakkanad_wetland") {
    applyLocationPreset("kakkanad");
  } else {
    applyLocationPreset("aluva");
  }
}

function switchActionCategory(cat) {
  document.querySelectorAll(".category-tab").forEach(tab => {
    tab.classList.toggle("active", tab.dataset.cat === cat);
  });
  document.querySelectorAll(".chips-bar .chip[data-cat]").forEach(chip => {
    if (cat === "all" || chip.dataset.cat === cat) {
      chip.style.display = "inline-flex";
    } else {
      chip.style.display = "none";
    }
  });
}
