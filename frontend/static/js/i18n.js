const log = document.getElementById("log");
const form = document.getElementById("form");
const input = document.getElementById("input");
const sendBtn = document.getElementById("send-btn");

let currentViewMode = "split";
let currentLanguage = localStorage.getItem("kandezhuthu_lang") || "en";

const TRANSLATIONS = {
  en: {
    brandTitle: "Kandezhuthu AI",
    brandSubtitle: "Kerala property title checks",
    badgeKerala: "Kerala Real Estate Guardrail",
    viewChat: "Chat",
    viewSplit: "Split View",
    viewMap: "Map & Satellite",
    wf1: "Document",
    wf2: "Prior deeds",
    wf3: "Site",
    wf4: "Follow-up",
    btnTimeline: "Ownership Timeline",
    btnPdf: "Export PDF",
    dropOverlayTitle: "Drop Scanned Kerala Deed or EC Here",
    dropOverlaySubtitle: "Directly ingests Malayalam/English deed text using Google Cloud Document AI & Gemini Multimodal Vision",
    tabLineage: "Ownership & Lineage",
    tabStatutory: "Statutory Traps",
    tabKpbr: "KPBR Building Rules",
    tabField: "Field Inspection",
    tabAll: "Show All",
    chips: {
      sampleDeed: "Test Kerala Sale Deed (1420/2014)",
      sampleEc: "Test 30-Yr Bank EC (Undisclosed Mortgage)",
      uploadDeed: "Browse / Snap Deed Photo",
      timelineAluva: "Sample: Aluva chain with 3 defects",
      maryRoy: "Mary Roy Coparcenary Defect",
      timelineClean: "Sample: 39-year chain, no gaps found",
      fairValue: "Fair Value & Stamp Duty Audit",
      measureRoad: "Measure Road Width (KPBR 2019)",
      demarcatePlot: "Demarcate & Seal Cadastral Plot",
      checkElevation: "Check Elevation & Flood Exposure",
      switchMapView: "Switch Map View (Hybrid / Satellite)",
      openChecklist: "Open On-Site Field Checklist",
      waInquiry: "WhatsApp Inquiry for Seller",
      exportDossier: "Export Advocate Dossier (PDF)",
      restartDiligence: "↺ Restart Full Diligence",
      timelineKakkanad: "Timeline: Kakkanad Wetland & Minor",
      sec45a: "Sec 45A Undervaluation & Deficit Stamp",
      ecMortgage: "Undischarged Bank Mortgage (EC)",
      pathway: "Pathway & Easement Encumbrances",
      wetland: "Paddy Land & Wetland 2008 Risk",
      kpbr: "Residential Road Width (3m vs 5m)",
      form6: "Form 6 / 27A Fee Slabs",
      surveyKallu: "Survey Boundary Stones"
    },
    chipPrompts: {
      fair_value: "Is historical purchase price a public record in Kerala? How much did the seller buy it for across prior deeds, and how does it compare to Government Notified Fair Value?",
      sec45a: "Explain Kerala Stamp Act Section 45A undervaluation risk: What happens if seller requests registering at a lower consideration than market price?",
      mary_roy: "Audit this partition deed under Mary Roy precedent: Ancestral Syrian Christian land partitioned in 1994 among sons only, excluding sister without registered release deed.",
      ec_mortgage: "Check EC entry: SRO Encumbrance Certificate shows equitable mortgage registered in 2022 with Federal Bank, but seller has no Gehan release deed.",
      pathway: "Scan this deed clause for traps: Schedule: 10 cents in Re-Sy 345/1. 2-meter pathway along southern boundary reserved for party of 2nd part.",
      wetland: "Check this for wetland trap: The property is 12 cents classified as Nilam in prior deed 142/1998, with unregularized dry status.",
      kpbr: "Under Kerala Panchayat Building Rules (KPBR 2019), what is the minimum road access width required to get a residential building permit?",
      form6: "How does the Kerala Conservation of Paddy Land Act Section 27A work? What is the fee slab for Form 6 and who gets the 25-cent free exemption?",
      survey_kallu: "What physical checks must I perform on the ground regarding survey boundary stones, boundaries, and road access before paying an advance?",
      advance_docs: "What documents should I ask the seller for before paying token advance for land in Kerala?",
    },
    dropzoneTag: "Cloud Document AI & Multimodal Vision",
    dropzoneTitle: "Drop a deed or EC here",
    dropzoneDesc: "PDF or photo, English or Malayalam. Or try a sample:",
    dropzoneModelTag: "Instant 1-Click Verification",
    dropzonePillLang: "English & Malayalam OCR",
    dropzonePillPhotos: "Camera Photos (JPG/PNG)",
    dropzoneMinimize: "− Minimize",
    dropzoneExpand: "+ Add document",
    cardDeedBadge: "Sample",
    cardDeedTitle: "Sale deed",
    cardDeedDesc: "Pathway easement, paddy land and a maintenance clause.",
    cardDeedCta: "Scan →",
    cardEcBadge: "Sample",
    cardEcTitle: "30-year EC",
    cardEcDesc: "Finds undisclosed bank mortgages and missing release deeds.",
    cardEcCta: "Scan →",
    cardUploadBadge: "PDF / Photo",
    cardUploadTitle: "Your document",
    cardUploadDesc: "Sale deed, partition deed, agreement or EC.",
    cardUploadCta: "Upload →",
    btnBrowse: "Browse Files",
    btnSampleDeed: "Ingest Sale Deed (PDF)",
    btnSampleEc: "Ingest SRO EC (PDF)",
    btnDownloadDeed: "↓ Download Test Deed",
    btnDownloadDeedText: "↓ Download Test Deed PDF",
    pwaOnline: "Online Mode",
    pwaOffline: "Offline Field Mode",
    quickPrompt1: "What documents should I get from the seller?",
    quickPrompt2: "How do I know if the road is wide enough to get a building permit (KPBR)?",
    quickPrompt3: "How to check if land is listed as Nilam in the 2008 Paddy Land Data Bank?",
    btnAutoDemarcate: "Auto-Demarcate",
    btnBhunaksha: "Outline from extent",
    btnDatabank: "Data Bank",
    welcomeTitle: "Kandezhuthu AI",
    welcomeP1: "Drop a deed or EC above, paste a clause below, or ask a question.",
    inputPlaceholder: "Paste a deed clause or ask a question",
    sendBtn: "Send",
    mapHeaderTitle: "Satellite Inspector",
    presetDefault: "Select Kerala Region...",
    mapSearchPlaceholder: "Search village, town, or lat,lng...",
    toolPin: "Pin Location",
    toolPlot: "Draw Plot (Cents)",
    toolRoad: "Measure Road Width",
    btnUndo: "↩️ Undo",
    btnClear: "Clear",
    btnChecklist: "Checklist",
    guidanceDefault: "Click anywhere on the satellite view to drop an inspection pin and view GPS coordinates.",
    guidancePlot: "Click on map to place plot boundary corner stones (min 3 corners). Click 'Seal Plot' or starting stone to finish.",
    guidanceRoad: "Click 2 points across the access road to measure width under Kerala Panchayat Building Rules (KPBR 2019).",
    guidanceSeal: "✓ Seal Plot",
    btnGuidanceAutoDemarcate: "Auto-Demarcate at Pin",
    hudLiveTag: "Live Plot HUD",
    hudCoords: "Coordinates",
    hudExtentLabel: "Plot Extent",
    hudCentsLabel: "Kerala Cents",
    hudArea: "Area (Revenue Ares & Sq.M)",
    hudRoad: "Road Width (KPBR 2019)",
    hudElevationLabel: "Elevation & Flood Exposure",
    hudMslLabel: "MSL",
    hudCentsUnit: "Cents",
    hudAresUnit: "Ares",
    hudSqMUnit: "m²",
    hudMetersUnit: "meters",
    hudMslUnit: "m MSL",
    hudRoadPass: "✓ KPBR Pass (≥3m)",
    hudRoadWarn: "▲ Small Plot Only",
    hudRoadFail: "✕ Defective Access",
    hudElevationRiskLow: "● Low Flood Risk",
    hudElevationRiskMod: "▲ Moderate Flood Risk",
    hudElevationRiskHigh: "■ High Flood Risk",
    hudElevationRiskCrit: "■ Critical Sub-MSL Trap",
    hudBasinPlinth: "Plinth:",
    btnHudSend: "Send to Auditor",
    btnHudExport: "Export Dossier PDF",
    btnOpenGmaps: "Google Maps",
    chkPanelTitle: "On-Site Field Check Essentials",
    chkKallu: "<strong>Survey Boundary Stones:</strong> Verify all 4 corner stones physically intact on ground.",
    chkRoad: "<strong>Road Access:</strong> Min 3.0m motorable road width for KPBR building permit.",
    chkWetland: "<strong>Wetland Proximity:</strong> Spot paddy fields/canals via satellite layer.",
    chkHt: "<strong>Overhead Lines:</strong> Verify no HT electricity lines cross over the plot.",
    chkFlood: "<strong>Flood Watermarks:</strong> Check compound walls & poles for 2018 monsoon waterlines.",
    chkHint: "Tick items as you verify them on-site with your surveyor.",
    typingAnalysis: "Analyzing property documents, prior title lineage, and Kerala statutes...",
    presets: {
      default: "Select Kerala Region...",
      aluva: "Aluva (Periyar River Basin - 2018 Flood Zone)",
      kakkanad: "Kakkanad / Infopark (Elevated Midlands)",
      kuttanad: "Kuttanad (Sub-Sea-Level Wetland Polders)",
      chengannur: "Chengannur (Pamba River Flood Corridor)",
      angamaly: "Angamaly (Paddy & Agricultural Zone)",
      kaloor: "Kaloor / Kochi (High Density Coastal)",
      thrissur: "Thrissur (Swaraj Round & Kole Wetlands)",
      kottayam: "Kottayam (Meenachil Wetland Valley)",
      kozhikode: "Kozhikode (Coastal City)",
      trivandrum: "Thiruvananthapuram (Kazhakkoottam)"
    },
    layers: {
      "google-hybrid": "Google Satellite Hybrid",
      "google-satellite": "Google Satellite Only",
      "google-roads": "Google Roadmap",
      "google-terrain": "Google Terrain",
      "osm": "OpenStreetMap"
    }
  },
  ml: {
    brandTitle: "കണ്ടെഴുത്ത് AI",
    brandSubtitle: "കേരള ഭൂമി ആധാര പരിശോധന",
    badgeKerala: "കേരള ഭൂമി നിയമ സുരക്ഷ",
    viewChat: "ചാറ്റ്",
    viewSplit: "സ്പ്ലിറ്റ് വ്യൂ",
    viewMap: "മാപ്പ് & സാറ്റലൈറ്റ്",
    wf1: "രേഖ",
    wf2: "മുന്നാധാരം",
    wf3: "സ്ഥലം",
    wf4: "തുടർനടപടി",
    btnTimeline: "മുന്നാധാര ടൈംലൈൻ",
    btnPdf: "PDF എക്സ്പോർട്ട്",
    dropOverlayTitle: "ആധാരമോ കുടിക്കട സർട്ടിഫിക്കറ്റോ ഇവിടെ നൽകുക",
    dropOverlaySubtitle: "ക്ലൗഡ് ഡോക്യുമെന്റ് AI & മൾട്ടിമോഡൽ വിഷൻ വഴി ആധാരങ്ങൾ നേരിട്ട് വായിക്കുന്നു",
    tabLineage: "ഉടമസ്ഥാവകാശവും മുന്നാധാരവും",
    tabStatutory: "നിയമപരമായ ചതിക്കുഴികൾ",
    tabKpbr: "KPBR കെട്ടിട നിർമ്മാണ ചട്ടങ്ങൾ",
    tabField: "സ്ഥല പരിശോധന (ഓൺ-സൈറ്റ്)",
    tabAll: "എല്ലാം കാണിക്കുക",
    chips: {
      sampleDeed: "മാതൃകാ തീറാധാരം (1420/2014)",
      sampleEc: "30-വർഷ ബാങ്ക് കുടിക്കടം (പണയം)",
      uploadDeed: "ആധാരം / ഫോട്ടോ തിരഞ്ഞെടുക്കുക",
      timelineAluva: "മാതൃക: ആലുവ ശൃംഖല (3 കുരുക്കുകൾ)",
      maryRoy: "മേരി റോയ് വിധി: പെൺമക്കളുടെ അവകാശം",
      timelineClean: "മാതൃക: 39 വർഷം, വിടവില്ല",
      fairValue: "ന്യായവില & മുദ്രവില ഓഡിറ്റ്",
      measureRoad: "വഴി വീതി അളക്കുക (KPBR 2019)",
      demarcatePlot: "അതിരുകൾ അടയാളപ്പെടുത്തുക",
      checkElevation: "ഉയരവും വെള്ളപ്പൊക്ക സാധ്യതയും",
      switchMapView: "മാപ്പ് വ്യൂ മാറ്റുക",
      openChecklist: "സ്ഥല പരിശോധനാ ചെക്ക്‌ലിസ്റ്റ്",
      waInquiry: "വിൽപ്പനക്കാരനുള്ള വാട്സാപ്പ് സന്ദേശം",
      exportDossier: "അഡ്വക്കേറ്റ് ലീഗൽ ഡോസിയർ (PDF)",
      restartDiligence: "↺ പരിശോധന വീണ്ടും തുടങ്ങുക",
      timelineKakkanad: "ടൈംലൈൻ: കാക്കനാട് നിലവും മൈനർ ഷെയറും",
      sec45a: "സെക്ഷൻ 45A അണ്ടർവാല്യുവേഷൻ & മുദ്രവില",
      ecMortgage: "ബാങ്ക് ബാധ്യത (കുടിക്കടം)",
      pathway: "വഴിയവകാശം / നടപ്പുവഴി ബാധ്യതകൾ",
      wetland: "2008 നെൽവയൽ-തണ്ണീർത്തട നിയമം (നിലം/പുരയിടം)",
      kpbr: "വീടുപണിക്ക് വേണ്ട വഴി വീതി (3 മീറ്റർ / 5 മീറ്റർ)",
      form6: "ഫോം 6 / 27A തരംമാറ്റ ഫീസ് ഇളവുകൾ",
      surveyKallu: "സർവേ കല്ലുകളും അതിർത്തി പരിശോധനയും"
    },
    chipPrompts: {
      fair_value: "കേരളത്തിൽ മുൻ ആധാരങ്ങളിലെ വില പൊതുരേഖയാണോ? വിൽപ്പനക്കാരൻ മുൻപ് എത്ര രൂപയ്ക്കാണ് ഇത് വാങ്ങിയത്, ഇപ്പോഴത്തെ സർക്കാർ ന്യായവിലയുമായി ഇത് എങ്ങനെ ഒത്തുപോകുന്നു എന്ന് വിശദീകരിക്കാമോ?",
      sec45a: "കേരള മുദ്രപ്പത്ര നിയമം സെക്ഷൻ 45A പ്രകാരമുള്ള കുറഞ്ഞ വില കാണിക്കൽ (അണ്ടർവാല്യുവേഷൻ) പ്രശ്നം എന്താണ്? യഥാർത്ഥ വിലയേക്കാൾ കുറഞ്ഞ തുകയ്ക്ക് ആധാരം രജിസ്റ്റർ ചെയ്താൽ വാങ്ങുന്നയാൾക്ക് എന്ത് ബാധ്യത വരും?",
      mary_roy: "മേരി റോയ് സുപ്രീം കോടതി വിധി പ്രകാരം ഈ ഭാഗപത്രം പരിശോധിക്കുക: 1994-ൽ ക്രിസ്ത്യൻ പിതൃസ്വത്ത് ആൺമക്കൾ മാത്രം വീതിച്ചെടുക്കുകയും സഹോദരിക്ക് ഒഴിമുറി നൽകാതിരിക്കുകയും ചെയ്താൽ ആധാരം സുരക്ഷിതമാണോ?",
      ec_mortgage: "സബ് രജിസ്ട്രാർ ഓഫീസ് കുടിക്കട സർട്ടിഫിക്കറ്റിൽ 2022-ൽ ഫെഡറൽ ബാങ്കിൽ പണയപ്പെടുത്തിയതായി കാണുന്നു, എന്നാൽ ഗഹാൻ ഒഴിവ് ആധാരമില്ല. ഇതിന്റെ അപകടസാധ്യത എന്താണ്?",
      pathway: "ഈ ആധാര വ്യവസ്ഥ പരിശോധിക്കുക: തെക്കേ അതിർത്തിയിലൂടെ രണ്ടാം കക്ഷിക്ക് 2 മീറ്റർ വീതിയിൽ നടപ്പുവഴി അവകാശം നിലനിർത്തിയിരിക്കുന്നു. ഇത് വാങ്ങുന്നയാൾക്ക് തടസ്സമാകുമോ?",
      wetland: "ഈ വസ്തു 1998-ലെ മുന്നാധാരത്തിൽ 'നിലം' എന്നാണ് രേഖപ്പെടുത്തിയിരിക്കുന്നത്, നിലവിൽ കരഭൂമിയാക്കി മാറ്റിയിട്ടില്ല. 2008-ലെ നെൽവയൽ തണ്ണീർത്തട നിയമപ്രകാരം ഇതിന്റെ നിയമസാധുത എന്താണ്?",
      kpbr: "കേരള പഞ്ചായത്ത് കെട്ടിട നിർമ്മാണ ചട്ടങ്ങൾ (KPBR 2019) പ്രകാരം ഒരു വീട് വെയ്ക്കാൻ പെർമിറ്റ് ലഭിക്കുന്നതിന് മിനിമം എത്ര വീതിയുള്ള വഴി വേണം?",
      form6: "2008-ലെ നെൽവയൽ നിയമം സെക്ഷൻ 27A (ഫോം 6) പ്രകാരം ഡാറ്റാ ബാങ്കിൽ ഇല്ലാത്ത ഭൂമി തരംമാറ്റുന്നതിനുള്ള ഫീസ് നിരക്കുകൾ എന്തൊക്കെയാണ്? 25 സെന്റ് വരെയുള്ള സൗജന്യ ഇളവ് ആർക്കൊക്കെ ലഭിക്കും?",
      survey_kallu: "ഭൂമിക്ക് അഡ്വാൻസ് തുക നൽകുന്നതിന് മുൻപ് സർവേ കല്ല്, അതിരുകൾ, റോഡ് പ്രവേശനം എന്നിവയിൽ നേരിട്ട് സ്ഥലത്ത് ചെന്ന് എന്തൊക്കെ പരിശോധിക്കണം?",
      advance_docs: "കേരളത്തിൽ സ്ഥലം വാങ്ങുമ്പോൾ ടോക്കൺ അഡ്വാൻസ് നൽകുന്നതിന് മുൻപ് വിൽപ്പനക്കാരനിൽ നിന്ന് എന്തൊക്കെ രേഖകളാണ് (ആധാരം, മുന്നാധാരം, കുടിക്കടം, ലൊക്കേഷൻ സ്കെച്ച്, നികുതി രസീത്) നിർബന്ധമായും വാങ്ങി പരിശോധിക്കേണ്ടത്?",
    },
    dropzoneTag: "ക്ലൗഡ് ഡോക്യുമെന്റ് AI & മൾട്ടിമോഡൽ വിഷൻ",
    dropzoneTitle: "ആധാരമോ EC-യോ ഇവിടെ ഇടുക",
    dropzoneDesc: "PDF അല്ലെങ്കിൽ ഫോട്ടോ, മലയാളം അല്ലെങ്കിൽ ഇംഗ്ലീഷ്. അല്ലെങ്കിൽ ഒരു മാതൃക നോക്കുക:",
    dropzoneModelTag: "തൽക്ഷണ പരിശോധന",
    dropzonePillLang: "മലയാളം & ഇംഗ്ലീഷ്",
    dropzonePillPhotos: "ക്യാമറ ഫോട്ടോകൾ",
    dropzoneMinimize: "− ചുരുക്കുക",
    dropzoneExpand: "+ രേഖ ചേർക്കുക",
    cardDeedBadge: "മാതൃക",
    cardDeedTitle: "തീറാധാരം",
    cardDeedDesc: "നടപ്പുവഴി, നിലം, സംരക്ഷണ വ്യവസ്ഥ.",
    cardDeedCta: "പരിശോധിക്കുക →",
    cardEcBadge: "മാതൃക",
    cardEcTitle: "30 വർഷത്തെ EC",
    cardEcDesc: "രഹസ്യമായി പണയം വെച്ച ബാങ്ക് ബാധ്യതകളും റിലീസ് ആധാരങ്ങളുടെ കുറവും കണ്ടെത്തുന്നത് കാണുക.",
    cardEcCta: "പരിശോധിക്കുക →",
    cardUploadBadge: "ഫയൽ / ഫോട്ടോ",
    cardUploadTitle: "നിങ്ങളുടെ രേഖ",
    cardUploadDesc: "തീറാധാരം, ഭാഗപത്രം, കരാർ അല്ലെങ്കിൽ EC.",
    cardUploadCta: "അപ്‌ലോഡ് →",
    btnBrowse: "ഫയലുകൾ തിരഞ്ഞെടുക്കുക",
    btnSampleDeed: "മാതൃകാ തീറാധാരം",
    btnSampleEc: "മാതൃകാ കുടിക്കടം",
    btnDownloadDeed: "↓ ടെസ്റ്റ് ആധാരം ഡൗൺലോഡ് ചെയ്യുക",
    btnDownloadDeedText: "↓ ടെസ്റ്റ് ആധാരം ഡൗൺലോഡ് ചെയ്യുക",
    pwaOnline: "ഓൺലൈൻ മോഡ്",
    pwaOffline: "ഓഫ്‌ലൈൻ പരിശോധനാ മോഡ്",
    quickPrompt1: "വിൽപ്പനക്കാരനിൽ നിന്ന് ഏതൊക്കെ രേഖകൾ വാങ്ങണം?",
    quickPrompt2: "വീടുപണിക്ക് അനുമതി ലഭിക്കാൻ വഴിക്ക് എത്ര വീതി വേണം (KPBR ചട്ടങ്ങൾ)?",
    quickPrompt3: "2008-ലെ നെൽവയൽ ഡാറ്റാ ബാങ്കിൽ ഭൂമി 'നിലം' ആണോ എന്ന് എങ്ങനെ പരിശോധിക്കാം?",
    btnAutoDemarcate: "അതിരുകൾ കണ്ടെത്തുക",
    btnBhunaksha: "ഏകദേശ അതിർത്തി",
    btnDatabank: "ഡാറ്റാ ബാങ്ക്",
    welcomeTitle: "കണ്ടെഴുത്ത് AI",
    welcomeP1: "മുകളിൽ ആധാരമോ EC-യോ ഇടുക, താഴെ വിവരങ്ങൾ പേസ്റ്റ് ചെയ്യുക, അല്ലെങ്കിൽ ചോദ്യം ചോദിക്കുക.",
    inputPlaceholder: "ആധാരത്തിലെ ഭാഗം പേസ്റ്റ് ചെയ്യുക അല്ലെങ്കിൽ ചോദ്യം ചോദിക്കുക",
    sendBtn: "അയക്കുക",
    mapHeaderTitle: "ഉപഗ്രഹ നിരീക്ഷണം",
    presetDefault: "കേരളത്തിലെ പ്രദേശം തിരഞ്ഞെടുക്കുക...",
    mapSearchPlaceholder: "വില്ലേജ്, സ്ഥലം അല്ലെങ്കിൽ അക്ഷാംശം, രേഖാംശം...",
    toolPin: "സ്ഥാനം അടയാളപ്പെടുത്തുക",
    toolPlot: "പ്ലോട്ട് വരയ്ക്കുക (സെന്റ്)",
    toolRoad: "വഴി വീതി അളക്കുക",
    btnUndo: "↩️ പഴയപടിയാക്കുക",
    btnClear: "മായ്ക്കുക",
    btnChecklist: "ചെക്ക്‌ലിസ്റ്റ്",
    guidanceDefault: "സാറ്റലൈറ്റ് മാപ്പിൽ എവിടെയെങ്കിലും ക്ലിക്ക് ചെയ്ത് പരിശോധനാ പിൻ സ്ഥാപിച്ച് ജിപിഎസ് ലൊക്കേഷൻ കാണുക.",
    guidancePlot: "സാറ്റലൈറ്റിൽ അതിർത്തിക്കല്ലുകൾ അടയാളപ്പെടുത്തുക. കുറഞ്ഞത് 3 പോയിന്റുകൾ ആവശ്യമാണ്. 'പ്ലോട്ട് പൂർത്തിയാക്കുക' ക്ലിക്ക് ചെയ്യുക.",
    guidanceRoad: "KPBR ചട്ടപ്രകാരം വഴി വീതി അറിയാൻ വഴിയുടെ ഇരുവശങ്ങളിലുമായി 2 പോയിന്റുകളിൽ ക്ലിക്ക് ചെയ്യുക.",
    guidanceSeal: "✓ പ്ലോട്ട് പൂർത്തിയാക്കുക",
    btnGuidanceAutoDemarcate: "അതിരുകൾ അടയാളപ്പെടുത്തുക",
    hudLiveTag: "തത്സമയ പ്ലോട്ട് വിവരങ്ങൾ",
    hudCoords: "അക്ഷാംശ രേഖാംശങ്ങൾ",
    hudExtentLabel: "പ്ലോട്ട് വിസ്തീർണ്ണം",
    hudCentsLabel: "കേരള സെന്റ്",
    hudArea: "വിസ്തീർണ്ണം (ആറുകളും ച.മീറ്ററും)",
    hudRoad: "വഴി വീതി (KPBR ചട്ടങ്ങൾ)",
    hudElevationLabel: "ഉയരവും വെള്ളപ്പൊക്ക സാധ്യതയും",
    hudMslLabel: "സമുദ്രനിരപ്പ്",
    hudCentsUnit: "സെന്റ്",
    hudAresUnit: "ആർ",
    hudSqMUnit: "ച.മീ.",
    hudMetersUnit: "മീറ്റർ",
    hudMslUnit: "മീറ്റർ സമുദ്രനിരപ്പ്",
    hudRoadPass: "✓ KPBR അനുമതി ലഭ്യം (≥3m)",
    hudRoadWarn: "▲ ചെറിയ പ്ലോട്ട് മാത്രം",
    hudRoadFail: "✕ വഴി സൗകര്യമില്ല",
    hudElevationRiskLow: "● കുറഞ്ഞ വെള്ളപ്പൊക്ക സാധ്യത",
    hudElevationRiskMod: "▲ മിതമായ വെള്ളപ്പൊക്ക സാധ്യത",
    hudElevationRiskHigh: "■ കൂടിയ വെള്ളപ്പൊക്ക സാധ്യത",
    hudElevationRiskCrit: "■ അതീവ അപകടസാധ്യത",
    hudBasinPlinth: "തറ ഉയരം:",
    btnHudSend: "ഓഡിറ്ററിലേക്ക്",
    btnHudExport: "PDF റിപ്പോർട്ട്",
    btnOpenGmaps: "ഗൂഗിൾ മാപ്പ്",
    chkPanelTitle: "സ്ഥല പരിശോധനാ മാനദണ്ഡങ്ങൾ",
    chkKallu: "<strong>സർവേ കല്ലുകൾ:</strong> 4 മൂലകളിലും സർവേ കല്ലുകൾ ഉണ്ടെന്ന് നേരിട്ട് കണ്ട് ഉറപ്പാക്കുക.",
    chkRoad: "<strong>വഴിയുടെ വീതി:</strong> KPBR പെർമിറ്റിനായി കുറഞ്ഞത് 3.0 മീറ്റർ സഞ്ചാരയോഗ്യമായ വഴി.",
    chkWetland: "<strong>തണ്ണീർത്തട സാമീപ്യം:</strong> പരിസരത്ത് തോടുകളോ നീർത്തടങ്ങളോ ഉണ്ടോയെന്ന് സാറ്റലൈറ്റിൽ കാണുക.",
    chkHt: "<strong>വൈദ്യുതി ലൈൻ:</strong> പ്ലോട്ടിന് മുകളിലൂടെ ഹൈ-ടെൻഷൻ ലൈൻ പോകുന്നില്ലെന്ന് ഉറപ്പാക്കുക.",
    chkFlood: "<strong>വെള്ളപ്പൊക്ക പാടുകൾ:</strong> മതിലുകളിലും തൂണുകളിലും 2018-ലെ വെള്ളപ്പൊക്ക ജലനിരപ്പ് പാടുകൾ പരിശോധിക്കുക.",
    chkHint: "സർവേയറുമൊത്ത് നേരിട്ട് പരിശോധിക്കുമ്പോൾ ഓരോന്നായി ടിക്ക് ചെയ്യുക.",
    typingAnalysis: "ആധാര രേഖകൾ, മുന്നാധാര ചരിത്രം, കേരള ചട്ടങ്ങൾ എന്നിവ പരിശോധിക്കുന്നു...",
    presets: {
      default: "കേരളത്തിലെ പ്രദേശം തിരഞ്ഞെടുക്കുക...",
      aluva: "ആലുവ (പെരിയാർ തീരം - 2018 വെള്ളപ്പൊക്ക മേഖല)",
      kakkanad: "കാക്കനാട് / ഇൻഫോപാർക്ക് (ഉയർന്ന പ്രദേശം)",
      kuttanad: "കുട്ടനാട് (സമുദ്രനിരപ്പിന് താഴെയുള്ള തണ്ണീർത്തടം)",
      chengannur: "ചെങ്ങന്നൂർ (പമ്പാനദി വെള്ളപ്പൊക്ക മേഖല)",
      angamaly: "അങ്കമാലി (നെൽവയൽ & കാർഷിക മേഖല)",
      kaloor: "കലൂർ / കൊച്ചി (തീരദേശ നഗരം)",
      thrissur: "തൃശ്ശൂർ (സ്വരാജ് റൗണ്ട് & കോൾ നിലങ്ങൾ)",
      kottayam: "കോട്ടയം (മീനച്ചിലാർ തണ്ണീർത്തടം)",
      kozhikode: "കോഴിക്കോട് (തീരദേശ നഗരം)",
      trivandrum: "തിരുവനന്തപുരം (കഴക്കൂട്ടം)"
    },
    layers: {
      "google-hybrid": "ഗൂഗിൾ സാറ്റലൈറ്റ് ഹൈബ്രിഡ്",
      "google-satellite": "ഗൂഗിൾ സാറ്റലൈറ്റ് മാത്രം",
      "google-roads": "ഗൂഗിൾ റോഡ് മാപ്പ്",
      "google-terrain": "ഗൂഗിൾ ഭൂപ്രകൃതി മാപ്പ്",
      "osm": "ഓപ്പൺ സ്ട്രീറ്റ് മാപ്പ്"
    }
  }
};

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
