const log = document.getElementById("log");
const form = document.getElementById("form");
const input = document.getElementById("input");
const sendBtn = document.getElementById("send-btn");

let currentViewMode = "split";
let currentLanguage = localStorage.getItem("kandezhuthu_lang") || "en";
// Demo mode (server started with KANDEZ_FIXTURES): sample deeds, presets and timelines.
let DEMO_MODE = false;

// Strings live in static/i18n/<lang>.json; loadTranslations() fills this before the UI starts.
const TRANSLATIONS = { en: {}, ml: {} };

async function loadTranslations() {
  await Promise.all(Object.keys(TRANSLATIONS).map(async lang => {
    const res = await fetch(`/static/i18n/${lang}.json`);
    if (res.ok) TRANSLATIONS[lang] = await res.json();
  }));
}

function setLanguage(lang) {
  currentLanguage = lang;
  localStorage.setItem("kandezhuthu_lang", lang);

  const t = TRANSLATIONS[lang] || TRANSLATIONS.en;

  const btnEn = document.getElementById("lang-btn-en");
  const btnMl = document.getElementById("lang-btn-ml");
  if (btnEn) btnEn.classList.toggle("active", lang === "en");
  if (btnMl) btnMl.classList.toggle("active", lang === "ml");

  const elBrandTitle = document.getElementById("brand-title");
  if (elBrandTitle) elBrandTitle.textContent = t.brandTitle;
  const elBrandSub = document.getElementById("brand-subtitle");
  if (elBrandSub) elBrandSub.textContent = t.brandSubtitle;
  const elBadgeKerala = document.getElementById("badge-kerala");
  if (elBadgeKerala) elBadgeKerala.textContent = t.badgeKerala;

  const btnViewChat = document.getElementById("view-btn-chat");
  if (btnViewChat) btnViewChat.textContent = t.viewChat;
  const btnViewSplit = document.getElementById("view-btn-split");
  if (btnViewSplit) btnViewSplit.textContent = t.viewSplit;
  const btnViewMap = document.getElementById("view-btn-map");
  if (btnViewMap) btnViewMap.textContent = t.viewMap;

  const wf1 = document.getElementById("wf-text-1");
  if (wf1) wf1.textContent = t.wf1;
  const wf2 = document.getElementById("wf-text-2");
  if (wf2) wf2.textContent = t.wf2;
  const wf3 = document.getElementById("wf-text-3");
  if (wf3) wf3.textContent = t.wf3;
  const wf4 = document.getElementById("wf-text-4");
  if (wf4) wf4.textContent = t.wf4;
  if (typeof updateStepNavBar === "function") updateStepNavBar();

  const btnTimeline = document.getElementById("btn-timeline-text");
  if (btnTimeline) btnTimeline.textContent = t.btnTimeline;
  const btnPdf = document.getElementById("btn-pdf-text");
  if (btnPdf) btnPdf.textContent = t.btnPdf;

  const elDropOverlayTitle = document.getElementById("drop-overlay-title");
  if (elDropOverlayTitle) elDropOverlayTitle.textContent = t.dropOverlayTitle;
  const elDropOverlaySub = document.getElementById("drop-overlay-subtitle");
  if (elDropOverlaySub) elDropOverlaySub.textContent = t.dropOverlaySubtitle;
  const elDropBadgeEc = document.getElementById("drop-badge-ec");
  if (elDropBadgeEc) elDropBadgeEc.textContent = lang === "ml" ? "കുടിക്കട സർട്ടിഫിക്കറ്റ്" : "Encumbrance Certificate (EC)";

  const tabLineage = document.getElementById("cat-tab-lineage");
  if (tabLineage) tabLineage.textContent = t.tabLineage;
  const tabStatutory = document.getElementById("cat-tab-statutory");
  if (tabStatutory) tabStatutory.textContent = t.tabStatutory;
  const tabKpbr = document.getElementById("cat-tab-kpbr");
  if (tabKpbr) tabKpbr.textContent = t.tabKpbr;
  const tabField = document.getElementById("cat-tab-field");
  if (tabField) tabField.textContent = t.tabField;
  const tabAll = document.getElementById("cat-tab-all");
  if (tabAll) tabAll.textContent = t.tabAll;

  const chipAluva = document.getElementById("chip-timeline-aluva");
  if (chipAluva && t.chips.timelineAluva) chipAluva.textContent = t.chips.timelineAluva;
  const chipKakkanad = document.getElementById("chip-timeline-kakkanad");
  if (chipKakkanad && t.chips.timelineKakkanad) chipKakkanad.textContent = t.chips.timelineKakkanad;
  const chipClean = document.getElementById("chip-timeline-clean");
  if (chipClean && t.chips.timelineClean) chipClean.textContent = t.chips.timelineClean;
  const chipFairValue = document.getElementById("chip-fair-value");
  if (chipFairValue && t.chips.fairValue) chipFairValue.textContent = t.chips.fairValue;
  const chipSampleDeed = document.getElementById("chip-sample-deed");
  if (chipSampleDeed && t.chips.sampleDeed) chipSampleDeed.textContent = t.chips.sampleDeed;
  const chipSampleEc = document.getElementById("chip-sample-ec");
  if (chipSampleEc && t.chips.sampleEc) chipSampleEc.textContent = t.chips.sampleEc;
  const chipUploadDeed = document.getElementById("chip-upload-deed");
  if (chipUploadDeed && t.chips.uploadDeed) chipUploadDeed.textContent = t.chips.uploadDeed;
  const chipSec45a = document.getElementById("chip-sec45a");
  if (chipSec45a && t.chips.sec45a) chipSec45a.textContent = t.chips.sec45a;
  const chipMaryRoy = document.getElementById("chip-mary-roy");
  if (chipMaryRoy && t.chips.maryRoy) chipMaryRoy.textContent = t.chips.maryRoy;
  const chipEcMortgage = document.getElementById("chip-ec-mortgage");
  if (chipEcMortgage && t.chips.ecMortgage) chipEcMortgage.textContent = t.chips.ecMortgage;
  const chipPathway = document.getElementById("chip-pathway");
  if (chipPathway && t.chips.pathway) chipPathway.textContent = t.chips.pathway;
  const chipWetland = document.getElementById("chip-wetland");
  if (chipWetland && t.chips.wetland) chipWetland.textContent = t.chips.wetland;
  const chipKpbr = document.getElementById("chip-kpbr");
  if (chipKpbr && t.chips.kpbr) chipKpbr.textContent = t.chips.kpbr;
  const chipForm6 = document.getElementById("chip-form6");
  if (chipForm6 && t.chips.form6) chipForm6.textContent = t.chips.form6;
  const chipSurveyKallu = document.getElementById("chip-survey-kallu");
  if (chipSurveyKallu && t.chips.surveyKallu) chipSurveyKallu.textContent = t.chips.surveyKallu;
  const chipMeasureRoad = document.getElementById("chip-measure-road");
  if (chipMeasureRoad && t.chips.measureRoad) chipMeasureRoad.textContent = t.chips.measureRoad;
  const chipDemarcatePlot = document.getElementById("chip-demarcate-plot");
  if (chipDemarcatePlot && t.chips.demarcatePlot) chipDemarcatePlot.textContent = t.chips.demarcatePlot;
  const chipCheckElevation = document.getElementById("chip-check-elevation");
  if (chipCheckElevation && t.chips.checkElevation) chipCheckElevation.textContent = t.chips.checkElevation;
  const chipSwitchMapView = document.getElementById("chip-switch-map-view");
  if (chipSwitchMapView && t.chips.switchMapView) chipSwitchMapView.textContent = t.chips.switchMapView;
  const chipOpenChecklist = document.getElementById("chip-open-checklist");
  if (chipOpenChecklist && t.chips.openChecklist) chipOpenChecklist.textContent = t.chips.openChecklist;
  const chipWaInquiry = document.getElementById("chip-wa-inquiry");
  if (chipWaInquiry && t.chips.waInquiry) chipWaInquiry.textContent = t.chips.waInquiry;
  const chipExportDossier = document.getElementById("chip-export-dossier");
  if (chipExportDossier && t.chips.exportDossier) chipExportDossier.textContent = t.chips.exportDossier;
  const chipRestartDiligence = document.getElementById("chip-restart-diligence");
  if (chipRestartDiligence && t.chips.restartDiligence) chipRestartDiligence.textContent = t.chips.restartDiligence;

  const elDzTag = document.getElementById("dropzone-tag");
  if (elDzTag) elDzTag.textContent = t.dropzoneTag;
  const elDzModelTag = document.getElementById("dropzone-model-tag");
  if (elDzModelTag) elDzModelTag.textContent = t.dropzoneModelTag;
  const elDzToggleBtn = document.getElementById("dropzone-toggle-btn");
  if (elDzToggleBtn) {
    const isMin = document.getElementById("deed-dropzone-container")?.classList.contains("minimized");
    elDzToggleBtn.textContent = isMin ? t.dropzoneExpand : t.dropzoneMinimize;
  }
  const elDzTitle = document.getElementById("dropzone-title");
  if (elDzTitle) elDzTitle.textContent = t.dropzoneTitle;
  const elDemoTag = document.getElementById("demo-tag");
  if (elDemoTag) elDemoTag.textContent = t.demoTag;
  const elSamplesLabel = document.getElementById("start-samples-label");
  if (elSamplesLabel) elSamplesLabel.textContent = t.samplesLabel;
  const elDzDesc = document.getElementById("dropzone-desc");
  if (elDzDesc) elDzDesc.textContent = t.dropzoneDesc;
  const elDzLang = document.getElementById("dropzone-pill-lang");
  if (elDzLang) elDzLang.textContent = t.dropzonePillLang;
  const dropzonePillPhotos = document.getElementById("dropzone-pill-photos");
  if (dropzonePillPhotos) dropzonePillPhotos.textContent = t.dropzonePillPhotos;

  const cardBadgeDeed = document.getElementById("card-badge-deed");
  if (cardBadgeDeed) cardBadgeDeed.textContent = t.cardDeedBadge;
  const cardTitleDeed = document.getElementById("card-title-deed");
  if (cardTitleDeed) cardTitleDeed.textContent = t.cardDeedTitle;
  const cardDescDeed = document.getElementById("card-desc-deed");
  if (cardDescDeed) cardDescDeed.textContent = t.cardDeedDesc;
  const cardCtaDeed = document.getElementById("card-cta-deed");
  if (cardCtaDeed) cardCtaDeed.textContent = t.cardDeedCta;

  const cardBadgeEc = document.getElementById("card-badge-ec");
  if (cardBadgeEc) cardBadgeEc.textContent = t.cardEcBadge;
  const cardTitleEc = document.getElementById("card-title-ec");
  if (cardTitleEc) cardTitleEc.textContent = t.cardEcTitle;
  const cardDescEc = document.getElementById("card-desc-ec");
  if (cardDescEc) cardDescEc.textContent = t.cardEcDesc;
  const cardCtaEc = document.getElementById("card-cta-ec");
  if (cardCtaEc) cardCtaEc.textContent = t.cardEcCta;

  const cardBadgeUpload = document.getElementById("card-badge-upload");
  if (cardBadgeUpload) cardBadgeUpload.textContent = t.cardUploadBadge;
  const cardTitleUpload = document.getElementById("card-title-upload");
  if (cardTitleUpload) cardTitleUpload.textContent = t.cardUploadTitle;
  const cardDescUpload = document.getElementById("card-desc-upload");
  if (cardDescUpload) cardDescUpload.textContent = t.cardUploadDesc;
  const cardCtaUpload = document.getElementById("card-cta-upload");
  if (cardCtaUpload) cardCtaUpload.textContent = t.cardUploadCta;

  const btnBrowse = document.getElementById("btn-browse-text");
  if (btnBrowse) btnBrowse.textContent = t.btnBrowse;
  const btnSampleDeedTxt = document.getElementById("btn-sample-deed-text");
  if (btnSampleDeedTxt) btnSampleDeedTxt.textContent = t.btnSampleDeed;
  const btnSampleEcTxt = document.getElementById("btn-sample-ec-text");
  if (btnSampleEcTxt) btnSampleEcTxt.textContent = t.btnSampleEc;
  const btnDownloadDeedTxt = document.getElementById("btn-download-deed-text");
  if (btnDownloadDeedTxt) btnDownloadDeedTxt.textContent = t.btnDownloadDeedText;

  const elWelcomeTitle = document.getElementById("welcome-bubble-title");
  if (elWelcomeTitle) elWelcomeTitle.textContent = t.welcomeTitle;
  const elWelcomeP1 = document.getElementById("welcome-bubble-p1");
  if (elWelcomeP1) elWelcomeP1.innerHTML = t.welcomeP1;

  const qp1 = document.getElementById("quick-prompt-1");
  if (qp1) qp1.innerHTML = `${t.quickPrompt1}`;
  const qp2 = document.getElementById("quick-prompt-2");
  if (qp2) qp2.innerHTML = `${t.quickPrompt2}`;
  const qp3 = document.getElementById("quick-prompt-3");
  if (qp3) qp3.innerHTML = `${t.quickPrompt3}`;

  const pwaStatusText = document.getElementById("pwa-status-text");
  if (pwaStatusText) {
    pwaStatusText.textContent = navigator.onLine ? t.pwaOnline : t.pwaOffline;
  }

  const toolAutoDemarcate = document.getElementById("tool-auto-demarcate");
  if (toolAutoDemarcate) toolAutoDemarcate.textContent = t.btnAutoDemarcate;
  const btnBhunaksha = document.getElementById("btn-bhunaksha");
  if (btnBhunaksha) btnBhunaksha.textContent = t.btnBhunaksha;
  const btnDatabank = document.getElementById("btn-databank");
  if (btnDatabank) btnDatabank.textContent = t.btnDatabank;

  const elInput = document.getElementById("input");
  if (elInput) elInput.placeholder = t.inputPlaceholder;
  const elSendBtn = document.getElementById("send-btn-text");
  if (elSendBtn) elSendBtn.textContent = t.sendBtn;

  const elMapTitle = document.getElementById("map-header-title");
  if (elMapTitle) elMapTitle.textContent = t.mapHeaderTitle;
  const optPresetDefault = document.getElementById("opt-preset-default");
  if (optPresetDefault) optPresetDefault.textContent = t.presetDefault;
  const elMapSearch = document.getElementById("map-search");
  if (elMapSearch) elMapSearch.placeholder = t.mapSearchPlaceholder;

  // Preset dropdown options
  const presetSel = document.getElementById("preset-select");
  if (presetSel && t.presets) {
    for (const opt of presetSel.options) {
      if (opt.value === "" && t.presets.default) opt.textContent = t.presets.default;
      else if (t.presets[opt.value]) opt.textContent = t.presets[opt.value];
    }
  }

  // Layer dropdown options
  const layerSel = document.getElementById("layer-select");
  if (layerSel && t.layers) {
    for (const opt of layerSel.options) {
      if (t.layers[opt.value]) opt.textContent = t.layers[opt.value];
    }
  }

  const elToolPin = document.getElementById("tool-pin");
  if (elToolPin) elToolPin.textContent = t.toolPin;
  const elToolPlot = document.getElementById("tool-plot");
  if (elToolPlot) elToolPlot.textContent = t.toolPlot;
  const elToolRoad = document.getElementById("tool-road");
  if (elToolRoad) elToolRoad.textContent = t.toolRoad;
  const elBtnUndo = document.getElementById("btn-undo");
  if (elBtnUndo) elBtnUndo.textContent = t.btnUndo;
  const elBtnClear = document.getElementById("btn-clear");
  if (elBtnClear) elBtnClear.textContent = t.btnClear;
  const elBtnChk = document.getElementById("btn-chk-text");
  if (elBtnChk) elBtnChk.textContent = t.btnChecklist;

  const elBtnGuidanceAuto = document.getElementById("btn-guidance-auto-demarcate");
  if (elBtnGuidanceAuto) elBtnGuidanceAuto.textContent = t.btnGuidanceAutoDemarcate;

  updateGuidanceBarText();

  // Floating HUD text & labels
  const elHudLiveTag = document.getElementById("hud-live-tag");
  if (elHudLiveTag) elHudLiveTag.textContent = t.hudLiveTag;
  const elHudCoords = document.getElementById("hud-lbl-coords");
  if (elHudCoords) elHudCoords.textContent = t.hudCoords;
  const elHudExtentTitle = document.getElementById("hud-extent-lbl-title");
  if (elHudExtentTitle) elHudExtentTitle.textContent = t.hudExtentLabel;
  const elHudExtentSub = document.getElementById("hud-extent-lbl-sub");
  if (elHudExtentSub) elHudExtentSub.textContent = t.hudCentsLabel;
  const elHudArea = document.getElementById("hud-lbl-area");
  if (elHudArea) elHudArea.textContent = t.hudArea;
  const elHudRoad = document.getElementById("hud-lbl-road");
  if (elHudRoad) elHudRoad.textContent = t.hudRoad;
  const elHudElevTitle = document.getElementById("hud-elevation-lbl-title");
  if (elHudElevTitle) elHudElevTitle.textContent = t.hudElevationLabel;
  const elHudElevSub = document.getElementById("hud-elevation-lbl-sub");
  if (elHudElevSub) elHudElevSub.textContent = t.hudMslLabel;

  const elBtnHudAuditor = document.getElementById("btn-hud-auditor") || document.getElementById("btn-hud-send");
  if (elBtnHudAuditor) elBtnHudAuditor.textContent = t.btnHudSend;
  const elBtnHudExport = document.getElementById("btn-hud-export");
  if (elBtnHudExport) elBtnHudExport.textContent = t.btnHudExport;
  const elBtnGmaps = document.getElementById("btn-hud-maps") || document.getElementById("btn-open-gmaps");
  if (elBtnGmaps) elBtnGmaps.textContent = t.btnOpenGmaps;

  // Refresh active HUD numbers & units
  refreshHUDLanguage();

  const elChkTitle = document.getElementById("chk-panel-title");
  if (elChkTitle) elChkTitle.textContent = t.chkPanelTitle;
  const elChkKallu = document.getElementById("chk-lbl-kallu");
  if (elChkKallu) elChkKallu.innerHTML = t.chkKallu;
  const elChkRoad = document.getElementById("chk-lbl-road");
  if (elChkRoad) elChkRoad.innerHTML = t.chkRoad;
  const elChkWetland = document.getElementById("chk-lbl-wetland");
  if (elChkWetland) elChkWetland.innerHTML = t.chkWetland;
  const elChkHt = document.getElementById("chk-lbl-ht");
  if (elChkHt) elChkHt.innerHTML = t.chkHt;
  const elChkFlood = document.getElementById("chk-lbl-flood");
  if (elChkFlood) elChkFlood.innerHTML = t.chkFlood;
  const elChkHint = document.getElementById("chk-hint");
  if (elChkHint) elChkHint.textContent = t.chkHint;


  // Refresh any currently rendered cards in DOM
  document.querySelectorAll(".whatsapp-card").forEach(card => {
    const titleEl = card.querySelector(".whatsapp-title");
    if (titleEl) {
      if (lang === "en") {
        if (titleEl.textContent.includes("വാട്സാപ്പ്") || titleEl.textContent.includes("ചോദ്യം") || titleEl.textContent.includes("Malayalam")) {
          titleEl.textContent = (titleEl.textContent.includes("ബാങ്ക്") || titleEl.textContent.includes("NOC"))
            ? "WhatsApp Inquiry for Bank NOC / Release Deed"
            : ((titleEl.textContent.includes("ബ്രോക്കർ") || titleEl.textContent.includes("Broker"))
              ? "WhatsApp Inquiry for Broker / Seller:"
              : "WhatsApp Inquiry for Seller / Broker:");
        }
      } else {
        if (titleEl.textContent.includes("Inquiry") || titleEl.textContent.includes("Seller")) {
          titleEl.textContent = (titleEl.textContent.includes("NOC") || titleEl.textContent.includes("Bank"))
            ? "ബാങ്ക് NOC / ഒഴിവുമുറിക്കായുള്ള വാട്സാപ്പ് സന്ദേശം"
            : (titleEl.textContent.includes("Broker")
              ? "വിൽപ്പനക്കാരനോട് ചോദിക്കേണ്ട ചോദ്യങ്ങൾ (WhatsApp):"
              : "വിൽപ്പനക്കാരനോട് ചോദിക്കേണ്ട ചോദ്യം (WhatsApp):");
        }
      }
    }
  });

  document.querySelectorAll(".boundary-title").forEach(el => {
    el.textContent = lang === "ml" ? "നാലതിരുകൾ (ചതുരതിരുകൾ):" : "Four Boundaries Schedule:";
  });

  document.querySelectorAll(".prior-title").forEach(el => {
    el.textContent = lang === "ml" ? "മുന്നാധാര വിവരങ്ങൾ (Prior Title Lineage):" : "Prior Title Lineage:";
  });

  if (typeof setWorkflowStep === "function") {
    setWorkflowStep(currentWorkflowStep);
  }
}

function getLocalizedBasinName(basinStr, isMl) {
  if (!basinStr) return isMl ? "പ്രാദേശിക നീർത്തടം" : "Local Watershed";
  if (!isMl) return basinStr;
  const mlMap = {
    "Periyar River Basin": "പെരിയാർ നദീതടം",
    "Chitrapuzha / Kadambrayar Basin (Elevated Midlands)": "ചിത്രപ്പുഴ / കടമ്പ്രയാർ തടം (ഉയർന്ന പ്രദേശം)",
    "Vembanad Wetland / Pamba-Meenachil Estuary": "വേമ്പനാട് കായൽ / പമ്പ-മീനച്ചിൽ തടം",
    "Kallada River Plain": "കല്ലട നദീതടം",
    "Bharathapuzha River Basin": "ഭാരതപ്പുഴ നദീതടം",
    "Karamana / Killi River Basin": "കരമന / കിള്ളിയാർ നദീതടം",
    "Chaliyar River Basin": "ചാലിയാർ നദീതടം",
    "Kadalundi River Basin": "കടലുണ്ടിപ്പുഴ തടം",
    "Valapattanam River Basin": "വളപട്ടണം പുഴത്തടം"
  };
  return mlMap[basinStr] || (basinStr.replace(/River Basin|Basin/gi, "").trim() + " നദീതടം");
}

function refreshHUDLanguage() {
  const t = TRANSLATIONS[currentLanguage] || TRANSLATIONS.en;
  const isMl = currentLanguage === "ml";

  // Locality title
  const locTitle = document.getElementById("hud-locality-title");
  if (locTitle && (locTitle.textContent.includes("Aluva") || locTitle.textContent.includes("ആലുവ"))) {
    locTitle.textContent = isMl ? "ആലുവ, എറണാകുളം ജില്ല" : "Aluva, Ernakulam District";
  }

  // Refresh cents display
  const centsEl = document.getElementById("hud-cents");
  if (centsEl && centsEl.textContent) {
    const numMatch = centsEl.textContent.match(/[\d.]+/);
    if (numMatch) {
      centsEl.textContent = `${numMatch[0]} ${t.hudCentsUnit}`;
    }
  }

  // Refresh sqm / ares display
  const sqmEl = document.getElementById("hud-sqm");
  if (sqmEl && sqmEl.textContent) {
    const aresMatch = sqmEl.textContent.match(/([\d.]+)\s*(?:Ares|ആർ)/i) || sqmEl.textContent.match(/([\d.]+)/);
    const sqmMatch = sqmEl.textContent.match(/([\d.]+)\s*(?:m²|ച\.മീ\.)/i);
    if (aresMatch && sqmMatch) {
      sqmEl.textContent = `${aresMatch[1]} ${t.hudAresUnit} (${sqmMatch[1]} ${t.hudSqMUnit})`;
    } else if (aresMatch) {
      const aVal = parseFloat(aresMatch[1]);
      const sVal = (aVal * 100).toFixed(1);
      sqmEl.textContent = `${aVal.toFixed(2)} ${t.hudAresUnit} (${sVal} ${t.hudSqMUnit})`;
    }
  }

  // Refresh road text & badge
  const roadTextEl = document.getElementById("hud-road-text");
  if (roadTextEl && roadTextEl.textContent) {
    const rMatch = roadTextEl.textContent.match(/[\d.]+/);
    if (rMatch) {
      roadTextEl.textContent = `${rMatch[0]} ${t.hudMetersUnit}`;
    }
  }
  const roadBadgeEl = document.getElementById("hud-road-badge");
  if (roadBadgeEl) {
    if (roadBadgeEl.classList.contains("pass")) roadBadgeEl.textContent = t.hudRoadPass;
    else if (roadBadgeEl.classList.contains("warn")) roadBadgeEl.textContent = t.hudRoadWarn;
    else if (roadBadgeEl.classList.contains("fail")) roadBadgeEl.textContent = t.hudRoadFail;
  }

  // Refresh elevation text & flood badge
  const elevTextEl = document.getElementById("hud-elevation-text");
  if (elevTextEl && elevTextEl.textContent) {
    const eMatch = elevTextEl.textContent.match(/[\d.]+/);
    if (eMatch) {
      const isEstimate = elevTextEl.textContent.startsWith("≈");
      const isMl = currentLanguage === "ml";
      elevTextEl.textContent = `${isEstimate ? "≈" : ""}${eMatch[0]} ${t.hudMslUnit}${isEstimate ? (isMl ? " (ഏകദേശം)" : " (rough estimate)") : ""}`;
    }
  }
  const floodBadgeEl = document.getElementById("hud-flood-badge");
  if (floodBadgeEl) {
    if (floodBadgeEl.classList.contains("pass")) floodBadgeEl.textContent = t.hudElevationRiskLow;
    else if (floodBadgeEl.classList.contains("warn")) floodBadgeEl.textContent = t.hudElevationRiskMod;
    else if (floodBadgeEl.classList.contains("fail")) floodBadgeEl.textContent = t.hudElevationRiskHigh;
  }

  // Refresh basin text
  const basinEl = document.getElementById("hud-basin-text");
  if (basinEl && window.currentElevationData) {
    const data = window.currentElevationData;
    const basinName = getLocalizedBasinName(data.river_basin, isMl);
    basinEl.textContent = `${basinName} • ${t.hudBasinPlinth} ≥${data.recommended_plinth_height_m}m`;
  } else if (basinEl) {
    basinEl.textContent = isMl
      ? 'പെരിയാർ നദീതടം • തറ ഉയരം: ≥0.75 മീറ്റർ'
      : 'Periyar River Basin • Plinth: ≥0.75m';
  }

  // Refresh sample marker popup if open
  if (currentMarker && currentMarker.getPopup() && currentMarker.getPopup().isOpen()) {
    const popContent = currentMarker.getPopup().getContent();
    if (popContent && (popContent.includes("345/1") || popContent.includes("Sample Plot") || popContent.includes("മാതൃകാ പ്ലോട്ട്"))) {
      const title = isMl ? "റീ-സർവേ 345/1 മാതൃകാ പ്ലോട്ട്" : "Re-Sy 345/1 Sample Plot";
      const village = isMl ? "ആലുവ വെസ്റ്റ്" : "Aluva West";
      const syLbl = isMl ? "സർവേ നമ്പർ:" : "Survey:";
      const extLbl = isMl ? "വിസ്തീർണ്ണം:" : "Extent:";
      const centsUnit = isMl ? "സെന്റ്" : "Cents";
      const source = isMl ? "✓ കൃത്യതയുള്ള 10-സെന്റ് അതിർത്തി" : "✓ Calibrated 10-Cent Footprint";
      currentMarker.setPopupContent(`
        <b>${title}</b><br>
        ${syLbl} <strong>345/1</strong> (${village})<br>
        ${extLbl} <strong>10.00 ${centsUnit}</strong> (404.7 m²)<br>
        <small style="color:#990f3d; font-weight:600;">${source}</small>
      `);
    }
  }

  const pwaStatusText = document.getElementById("pwa-status-text");
  if (pwaStatusText && navigator.onLine) {
    pwaStatusText.textContent = isMl ? "ഓൺലൈൻ മോഡ്" : "Online Mode";
  }
}
