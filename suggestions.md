# Kandezhuthu AI (കണ്ടെഴുത്ത് - ആധാരംനോക്കി)
## Comprehensive Application Testing Report & Improvement Roadmap

---

## 1. Executive Summary & Verification Matrix

During this comprehensive audit, **Kandezhuthu AI** was tested across all four architectural tiers:
1. **Deterministic Core Engines (`app/domain/`)**
2. **Backend REST APIs & Multimodal Vision Pipeline (`frontend/main.py`)**
3. **Live Generative AI Legal Assistant (`app/agent.py` on `gemini-3.8-flash`)**
4. **End-to-End Browser UI & Satellite Cadastral Workflows (`tests/ui/` via Playwright Chromium)**

### Summary Status Table

| Layer / Test Suite | Scope | Status | Notes |
|---|---|---|---|
| **Domain Unit Tests** | `SingleDeedScanner` & `MunnadharamAuditor` | ✅ **10 / 10 PASSED** | 4 fatal statutory traps, lineage math, succession law (*Mary Roy*, Hindu coparcenary) |
| **Integration Suite** | ADK Agent Runner & Server E2E (`/a2a/kandezhuthu`) | ✅ **PASSED** | A2A JSON-RPC 2.0 protocol & multi-turn memory session verified |
| **Multimodal Deed OCR** | `POST /api/upload_deed` & `GET /api/sample_deed` | ✅ **PASSED** | Extracted Re-Sy 345/1 Aluva (11 Cents Nilam), computed Sec 27A fee exemption |
| **Elevation & Hydrology** | `POST /api/plot_elevation` | ✅ **PASSED** | Aluva (6.5m MSL, Periyar Basin, 2018 flood warning, plinth >=0.75m) |
| **PDF Dossier Export** | `POST /api/export_dossier` | ✅ **PASSED** | Generated valid ReportLab PDF with metadata, risks, and Malayalam inquiries |
| **UI: Elevation & Flood** | `tests/ui/test_elevation_flood_ui.py` | ✅ **5 / 5 PASSED** | Aluva, Kakkanad, Kuttanad sub-MSL risk, 5-item checklist |
| **UI: 30-Year Lineage** | `tests/ui/test_munnadharam_lineage_ui.py` | ✅ **5 / 5 PASSED** | Aluva broken chain (0/100), Kakkanad (35/100), Clean title (100/100) |
| **UI: Realistic Buyer Journey**| `tests/ui/test_realistic_buyer_journey.py`| ✅ **8 / 8 PASSED** | Satellite plot, KPBR road, live Gemini triage, WhatsApp copy & link |
| **UI: PDF Dossier Export** | `tests/ui/test_pdf_dossier_export.py` | ✅ **4 / 4 PASSED** | HUD plot dossier, lineage dossier, deed audit scorecard dossier |
| **UI: Multimodal OCR Pipeline**| `tests/ui/test_ocr_document_pipeline.py`| ✅ **6 / 6 PASSED** | Deed dropzone, sale deed OCR, EC Form 15 mortgage detection |
| **UI: Cadastral Map Tools** | `tests/ui/test_cadastral_map_tools.py` | ✅ **6 / 6 PASSED** | Kakkanad search, pin tool, 4-point polygon sealing, road width, clear |
| **UI: Bilingual & Workflow** | `tests/ui/test_bilingual_workflow_ui.py` | ✅ **6 / 6 PASSED** | EN ⇄ ML switch, 3-step guided flow, quick chip filtering, input auto-resize |
| **UI: Comprehensive Playwright**| `tests/ui/test_ui_playwright.py` | ✅ **8 / 8 PASSED** | Split view, map tools, undo, KPBR pill, live agent streaming, mobile view |

---

## 2. Defects Diagnosed & Remediated During Testing

1. **Environment Initialization in Integration Tests (`tests/integration/test_agent.py`)**
   - *Problem*: `test_agent.py` executed without calling `load_dotenv()`, resulting in missing Vertex AI project configurations during headless runs.
   - *Fix*: Added `from dotenv import load_dotenv; load_dotenv()` before initializing ADK agents.

2. **A2A Protocol Route Mismatch (`tests/integration/test_server_e2e.py`)**
   - *Problem*: Test suite targeted legacy endpoint `/a2a/app/` while `app.agent.app.name` was configured as `"kandezhuthu"`.
   - *Fix*: Updated test routes to `/a2a/kandezhuthu/` and `app_name: "kandezhuthu"`.

3. **Continuous Satellite Tile Streaming vs. `networkidle` Timeout**
   - *Problem*: Leaflet loads dynamic raster tiles from Google Satellite / OSM, causing `page.goto(..., wait_until="networkidle")` to trigger false-positive 30-second timeouts.
   - *Fix*: Transitioned all UI test suites to `wait_until="domcontentloaded"` with a 1.2s DOM settling buffer.

4. **Field Checklist Expansion Assertion**
   - *Problem*: A 5th checklist item (*Elevation & 2018 Flood Watermark Check*) was added to the HUD, causing tests asserting badge text `"2/4"` to fail.
   - *Fix*: Updated UI assertions to validate `"2/5"`.

5. **DOM Element Selector Evolution**
   - *Problem*: The landing UI was upgraded with modern 1-click action cards (`.layman-card.card-deed`, `.layman-card.card-ec`), breaking legacy text-based button selectors.
   - *Fix*: Refactored test selectors to `.layman-card.card-deed`, `.layman-card.card-ec`, and `button:has-text('Export Dossier')`.

6. **Malayalam Quote Escaping in WhatsApp Button Handler (`frontend/static/index.html`)**
   - *Problem*: When generating WhatsApp inquiry drafts containing single quotes in Malayalam legal terms (e.g. `'നിലം'`, `'പുരയിടം'`), inline attributes like `onclick="copyWhatsApp(this, '${safeWa}')"` broke JavaScript string parsing on click.
   - *Fix*: Refactored `copyWhatsApp(this)` to automatically extract text from the sibling `.whatsapp-text` element using DOM traversal, eliminating quote escaping vulnerabilities entirely.

7. **Cadastral Map Search Selector & Overlay Offsets**
   - *Problem*: `test_cadastral_map_tools.py` searched for `#map-search-input` instead of `#map-search`, and clicked canvas coordinates obstructed by the floating guidance bar and center popup.
   - *Fix*: Corrected input ID to `#map-search` and introduced canvas offset points (`ox = cx - 120, oy = cy - 120`) to prevent marker interception.

8. **Asynchronous Elevation Fetch Race Condition**
   - *Problem*: In `test_cadastral_map_tools.py`, inspecting `#hud-elevation-text` immediately after polygon sealing evaluated the string while in the `"Calculating..."` state.
   - *Fix*: Added `expect(page.locator("#hud-elevation-text")).to_contain_text("MSL", timeout=5000)`.

9. **Missing Favicon Route Generating Browser Console 404**
   - *Problem*: Browser test runs logged a 404 error attempting to fetch `/favicon.ico`.
   - *Fix*: Added `/favicon.ico` route in FastAPI and created `frontend/static/favicon.ico`.

---

## 3. Prioritized Improvement Suggestions

### Priority 1: Document Ingestion & Legal Diligence (Immediate Impact)

| Feature | Description | Technical Implementation |
|---|---|---|
| **Multi-Page Deed Chunking & Stitching** | Kerala *Theeradharam* documents frequently span 12–25 stamp paper pages. Current OCR processes single-page or combined PDFs. | Implement PyPDF2/pdf2image page splitting with Gemini batch processing, stitching schedules and recitals into a unified AST. |
| **Structured SRO EC (Form 15) Tabular Extraction** | SRO Encumbrance Certificates contain structured tables with Document No, Year, Claimant, Executant, and Consideration. | Use Gemini multimodal table extraction with a strict JSON Schema output matching `ECRecord` fields. |
| **Kerala Registration Fair Value Triangulation** | Sellers often inflate land value or under-declare for stamp duty evasion. | Integrate with Kerala Registration Department Fair Value lookup tables based on District, Taluk, Village, and Survey No. |
| **Malayalam Vintage Cursive Script Normalization** | Older pre-1990 deeds (*Munnadharam*) use vintage Malayalam script (*പഴയ ലിപി* / *Ezhuthu*). | Fine-tune OCR prompts with domain-specific vocabulary for old Malayalam orthography (e.g., ഌ, ൹, ൲). |

---

### Priority 2: GIS, Hydrology & Satellite Cadastral Intelligence

| Feature | Description | Technical Implementation |
|---|---|---|
| **KSDMA Flood Polygon Vector Overlay** | Allow buyers to toggle Kerala State Disaster Management Authority (KSDMA) flood hazard zone polygons on the satellite view. | Add GeoJSON vector layer toggle in Leaflet for Periyar, Pamba, and Meenachil river flood hazard contours. |
| **BhuNaksha FMB Cadastral Geo-Rectification** | Enable buyers to overlay scanned Field Measurement Book (FMB / പ്ലോട്ട് സ്കെച്ച്) sketches directly onto satellite imagery. | Implement Leaflet ImageOverlay with 3-point affine coordinate warping to match ground survey stones. |
| **Digital Elevation Model (DEM) Contours** | Visual elevation contours to identify steep slopes or natural drainage channels prone to waterlogging. | Integrate open-source SRTM 30m or Copernicus DEM tiles with color-coded elevation bands. |
| **CRZ (Coastal Regulation Zone) Boundary Buffer** | Coastal and backwater plots (e.g., Kochi, Alappuzha) are restricted under CRZ 2019 regulations. | Display high-tide line (HTL) 50m / 100m / 200m setback restriction buffer lines on coastal coordinates. |

---

### Priority 3: Layman User Experience & Cultural Ergonomics

| Feature | Description | Technical Implementation |
|---|---|---|
| **Interactive Form 6 Government Fee Calculator** | Section 27A fee calculation depends on plot extent (<=25 cents = ₹0; >25 cents = 10%–20% of fair value). | Add an interactive slider widget that calculates estimated revenue conversion fees based on village fair value. |
| **Malayalam Text-to-Speech (TTS) Voice Explanations** | Many elderly buyers and NRIs prefer listening to audio breakdowns over reading dense legal disclaimers. | Add Web Speech API / Google Cloud TTS playback for the deed audit scorecard and WhatsApp inquiry drafts. |
| **Side-by-Side Plot Comparison Mode** | Buyers evaluating multiple plots need comparative risk scorecards side by side. | Enable saving up to 3 plots in `localStorage` with a comparative matrix (Elevation, KPBR road, Clean Title score). |
| **Native Web Share API for Legal Dossiers** | Direct 1-tap WhatsApp sharing of generated PDF dossiers from mobile browsers. | Use `navigator.share({ files: [dossierPdf] })` on mobile devices. |

---

### Priority 4: Test Automation & Production Hardening

| Feature | Description | Technical Implementation |
|---|---|---|
| **CI Headless Clipboard Mocking** | Playwright in headless CI environments restricts `navigator.clipboard`. | Inject `page.add_init_script` mock for clipboard API across all UI test fixtures. |
| **Synthetic 30-Year Lineage Chain Generator** | Generate edge-case title chains (e.g., 5-generation intestate succession) for fuzz testing. | Create property-based test generators using `hypothesis` to test the deterministic auditor. |
| **Redis Session Persistence for Multi-Tenant Deployments** | Currently uses `InMemorySessionService` in local development. | Add Redis or Firestore session persistence when deploying to Cloud Run via `agents-cli deploy`. |

---

## 4. Ethical & Statutory Guardrails Summary

The testing confirmed that Kandezhuthu AI consistently adheres to all non-negotiable legal principles:
1. **Never Guarantees 100% Clean Title on Paper Alone**: Prominently displays the warning that document analysis cannot substitute on-ground physical inspection.
2. **Explicit Non-AI Verifiability Checklist**: Consistently enumerates what cannot be verified via deed OCR:
   - Physical boundary stones (*Survey Kallu*) and neighbor encroachment
   - Motorability and physical width of access roads
   - Oral family agreements (*Vaymozhi udanpadi*) and unfiled caveats
   - Historical waterlogging and high-tension overhead electrical lines
3. **Mandatory Advocate Consultation Notice**: Explicitly instructs users to consult a licensed Kerala High Court or District advocate before releasing token advances or earnest money.
